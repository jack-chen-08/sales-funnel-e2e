# EVIDENCE 索引（本目录全部为真跑落盘，未手工编辑）

| 目录 | 内容 | 对应 AC |
| --- | --- | --- |
| `run_5x/` | 连续 5 次完整 12 步的报告（`report.json` / `report.md`）、pytest 日志、逐步 trace 与 HTTP 留证；汇总 `summary.json` / `summary.md` | AC1 |
| `miniprogram/` | 第 11、12 步的小程序执行证据（**组件级** simulate）：三阶段渲染树、真实 HTTP 请求响应（`requests.jsonl`）、21 条断言（`trace.json`）、`summary.md` | AC1（小程序两步） |
| `miniprogram/automator/` | 第 11、12 步**页面级**执行证据：开发者工具 + `miniprogram-automator`，真实页面/真实 input-button/真实 `wx.navigateTo` 路由，4 张像素截图 + 13 条断言 + 12/12 整链报告（`RUN.md` 有环境与复现命令） | AC1（页面级） |
| `esign_reject/` | 拒签失败路径：`report.json` / `report.md`、`pytest.log`、步骤 8 的 trace、失败截图、失败 DOM、HTTP 留证 | AC2 |
| `cleanup/` | 清理前 psql 直查（21 行）、DELETE 接口响应、清理后 psql 直查（0 行） | AC3 |
| `skip_miniprogram/` | `--skip-miniprogram` 模式报告（10 通过 / 2 跳过）与产物；命令行开关与 `@pytest.mark.skip_mini` 两种触发方式各一份（`report.*` / `report_marker.*`） | AC4 |
| `env/` | 起环境日志、Python/依赖/Chromium/PostgreSQL 版本 | 环境基线 |

## 关键数字（取自下列文件）

- AC1：5/5 通过，单次 23.64–26.48s，平均 24.57s，上限 600s → `run_5x/summary.json`
- AC1（小程序两步）：5/5 次均由 `miniprogram-automator` 在真页面执行（`--miniapp-executor automator`，
  每次迭代前由 `scripts/run_5x.sh` 调 `open_automator_port.sh` 重新开窗），`mode=miniapp`、`component_phase`
  依次为 `certified` / `home`，每次各 4 张截图与 `trace.json` → `run_5x/run_{1..5}/artifacts/miniapp/`
- AC1（小程序两步·页面级）：1 次由 `miniprogram-automator` + 开发者工具真实执行，13 条断言 0 失败，`entry_page=/pages/entry/index`、路由到 `pages/home/index`、页面数到 3 个资源条目 → `miniprogram/automator/report.json`、`miniprogram/automator/trace.json`
- AC2：失败步骤 `#8「电子签」`，原因「AssertionError: 电子签未完成两方签署：签约方拒签：签约方在签署页点击拒签（电子签桩模拟）」→ `esign_reject/report.json`
- AC3：清理前 21 行 → 删除 21 行 → 清理后 12 张业务表合计 0 行 → `cleanup/psql_before_cleanup.log`、`cleanup/psql_after_cleanup.log`
- AC4：`counts = {"passed": 10, "skipped": 2, "failed": 0}`，跳过步骤号 `[11, 12]` → `skip_miniprogram/report.json`

> 耗时均为「接口桩 + 本地 Chromium + 本地小程序模拟器」环境下的实测值，用于验证链路正确性与稳定性，不代表真实平台性能。

## 复现

```bash
bash scripts/start_env.sh              # 起 mock 平台
bash scripts/setup_miniapp.sh          # 安装小程序自动化依赖（首次，仅 Node 侧）
bash scripts/run_5x.sh                 # AC1（含小程序两步真跑）
bash scripts/run_reject_demo.sh        # AC2
bash scripts/cleanup_proof.sh          # AC3
bash scripts/run_skip_miniprogram.sh   # AC4
```

查看失败步骤 trace：

```bash
.venv/bin/playwright show-trace EVIDENCE/esign_reject/artifacts/step_08_esign_trace.zip
```
