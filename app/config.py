"""配置只从环境变量读取（统一技术约定：配置与密钥不落盘、不进代码）。"""

from __future__ import annotations

import os
from dataclasses import dataclass


def _require(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"缺少必需的环境变量：{name}")
    return value


@dataclass(frozen=True)
class Settings:
    database_url: str
    sign_stub_mode: str
    miniapp_stub_mode: str
    org_id: str
    site_id: str
    default_advisor_prefix: str

    @property
    def esign_will_reject(self) -> bool:
        return self.sign_stub_mode.lower() == "reject"


def load_settings() -> Settings:
    database_url = os.environ.get("DATABASE_URL", "").strip()
    if not database_url:
        database_url = (
            "postgresql+psycopg://"
            f"{os.environ.get('POSTGRES_USER', 'smoke')}:"
            f"{os.environ.get('POSTGRES_PASSWORD', '')}@"
            f"127.0.0.1:{os.environ.get('PG_PORT', '55433')}/"
            f"{os.environ.get('POSTGRES_DB', 'smoke')}"
        )
    return Settings(
        database_url=database_url,
        sign_stub_mode=os.environ.get("SIGN_STUB_MODE", "ok"),
        miniapp_stub_mode=os.environ.get("MINIAPP_STUB_MODE", "ok"),
        org_id=os.environ.get("SMOKE_ORG_ID", "6f1c2b40-0000-4000-8000-000000000001"),
        site_id=os.environ.get("SMOKE_SITE_ID", "6f1c2b40-0000-4000-8000-0000000000a1"),
        default_advisor_prefix="ADV",
    )


settings = load_settings()
