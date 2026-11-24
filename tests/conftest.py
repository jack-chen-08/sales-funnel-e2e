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
        "--miniapp-executor",
        action="store",
        default=os.environ.get("MINIAPP_EXECUTOR", "auto"),
        choices=["auto", "automator", "simulate"],
        help=(
            "小程序两步的执行器：auto（默认，有开发者工具则用 automator，否则回退 simulate）"
            "/automator（miniprogram-automator 页面级，订单指定框架）/simulate（组件级补充）"
        ),
    )
    group.addoption(
        "--devtools-cli",
        action="store",
        default=os.environ.get("WECHAT_DEVTOOLS_CLI", ""),
        help="微信开发者工具 cli.bat 路径（automator 执行器用；不传则自动探测常见安装位置）",
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
def miniapp_executor(pytestconfig: pytest.Config) -> str:
    """小程序两步的执行器选择：auto / automator / simulate。"""
    return str(pytestconfig.getoption("--miniapp-executor")).strip().lower()


@pytest.fixture(scope="session")
def miniapp_ready(miniapp_executor: str) -> tuple[bool, str, str, str]:
    """小程序两步的执行环境是否就绪。

    返回 (是否可执行, 原因, 实际执行器, 回退说明)：
    - auto 模式下有开发者工具走 automator（订单指定框架），没有则回退 simulate 并在报告里写明；
    - 显式指定 automator/simulate 时不做静默回退；
    - 未就绪时由用例显式 skip 并给出修复指引 —— 不静默回退为接口桩，否则报告会谎称 12 步全跑。
    """
    from tests.core import miniapp

    return miniapp.availability(miniapp_executor)


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
