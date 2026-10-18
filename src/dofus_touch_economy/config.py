from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit

from sqlalchemy import URL


@dataclass(frozen=True)
class Settings:
    project_root: Path
    database_path: Path
    market_context: str
    allowed_hosts: tuple[str, ...]
    bigquery_project_id: str = "claude-projects-489306"
    bigquery_location: str = "US"
    bigquery_datasets: tuple[str, ...] = ("dofus_dev", "dofus_prod")
    public_origin: str | None = None

    def __post_init__(self) -> None:
        if self.public_origin is None:
            return
        parsed = urlsplit(self.public_origin)
        if (
            parsed.scheme != "https"
            or not parsed.hostname
            or parsed.username is not None
            or parsed.password is not None
            or parsed.path
            or parsed.query
            or parsed.fragment
            or parsed.netloc != parsed.hostname
        ):
            raise ValueError("DOFUS_PUBLIC_ORIGIN must be an HTTPS origin without a path or port")
        if parsed.hostname not in self.allowed_hosts or "*" in self.allowed_hosts:
            raise ValueError("DOFUS_PUBLIC_ORIGIN requires its exact hostname in allowed hosts")

    @property
    def database_url(self) -> URL:
        return URL.create("sqlite+pysqlite", database=str(self.database_path))

    @classmethod
    def from_env(cls) -> Settings:
        default_root = Path(__file__).resolve().parents[2]
        project_root = Path(os.environ.get("DOFUS_PROJECT_ROOT", default_root)).resolve()

        configured_database_path = Path(
            os.environ.get("DOFUS_APP_DATABASE_PATH", "data/app/dofus_touch.sqlite3")
        )
        if not configured_database_path.is_absolute():
            configured_database_path = project_root / configured_database_path
        database_path = configured_database_path.resolve()

        market_context = os.environ.get("DOFUS_MARKET_CONTEXT", "unspecified").strip()
        if not market_context:
            raise ValueError("DOFUS_MARKET_CONTEXT must not be empty")

        allowed_hosts = tuple(
            host.strip()
            for host in os.environ.get("DOFUS_ALLOWED_HOSTS", "127.0.0.1,localhost").split(",")
            if host.strip()
        )
        if not allowed_hosts:
            raise ValueError("DOFUS_ALLOWED_HOSTS must contain at least one host")

        bigquery_project_id = os.environ.get(
            "DOFUS_BIGQUERY_PROJECT_ID", "claude-projects-489306"
        ).strip()
        if not bigquery_project_id:
            raise ValueError("DOFUS_BIGQUERY_PROJECT_ID must not be empty")
        bigquery_location = os.environ.get("DOFUS_BIGQUERY_LOCATION", "US").strip()
        if not bigquery_location:
            raise ValueError("DOFUS_BIGQUERY_LOCATION must not be empty")
        bigquery_datasets = tuple(
            dataset.strip()
            for dataset in os.environ.get("DOFUS_BIGQUERY_DATASETS", "dofus_dev,dofus_prod").split(
                ","
            )
            if dataset.strip()
        )
        if not bigquery_datasets:
            raise ValueError("DOFUS_BIGQUERY_DATASETS must contain at least one dataset")
        if len(set(bigquery_datasets)) != len(bigquery_datasets):
            raise ValueError("DOFUS_BIGQUERY_DATASETS must not contain duplicates")

        return cls(
            project_root=project_root,
            database_path=database_path,
            market_context=market_context,
            allowed_hosts=allowed_hosts,
            bigquery_project_id=bigquery_project_id,
            bigquery_location=bigquery_location,
            bigquery_datasets=bigquery_datasets,
            public_origin=os.environ.get("DOFUS_PUBLIC_ORIGIN", "").strip() or None,
        )
