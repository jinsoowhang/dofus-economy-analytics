from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from urllib.parse import urlsplit

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker
from starlette.concurrency import run_in_threadpool
from starlette.middleware.gzip import GZipMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from dofus_touch_economy.bigquery_sync import BigQuerySyncManager
from dofus_touch_economy.config import Settings
from dofus_touch_economy.database import create_engine_for_url, create_session_factory
from dofus_touch_economy.services.accounts import Account, AccountConflict, AccountService
from dofus_touch_economy.worlds import (
    DEFAULT_WORLD,
    WORLD_COOKIE,
    WORLDS,
    find_world,
    validate_world_paths,
    world_settings,
    world_url,
)

UNSAFE_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})


async def _request_world(request: Request):
    if request.method in UNSAFE_METHODS and request.headers.get("content-type", "").startswith(
        ("application/x-www-form-urlencoded", "multipart/form-data")
    ):
        form = await request.form()
        account_ids = form.getlist("account_id")
        if account_ids and any(value != request.state.account.id for value in account_ids):
            raise HTTPException(409, "Account changed; reload this page before submitting")
        keys = form.getlist("world")
        if keys:
            if len(set(keys)) != 1:
                raise HTTPException(400, "Conflicting game/server selections")
            try:
                submitted = find_world(str(keys[0]))
            except ValueError as error:
                raise HTTPException(400, str(error)) from error
            if request.state.explicit_world and submitted != request.state.world:
                raise HTTPException(400, "Conflicting game/server selections")
            request.state.world = submitted
            request.state.explicit_world = True
    return request.state.world


async def get_session(request: Request) -> AsyncIterator[Session]:
    world = await _request_world(request)
    factory: sessionmaker[Session] = request.app.state.world_session_factories[world.key]
    settings = world_settings(request.app.state.settings, world)
    if world != DEFAULT_WORLD and not settings.database_path.is_file():
        raise HTTPException(503, "Dofus catalog is not initialized; run dofus-sync-pc first")
    account = request.state.account
    with factory(info={"owner_id": account.id, "is_admin": account.is_admin}) as session:
        yield session


async def get_settings(request: Request) -> Settings:
    return world_settings(request.app.state.settings, await _request_world(request))


async def get_bigquery_sync_manager(request: Request) -> BigQuerySyncManager:
    if not request.state.account.is_admin:
        raise HTTPException(403, "Only the owner can publish analytical snapshots")
    world = await _request_world(request)
    if world == DEFAULT_WORLD:
        return request.app.state.bigquery_sync_manager
    return request.app.state.world_sync_managers[world.key]


