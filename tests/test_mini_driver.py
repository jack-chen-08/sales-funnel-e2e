"""miniprogram-automator 驱动的契约测试。

真实小程序路径需要微信开发者工具（本仓 CI 不具备），但驱动与本机 node 之间的
**协议**必须可验证：返回码、stdout 末行 JSON、member_id 缺失、node 不可用。
这四条保证「失败会抛明确异常、不静默降级」，不会因为没装开发者工具就悄悄算通过。
"""
from __future__ import annotations

import json

import pytest

import chain.mini_driver as md


def _write_fake_node(tmp_path, body: str):
    path = tmp_path / "fake_automator.js"
    path.write_text(body, encoding="utf-8")
    return path


def _call(driver):
    return driver.verify(page=None, base_url="http://127.0.0.1:9", lead_id="lead-test",
                         phone="13800000000", code="246810")


def test_automator_returns_member_id(tmp_path, monkeypatch):
    js = _write_fake_node(
        tmp_path, 'console.log(JSON.stringify({member_id: "mb-test01", status: "ok"}));')
    monkeypatch.setattr(md, "AUTOMATOR_JS", js)
    assert _call(md.AutomatorDriver()) == "mb-test01"


def test_automator_nonzero_exit_raises_with_stderr(tmp_path, monkeypatch):
    js = _write_fake_node(
        tmp_path, 'console.error("devtools automation port closed"); process.exit(3);')
    monkeypatch.setattr(md, "AUTOMATOR_JS", js)
    with pytest.raises(RuntimeError, match="miniprogram-automator run failed") as exc:
        _call(md.AutomatorDriver())
    assert "automation port closed" in str(exc.value)


def test_automator_missing_member_id_raises(tmp_path, monkeypatch):
    js = _write_fake_node(tmp_path, 'console.log(JSON.stringify({status: "ok"}));')
    monkeypatch.setattr(md, "AUTOMATOR_JS", js)
    with pytest.raises(RuntimeError, match="no member_id"):
        _call(md.AutomatorDriver())


def test_automator_requires_node(monkeypatch):
    monkeypatch.setattr(md.shutil, "which", lambda _name: None)
    with pytest.raises(RuntimeError, match="needs node"):
        md.AutomatorDriver()


def test_automator_requires_script(tmp_path, monkeypatch):
    monkeypatch.setattr(md, "AUTOMATOR_JS", tmp_path / "not_there.js")
    with pytest.raises(RuntimeError, match="missing"):
        md.AutomatorDriver()


def test_automator_script_is_valid_javascript():
    """仓库里真正的执行器必须至少语法正确（node --check）。"""
    import shutil
    import subprocess

    if not shutil.which("node"):
        pytest.skip("node not installed")
    proc = subprocess.run(["node", "--check", str(md.AUTOMATOR_JS)],
                          capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr


def test_make_driver_selection(monkeypatch):
    assert md.make_driver("playwright-h5").name == "playwright-h5"
    assert md.make_driver("h5").name == "playwright-h5"
    monkeypatch.setattr(md.shutil, "which", lambda _n: "/usr/bin/node")
    assert md.make_driver("miniprogram-automator").name == "miniprogram-automator"
    with pytest.raises(ValueError, match="unknown MINI_DRIVER"):
        md.make_driver("selenium")


def test_driver_env_passthrough(tmp_path, monkeypatch):
    """driver 必须把 lead_id / phone / code 通过环境变量交给 node 脚本。"""
    js = _write_fake_node(tmp_path, (
        'const e = process.env;'
        'console.log(JSON.stringify({member_id: "mb-" + e.MINI_LEAD_ID + "-" + '
        'e.MINI_PHONE + "-" + e.MINI_CODE}));'))
    monkeypatch.setattr(md, "AUTOMATOR_JS", js)
    out = _call(md.AutomatorDriver())
    assert out == "mb-lead-test-13800000000-246810"
    assert json.dumps(out)  # 返回值是纯字符串，不含 JSON 包装
