# 交付说明 · 招商全链路冒烟（12 步链式 E2E）

- 交付形态：本地 git 仓库；平台侧已提交 v1 并被要求返工，本次为 v2（返工回应见第 5 节）
- 技术栈：Python 3.12.13 / FastAPI 0.115.6 / SQLAlchemy 2.0.36 / Alembic 1.14 / PostgreSQL 16.16 / pytest 8.3.4 / Playwright 1.49.1（Chromium 1148）
- 数据：全部虚构（虚构企业「星澜数字科技」、虚构联系人、虚构手机号 13800000001），不含任何客户名称与真实个人信息
- 密钥：仅从环境变量读取，`.env` 未入库（`.gitignore`），仓库内只有 `.env.example`

## 1. 交付物

| 路径 | 说明 |
| --- | --- |
| `app/` | mock 平台：4 个真实网页（官网申请 / 顾问工作台 / 前台核销 / 电子签签约台）+ 12 步接口 + 状态机 + 清理接口 |
| `alembic/` | PostgreSQL 16 基线迁移，13 张表 |
| `tests/test_chain_e2e.py` | 4 条用例：主链路、跳过小程序（命令行开关）、跳过小程序（`skip_mini` 标记）、拒签失败路径 |
| `.github/workflows/smoke.yml` | CI 闸门 + 夜间定时：PR/push/每日 02:00(UTC+8) 跑 10 步链路，报告与证据上传 artifact |
| `tests/core/` | 链式执行器（逐步计时/留证/失败定位/清理）、HTTP 客户端、JSON+MD 报告 |
| `scripts/` | `start_env` / `stop_env` / `run_chain` / `run_skip_miniprogram` / `run_reject_demo` / `run_5x` / `cleanup_proof` / `check_cleanup` |
| `EVIDENCE/` | 真跑证据：5 次报告与日志、拒签 trace 与截图、清理前后 psql 直查、环境版本 |
| `README.md` | 可复制命令：起环境、跑链、跳过模式、拒签演示、清理 SQL |

## 2. AC 对照（标准 → 用例 → 证据）

| 验收标准 | 对应用例 / 脚本（可复制命令） | 证据文件 |
| --- | --- | --- |
| AC1 链式用例连续运行 5 次全部通过，平均耗时 ≤ 10 分钟 | `tests/test_chain_e2e.py::test_recruitment_chain_all_12_steps`，由 `bash scripts/run_5x.sh` 连跑 5 次（每次独立 run_id） | `EVIDENCE/run_5x/summary.json`、`EVIDENCE/run_5x/summary.md`、`EVIDENCE/run_5x/run_{1..5}/report.json`、`EVIDENCE/run_5x/run_{1..5}/pytest.log` |
| AC2 人为让电子签桩拒签时，报告指出失败步骤为「电子签」并附 trace | `tests/test_chain_e2e.py::test_esign_reject_reports_failed_step_with_trace`（`bash scripts/run_reject_demo.sh`，服务以 `SIGN_STUB_MODE=reject` 启动） | `EVIDENCE/esign_reject/report.json`（`failed_step.no=8`、`name=电子签`）、`EVIDENCE/esign_reject/report.md`、`EVIDENCE/esign_reject/artifacts/step_08_esign_trace.zip`、`step_08_esign_failure.png`、`step_08_esign_failure.html` |
| AC3 运行结束后该 run_id 数据被清理，查询结果为 0 | 主链路与跳过模式用例内的 `cleanup.remaining_total == 0` 断言；DB 级复核用 `bash scripts/cleanup_proof.sh` 与 `bash scripts/check_cleanup.sh <run_id>` | `EVIDENCE/cleanup/psql_before_cleanup.log`（21 行）、`EVIDENCE/cleanup/delete_api_response.json`（deleted_total=21）、`EVIDENCE/cleanup/psql_after_cleanup.log`（0 行） |
| AC4 跳过小程序步骤的模式下，其余 10 步照常执行并通过 | `tests/test_chain_e2e.py::test_skip_miniprogram_mode_runs_other_10_steps`、`test_skip_mini_marker_skips_steps_11_12`（标记方式，实测 passed）（`bash scripts/run_skip_miniprogram.sh`，即 `pytest -m skip_mode --skip-miniprogram`） | `EVIDENCE/skip_miniprogram/report.json`（`counts.passed=10`、`skipped=2`、跳过号 `[11,12]`）、`EVIDENCE/skip_miniprogram/report.md`、`EVIDENCE/skip_miniprogram/pytest.log` |

## 3. 真实输出

### 3.1 AC1 —— 连续 5 次（`EVIDENCE/run_5x/summary.md` 原文）

