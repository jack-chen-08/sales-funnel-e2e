"""基线版本：一次性建立冒烟平台全部业务表。

说明：这是仓库的第一个基线 revision，直接由 SQLAlchemy 模型元数据建表，
后续变更再按增量 revision 演进，保持 Alembic 版本链连续。
"""

from __future__ import annotations

from alembic import op

from app.models import Base

revision = "0001_baseline"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    Base.metadata.create_all(bind=op.get_bind())


def downgrade() -> None:
    Base.metadata.drop_all(bind=op.get_bind())
