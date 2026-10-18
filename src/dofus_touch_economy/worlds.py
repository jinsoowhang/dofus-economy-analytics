"""Fixed, independently persisted game/server workspaces.

The legacy database and market identifier belong to Blair. Never rename its
observations: the display name and stored market identifier are separate concerns.
"""

from dataclasses import dataclass, replace
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from dofus_touch_economy.config import Settings


@dataclass(frozen=True)
class World:
    key: str
    game: str
    game_label: str
    server: str
    crafting_professions: tuple[str, ...]


WORLDS = (
    World("touch-blair", "touch", "Dofus Touch", "Blair", ("Shoemaker", "Jeweller", "Tailor")),
    World("dofus-tal-kasha", "dofus", "Dofus", "Tal Kasha", ("Hunter", "Jeweller", "Shoemaker")),
)
DEFAULT_WORLD = WORLDS[0]
WORLD_COOKIE = "dofus_world"


def find_world(key: str) -> World:
    for world in WORLDS:
        if world.key == key:
            return world
    raise ValueError("Unknown game/server selection")


def world_settings(settings: Settings, world: World) -> Settings:
    if world == DEFAULT_WORLD:
        return settings
    return replace(
        settings,
        database_path=settings.dofus_database_path
        or settings.database_path.parent / "dofus_tal_kasha.sqlite3",
        market_context="Tal Kasha",
        bigquery_datasets=tuple(
            f"{dataset}_dofus_tal_kasha" for dataset in settings.bigquery_datasets
        ),
    )


def world_url(url: str, world: World) -> str:
    """Pin local navigation, including redirects, to the initiating workspace."""
    parsed = urlsplit(url)
    if parsed.scheme or parsed.netloc or not parsed.path.startswith("/"):
        return url
    if parsed.path.startswith(("/static/", "/item-icons/", "/oauth2/")):
        return url
    query = [
        (key, value)
        for key, value in parse_qsl(parsed.query, keep_blank_values=True)
        if key != "world"
    ]
    query.append(("world", world.key))
    return urlunsplit(parsed._replace(query=urlencode(query)))


def validate_world_paths(settings: Settings) -> None:
    paths = [world_settings(settings, world).database_path.resolve() for world in WORLDS]
    if len(set(paths)) != len(paths):
        raise ValueError("Game/server databases must use different paths")