```
| 次数 | run_id | 结果 | 通过 | 总耗时(s) | 清理后残留 | 小程序两步 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | smk-5x-r1-20261124-142831-aa52 | passed | 12/12 | 5.13 | 0 | miniprogram-simulate 执行 |
| 2 | smk-5x-r2-20261124-142837-e421 | passed | 12/12 | 4.57 | 0 | miniprogram-simulate 执行 |
| 3 | smk-5x-r3-20261124-142842-6188 | passed | 12/12 | 4.57 | 0 | miniprogram-simulate 执行 |
| 4 | smk-5x-r4-20261124-142847-54bd | passed | 12/12 | 4.54 | 0 | miniprogram-simulate 执行 |
| 5 | smk-5x-r5-20261124-142852-9edd | passed | 12/12 | 4.64 | 0 | miniprogram-simulate 执行 |

通过次数：5/5
平均耗时：4.69s（上限 600s）
最长单次：5.13s
```

> 微信官方模拟器接入后单次耗时由 3.67s 升至约 4.5s（+0.8s 为 Node 侧装载/编译组件与两次真实 HTTP 往返）。

逐步耗时（第 1 次，总计 4563.8ms，清理删除 24 行）：

| # | 步骤 | 方式 | 耗时(ms) |
|---|------|------|----------|
| 1 | 官网提交申请 | ui | 856.5 |
| 2 | 线索按规则分配 | api | 10.3 |
| 3 | 顾问首次联系 | ui | 729.9 |
| 4 | 推进到预约参观 | api | 12.1 |
| 5 | 前台核销访客码 | ui | 740.8 |
| 6 | 纪要确认 | api | 11.8 |
| 7 | 9.5 折以内报价 | api | 12.8 |
| 8 | 电子签 | ui | 694.2 |
| 9 | 房态变为已租 | api | 11.9 |
| 10 | 会员经理领取交接 | api | 11.1 |
| 11 | 小程序完成认证 | miniapp | 910.4 |
| 12 | 小程序首页首月资源推荐 | miniapp | 0.0（渲染随第 11 步 certified 事件同驱动完成，本步仅断言；HTTP 12ms） |

### 3.2 AC2 —— 拒签失败路径（`scripts/run_reject_demo.sh` 输出原文）

```
== 启动拒签桩实例 http://127.0.0.1:5601（SIGN_STUB_MODE=reject）==
健康检查：{"status":"ok","sign_stub_mode":"reject","miniapp_stub_mode":"ok","steps":12}
== 跑拒签失败路径用例 ==
.                                                                        [100%]
== 失败步骤摘要 ==
run_id=smk-reject-20261124-004247-ca4b status=failed
失败步骤：#8「电子签」原因：AssertionError: 电子签未完成两方签署：签约方拒签：签约方在签署页点击拒签（电子签桩模拟）
步骤8 证据：trace=reports/artifacts/smk-reject-20261124-004247-ca4b/step_08_esign_trace.zip screenshot=reports/artifacts/smk-reject-20261124-004247-ca4b/step_08_esign_failure.png
清理后残留行数：0
退出码：0（0 表示成功检出拒签并点名「电子签」步骤）
```

拒签后主状态停在 `quoted`（未推进到 `signed`/`rented`），失败路径同样按 run_id 完成清理。
用例断言：失败步号 8、步骤名「电子签」、原因含「拒签」、trace 文件存在且非空、截图与 HTTP 留证存在。

### 3.3 AC3 —— 清理校验（`EVIDENCE/cleanup/psql_*.log` 原文摘录）

```
== 2. 清理前数据库直查 ==  (run_id=smk-ac3-before-20261124-004251-6402)
 applications             |    1
 leads                    |    1
 contacts                 |    1
 visits                   |    1
 visit_minutes            |    1
 quotes                   |    1
 esign_envelopes          |    1
 rooms                    |    2
 handovers                |    1
 members                  |    1
 resource_recommendations |    0
 audit_events             |   10
 remaining_rows_total     |   21

== 3. 调清理接口 DELETE /api/admin/run/smk-ac3-before-20261124-004251-6402 ==
{"deleted_total":21,"remaining_total":0,...}

== 4. 清理后数据库直查 ==
 12 张业务表全部为 0
 remaining_rows_total     |    0
```

`smoke_runs` 运行台账保留 1 行（写入 `cleaned_at`）用于审计，不计入业务数据。
主链路每次运行结束后报告内 `cleanup.remaining_total` 亦为 0（5 次均如此）。

### 3.4 AC4 —— 跳过小程序两步