def create_app(
    settings: Settings | None = None,
    session_factory: sessionmaker[Session] | None = None,
    bigquery_sync_manager: BigQuerySyncManager | None = None,
) -> FastAPI:
    from dofus_touch_economy.routers import api, web

    resolved_settings = settings or Settings.from_env()
    validate_world_paths(resolved_settings)
    owned_engines: list[Engine] = []
    if session_factory is None:
        engine = create_engine_for_url(resolved_settings.database_url)
        owned_engines.append(engine)
        session_factory = create_session_factory(engine)
    factories = {DEFAULT_WORLD.key: session_factory}
    for world in WORLDS[1:]:
        engine = create_engine_for_url(world_settings(resolved_settings, world).database_url)
        owned_engines.append(engine)
        factories[world.key] = create_session_factory(engine)

    @asynccontextmanager
    async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
        yield
        for engine in owned_engines:
            engine.dispose()

    application = FastAPI(title="Dofus Economy", lifespan=lifespan)
    application.state.settings = resolved_settings
    application.state.session_factory = session_factory
    application.state.world_session_factories = factories
    application.state.accounts = AccountService(factories[DEFAULT_WORLD.key], resolved_settings)
    application.state.bigquery_sync_manager = bigquery_sync_manager or BigQuerySyncManager(
        resolved_settings.bigquery_project_id,
        resolved_settings.bigquery_location,
        resolved_settings.bigquery_datasets,
        resolved_settings.database_path,
    )
    application.state.world_sync_managers = {
        DEFAULT_WORLD.key: application.state.bigquery_sync_manager,
    }
    for world in WORLDS[1:]:
        scoped = world_settings(resolved_settings, world)
        application.state.world_sync_managers[world.key] = BigQuerySyncManager(
            scoped.bigquery_project_id,
            scoped.bigquery_location,
            scoped.bigquery_datasets,
            scoped.database_path,
        )

    @application.get("/select-world", include_in_schema=False)
    def select_world(request: Request, game: str, server: str):
        selected = next(
            (world for world in WORLDS if world.game == game and world.key == server), None
        )
        if selected is None:
            raise HTTPException(400, "Unknown game/server selection")
        request.state.world = selected
        response = RedirectResponse(world_url("/", selected), status_code=303)
        response.set_cookie(
            WORLD_COOKIE
            if request.state.account.id == "owner"
            else f"{WORLD_COOKIE}_{request.state.account.id}",
            selected.key,
            max_age=365 * 24 * 60 * 60,
            httponly=True,
            secure=resolved_settings.public_origin is not None,
            samesite="lax",
        )
        return response

    @application.get("/healthz", include_in_schema=False)
    def health():
        return {"status": "ok"}

    @application.get("/account/status", include_in_schema=False)
    def account_status(request: Request):
        return {"account_id": request.state.account.id}

    @application.middleware("http")
    async def enforce_same_origin(request: Request, call_next):
        request.state.account = Account("owner", "", "approved", True, False)
        if request.url.path == "/healthz":
            return await call_next(request)
        if resolved_settings.accounts_enabled:
            subject = request.headers.get("x-forwarded-user", "")
            email = request.headers.get("x-forwarded-email", "")
            if not subject or not email:
                return JSONResponse(
                    status_code=401,
                    content={"detail": "Google sign-in required"},
                    headers={"Cache-Control": "private, no-store"},
                )
            try:
                request.state.account = await run_in_threadpool(
                    application.state.accounts.identify, subject, email
                )
            except AccountConflict:
                return JSONResponse(
                    status_code=403,
                    content={"detail": "Account identity conflict"},
                    headers={"Cache-Control": "private, no-store"},
                )
            if request.state.account.status != "approved":
                if request.url.path != "/access-request":
                    if request.url.path.startswith("/api/") or request.method in UNSAFE_METHODS:
                        return JSONResponse(
                            status_code=403,
                            content={"detail": "Account approval required"},
                            headers={"Cache-Control": "private, no-store"},
                        )
                    return RedirectResponse(
                        "/access-request",
                        status_code=303,
                        headers={"Cache-Control": "private, no-store"},
                    )
                from dofus_touch_economy.routers.accounts import access_response

                return access_response(request)
        supplied_account = request.headers.get("x-economy-account")
        if supplied_account is not None and supplied_account != request.state.account.id:
            return JSONResponse(
                status_code=409, content={"detail": "Account changed; reload this page"}
            )
        explicit_keys = request.query_params.getlist("world")
        header_world = request.headers.get("x-economy-world")
        if header_world is not None:
            explicit_keys.append(header_world)
        if len(set(explicit_keys)) > 1:
            return JSONResponse(
                status_code=400, content={"detail": "Conflicting game/server selections"}
            )
        request.state.explicit_world = bool(explicit_keys)
        try:
            request.state.world = find_world(
                explicit_keys[0]
                if explicit_keys
                else request.cookies.get(
                    WORLD_COOKIE
                    if request.state.account.id == "owner"
                    else f"{WORLD_COOKIE}_{request.state.account.id}",
                    DEFAULT_WORLD.key,
                )
            )
        except ValueError as error:
            if explicit_keys:
                return JSONResponse(status_code=400, content={"detail": str(error)})
            request.state.world = DEFAULT_WORLD
        origin = request.headers.get("origin")
        if request.method in UNSAFE_METHODS and resolved_settings.public_origin is not None:
            source = origin if origin is not None else request.headers.get("referer", "")
            try:
                parsed_source = urlsplit(source)
                source_origin = f"{parsed_source.scheme}://{parsed_source.netloc}"
            except ValueError:
                source_origin = ""
            if (
                source_origin != resolved_settings.public_origin
                or request.headers.get("sec-fetch-site") == "cross-site"
            ):
                return JSONResponse(
                    status_code=403, content={"detail": "same-origin request required"}
                )
        if request.method in UNSAFE_METHODS and origin is not None:
            try:
                origin_authority = urlsplit(origin).netloc.casefold()
            except ValueError:
                origin_authority = ""
            request_authority = request.headers.get("host", "").casefold()
            if not origin_authority or origin_authority != request_authority:
                return JSONResponse(
                    status_code=403, content={"detail": "cross-origin request denied"}
                )
        response = await call_next(request)
        world = request.state.world
        if "location" in response.headers and (
            request.state.explicit_world or world != DEFAULT_WORLD
        ):
            response.headers["location"] = world_url(response.headers["location"], world)
        if "hx-redirect" in response.headers and (
            request.state.explicit_world or world != DEFAULT_WORLD
        ):
            response.headers["hx-redirect"] = world_url(response.headers["hx-redirect"], world)
        response.headers["Cache-Control"] = (
            "private, no-store" if resolved_settings.accounts_enabled else "no-store"
        )
        if not request.url.path.startswith(("/static/", "/item-icons/")):
            response.headers["X-Economy-World"] = world.key
        return response

    application.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=list(resolved_settings.allowed_hosts),
    )
    application.add_middleware(GZipMiddleware, minimum_size=1_000)
    static_directory = Path(__file__).resolve().parent / "static"
    application.mount(
        "/static",
        StaticFiles(directory=static_directory, check_dir=False),
        name="static",
    )
    application.mount(
        "/item-icons",
        StaticFiles(
            directory=resolved_settings.project_root / "data" / "app" / "item_icons",
            check_dir=False,
        ),
        name="item-icons",
    )
    application.include_router(web.router)
    application.include_router(api.router, prefix="/api/v1")
    from dofus_touch_economy.routers.accounts import router as accounts_router

    application.include_router(accounts_router)
    return application
