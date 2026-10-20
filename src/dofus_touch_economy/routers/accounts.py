from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.concurrency import run_in_threadpool

from dofus_touch_economy.services.accounts import AccountConflict
from dofus_touch_economy.worlds import WORLDS

router = APIRouter()
templates = Jinja2Templates(directory=Path(__file__).resolve().parents[1] / "templates")


def access_response(request: Request):
    response = templates.TemplateResponse(
        request=request, name="access_request.html", context={"account": request.state.account}
    )
    response.headers["Cache-Control"] = "private, no-store"
    return response


@router.get("/access-request", include_in_schema=False)
def access_request(request: Request):
    return RedirectResponse("/", status_code=303)


def require_admin(request: Request):
    if not request.state.account.is_admin or not request.app.state.settings.accounts_enabled:
        raise HTTPException(403, "Administrator access required")
    return request.app.state.accounts


@router.get("/admin/access-requests", include_in_schema=False)
def access_requests(request: Request):
    service = require_admin(request)
    return templates.TemplateResponse(
        request=request,
        name="access_requests.html",
        context={
            "accounts": service.requests(),
            "world": request.state.world,
            "worlds": WORLDS,
            "active_tab": "access_requests",
        },
    )


@router.post("/admin/access-requests/{account_id}/{action}", include_in_schema=False)
async def decide_access(request: Request, account_id: str, action: str):
    service = require_admin(request)
    form = await request.form()
    if form.get("account_id") != request.state.account.id:
        raise HTTPException(409, "Account changed; reload this page")
    try:
        if action == "retry-email":
            await run_in_threadpool(service.notify, account_id)
        else:
            service.decide(account_id, {"approve": "approved", "deny": "denied"}.get(action, ""))
    except AccountConflict as error:
        raise HTTPException(400, str(error)) from error
    return RedirectResponse("/admin/access-requests", status_code=303)