```
通过 / 跳过 / 失败：10 / 2 / 0
| 11 | 小程序内完成认证 | 企业联系人 | skipped | 跳过 | 0.00s | 小程序步骤按 --skip-miniprogram 标记跳过（本轮显式要求跳过；默认执行方式为官方模拟器组件级真跑） |
| 12 | 小程序首页首月资源推荐 | 企业联系人 | skipped | 跳过 | 0.00s | 同上 |
总耗时：3.67s
run_id：smk-skipmode-20261124-035335-043d
```

## 4. 已知短板

- 小程序两步（11/12）有**两个执行器**：①**页面级（主）**——微信开发者工具 + 官方 `miniprogram-automator`，走真实页面 `pages/entry/index`、真实 `<input>`/`<button>`、真实 `wx.navigateTo` 到 `pages/home/index`，带 4 张像素截图与 13 条断言（证据 `EVIDENCE/miniprogram/automator/`，运行 `smk-auto14-20261124-142939-a30c`）；②**组件级（CI 默认）**——`miniprogram-simulate`，官方编译器编译仓库内真实 WXML/WXSS，不含页面壳与路由（证据 `EVIDENCE/miniprogram/`）。两者共同边界：非真机（未安装到手机）、`code2session` 由平台桩替代（`openid` 为 `wx_stub_*`）、未走真实短信（验证码 `123456` 为平台桩校验码）。
- 12 步中 **4 步为真实浏览器**（1 官网申请、3 顾问首次联系、5 前台核销、8 电子签）+ **2 步官方模拟器组件级**（11/12），其余 6 步（2/4/6/7/9/10）走接口，属 mock 平台内部 API，非真实下游系统。
- 电子签、小程序、房态、会员档案均为 mock/桩，接入真实系统需按 `app/stubs.py` 顶部「对接点」替换，并重新标定 10 分钟阈值（当前 4.5s 只代表本机 mock）。
- 单机串行执行，未做并发/多环境矩阵；`run_5x.sh` 仅顺序连跑 5 次。

## 5. 返工回应（针对上一轮 4 条意见）

| # | 上一轮意见 | 本轮状态 | 落地位置 / 验证 |
| --- | --- | --- | --- |
| 1 | 自动化脚本不可直接执行（指向的小程序项目不存在、未产出 trace/截图/请求响应） | **已闭环（页面级 + 组件级双执行器）** | ①仓库内已有可跑小程序工程 `miniapp/`（`app.js`/`app.json`/`app.wxss`/`pages/entry`/`components/member-entry`）；②`scripts/miniapp_smoke.js` 一条命令驱动两步，产出 trace／三阶段渲染树／真实请求响应／21 条断言；③`EVIDENCE/miniprogram/`（7 文件 = 6 份运行产物 + README，一次运行原样落盘）+ `EVIDENCE/run_5x/run_{1..5}/artifacts/miniapp/`（5 次连跑各一份）；④`pytest -m chain` 中 11/12 步实测 `mode=miniapp`、`status=passed`；⑤页面级证据 `EVIDENCE/miniprogram/automator/`（开发者工具 + `miniprogram-automator`，真实页面/输入/点击/路由 + 4 张截图，`smk-auto14-20261124-142939-a30c`，13 断言 0 失败）。能力边界见 `EVIDENCE/miniprogram/README.md` 与 `automator/RUN.md`。 |
| 2 | 小程序两步只能靠命令行开关跳过，无 pytest 标记 | **已闭环** | `pytest.ini` 注册 `skip_mini`；`tests/conftest.py` 的 `skip_miniprogram` 同时认命令行开关与该标记；新增用例 `test_skip_mini_marker_skips_steps_11_12`，实测通过（10 步 passed、11/12 记 skipped、清理残留 0）。 |
| 3 | 缺 CI 配置与夜间定时 | **已闭环（GitHub Actions 已首跑 success）** | `.github/workflows/smoke.yml`：push main / PR / 手动 / 每日 18:00 UTC（02:00 UTC+8）；PostgreSQL 16 service → Alembic → 起平台等 `/healthz` → 跑 10 步 → 报告与 `EVIDENCE/` 上传 artifact。命令序列与本地已验证流程逐条对应；首次运行已于 `3d0c490` 上 **success**（118 秒，https://github.com/jack-chen-08/sales-funnel-e2e/actions/runs/45255958600 ）。 |
| 4 | 文档里的测试名与错误码跟代码对不上 | **已闭环** | 文档只引用真实存在的用例名（4 条）；报价折扣的政策上限错误码统一为 `DISCOUNT_EXCEEDS_POLICY`（`app/main.py:459`），不再出现旧名 `BELOW_FLOOR_*`。 |
