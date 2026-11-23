"""pytest 公共配置：命令行开关与运行标识生成。"""

from __future__ import annotations

import datetime as dt
import os
import uuid

import pytest


def pytest_addoption(parser: pytest.Parser) -> None:
    group = parser.getgroup("smoke")
    group.addoption(
        "--smoke-base-url",
        action="store",
        default=os.environ.get("SMOKE_BASE_URL", "http://127.0.0.1:5600"),
        help="冒烟 mock 平台地址，默认取环境变量 SMOKE_BASE_URL",
    )
    group.addoption(
        "--skip-miniprogram",
        action="store_true",
        default=False,
        help="跳过小程序两步（跳过后不装载官方模拟器，仅跑其余 10 步）",
    )
    group.addoption(
        "--run-tag",
        action="store",
        default="",
        help="run_id 前缀标签，便于在报告中区分批次",
    )


@pytest.fixture(scope="session")
def base_url(pytestconfig: pytest.Config) -> str:
    return str(pytestconfig.getoption("--smoke-base-url")).rstrip("/")


@pytest.fixture
def skip_miniprogram(pytestconfig: pytest.Config, request: pytest.FixtureRequest) -> bool:
    """跳过小程序两步：命令行 --skip-miniprogram 或 @pytest.mark.skip_mini 标记，任一即生效。

    标记方式供只认 marker 的流水线（部分 CI 不允许改命令行）使用，等价于命令行开关。
    """
    if request.node.get_closest_marker("skip_mini") is not None:
        return True
    return bool(pytestconfig.getoption("--skip-miniprogram"))


@pytest.fixture(scope="session")
def miniapp_ready() -> tuple[bool, str]:
    """小程序两步的执行环境是否就绪（Node + 官方模拟器依赖 + 仓内工程）。

    未就绪时由用例显式 skip 并给出修复指引 —— 不静默回退为接口桩，
    否则报告会谎称 12 步全部真实执行。
    """
    from tests.core import miniapp

    return miniapp.availability()


@pytest.fixture(scope="session")
def headless() -> bool:
    return os.environ.get("SMOKE_HEADLESS", "1") not in {"0", "false", "False"}


@pytest.fixture
def make_run_id(pytestconfig: pytest.Config):
    def _make(scenario: str) -> str:
        tag = pytestconfig.getoption("--run-tag") or scenario
        stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
        return f"smk-{tag}-{stamp}-{uuid.uuid4().hex[:4]}"

    return _make
