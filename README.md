# 招商全链路冒烟（12 步链式 E2E）

把「官网提交申请 → 首次进入会员小程序」串成 1 条链式用例，用作发版前闸门与夜间冒烟。
框架：Playwright 1.49 + pytest 8.3 + FastAPI mock 平台 + PostgreSQL 16；小程序两步由微信官方
`miniprogram-simulate` 在 Node 端组件级真跑，可用 `--skip-miniprogram` 跳过。

- 12 步顺序执行，每步断言关键状态并记录 start / end / duration
- 数据用独立 `run_id`（`smk-<tag>-<时间戳>-<4位随机>`），结束（含失败）自动按 `run_id` 清理并回查残留必须为 0
- 任一步失败：报告点名失败步骤 + 该步 Playwright trace / 截图 / HTTP 请求响应 + 已创建数据 ID
- 4 步走真实浏览器点击：**1 官网申请**、**3 顾问首次联系**、**5 前台核销**、**8 电子签签约台**
- 金额一律以「分」存整数；配置与口令只从环境变量读取；仅使用虚构数据

## 目录

```
app/                    mock 平台（FastAPI）
  main.py               21 个路由：4 个真实网页 + 12 步 API + 管理/清理接口
  workflow.py           12 步状态机（唯一定义，所有接口都过 assert_status）
  models.py             13 张表，统一 id/org_id/site_id/created_at/created_by/updated_at/deleted_at + run_id
  stubs.py              电子签桩、小程序桩、外部系统对接点说明
  templates/            官网申请表、顾问工作台、前台核销台、电子签签约台
alembic/                PostgreSQL 16 迁移（0001_baseline）
tests/
  test_chain_e2e.py     AC1 / AC2 / AC4 三条用例
  core/runner.py        12 步执行器：计时、留证、失败定位、清理
  core/client.py        HTTP 客户端（自动带 X-Run-Id，逐步记录请求响应）
  core/report.py        JSON + Markdown 双份报告
scripts/                起停环境、跑链、5 连跑、拒签演示、清理校验
EVIDENCE/               真跑证据（5 次报告、拒签 trace、清理前后直查、环境版本）
```

## 快速开始

前置：Docker 可用、Python 3.11+（实测 3.12.13）、可联网装依赖与 Chromium。

```bash
cd sales-funnel-e2e

# 0) 依赖（首次）
python3.12 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/playwright install chromium

# 1) 配置：只走环境变量，.env 不入库
cp .env.example .env      # 按需改端口与数据库口令

# 2) 起环境：PostgreSQL 16（docker compose）→ Alembic 建表 → 启动 mock 平台 :5600
bash scripts/start_env.sh

# 3) 跑 12 步链式用例（AC1）
bash scripts/run_chain.sh
#   等价：.venv/bin/python -m pytest -m chain -q

# 4) 跳过小程序两步（AC4）：其余 10 步照常执行
bash scripts/run_skip_miniprogram.sh
#   等价：.venv/bin/python -m pytest -m skip_mode -q --skip-miniprogram

# 5) 电子签桩拒签失败演示（AC2）：另起一个 SIGN_STUB_MODE=reject 实例（:5601）
bash scripts/run_reject_demo.sh

# 6) 连续 5 次 + 汇总（AC1）：报告、日志、产物落到 EVIDENCE/run_5x/
bash scripts/run_5x.sh

# 7) 清理校验（AC3）：清理前直查非 0 → DELETE 按 run_id 清理 → 清理后直查为 0
bash scripts/cleanup_proof.sh
#   已有 run_id 直接查：
bash scripts/check_cleanup.sh <run_id>

# 停环境
bash scripts/stop_env.sh
```

小程序两步的三种跳过方式，任选其一（等价）：

```bash
.venv/bin/python -m pytest -m skip_mode -q --skip-miniprogram   # 命令行开关
.venv/bin/python -m pytest -q -m chain -k marker_skip           # pytest 标记 skip_mini
.venv/bin/python -m pytest -q -m "chain or skip_mode" --skip-miniprogram   # CI 里的用法
```

`@pytest.mark.skip_mini` 已注册在 `pytest.ini`，语义与 `--skip-miniprogram` 完全一致：只跳过第 11、12 步，
其余 10 步（含 4 步真实浏览器点击）照常执行；供不允许改命令行的流水线使用。

## CI 与夜间定时

`.github/workflows/smoke.yml`（推 main / PR / 手动触发 / 每日 18:00 UTC＝02:00 UTC+8）：
PostgreSQL 16 service → `alembic upgrade head` → 起 mock 平台等 `/healthz` → `pytest -m "chain or skip_mode" --skip-miniprogram`
→ 报告与 `EVIDENCE/` 作为 artifact 上传（保留 14 天）。

- 只在 CI 环境跑 10 步：CI 未装 `miniapp/node_modules`（模拟器依赖），故统一带 `--skip-miniprogram`；第 11、12 步在报告中记 `skipped`。要 CI 也跑小程序两步，加一步 `bash scripts/setup_miniapp.sh`。
- 该 workflow 的每条命令都对应本地已跑过的同一序列（见上文 1)–4)）。**首次运行已通过**：
  `smoke` 在 `3d0c490` 上 completed / success（2026-11-23T20:06:58Z，[run 45255958600](https://github.com/jack-chen-08/sales-funnel-e2e/actions/runs/45255958600)）。

清理校验 SQL（可直接贴 psql）：

```sql
-- 逐表核对某个 run_id 的残留（应为 0）
SELECT 'applications' AS table_name, count(*) FROM applications WHERE run_id = '<run_id>'
UNION ALL SELECT 'leads', count(*) FROM leads WHERE run_id = '<run_id>'
UNION ALL SELECT 'contacts', count(*) FROM contacts WHERE run_id = '<run_id>'
UNION ALL SELECT 'visits', count(*) FROM visits WHERE run_id = '<run_id>'
UNION ALL SELECT 'visit_minutes', count(*) FROM visit_minutes WHERE run_id = '<run_id>'
UNION ALL SELECT 'quotes', count(*) FROM quotes WHERE run_id = '<run_id>'
UNION ALL SELECT 'esign_envelopes', count(*) FROM esign_envelopes WHERE run_id = '<run_id>'
UNION ALL SELECT 'rooms', count(*) FROM rooms WHERE run_id = '<run_id>'
UNION ALL SELECT 'handovers', count(*) FROM handovers WHERE run_id = '<run_id>'
UNION ALL SELECT 'members', count(*) FROM members WHERE run_id = '<run_id>'
UNION ALL SELECT 'resource_recommendations', count(*) FROM resource_recommendations WHERE run_id = '<run_id>'
UNION ALL SELECT 'audit_events', count(*) FROM audit_events WHERE run_id = '<run_id>';

-- 一行汇总
SELECT sum(rows) AS remaining_rows_total FROM (
  SELECT count(*) AS rows FROM applications WHERE run_id = '<run_id>'
  UNION ALL SELECT count(*) FROM leads        WHERE run_id = '<run_id>'
  UNION ALL SELECT count(*) FROM audit_events WHERE run_id = '<run_id>'
  -- 其余表同上，完整脚本见 scripts/check_cleanup.sh
) s;
```

## 环境变量

| 变量 | 作用 | 默认 |
| --- | --- | --- |
| `DATABASE_URL` | SQLAlchemy 连接串（psycopg3） | 必填，见 `.env.example` |
| `POSTGRES_USER` / `POSTGRES_PASSWORD` / `POSTGRES_DB` / `PG_PORT` | 容器与直查用 | 见 `.env.example` |
| `SMOKE_PLATFORM_PORT` | mock 平台端口 | `5600` |
| `SMOKE_BASE_URL` | 用例目标地址（pytest `--smoke-base-url` 优先） | `http://127.0.0.1:5600` |
| `SIGN_STUB_MODE` | `ok` 正常两方签署 / `reject` 第二方拒签 | `ok` |
| `MINIAPP_STUB_MODE` | `ok` / `error`（小程序桩异常，用于演练） | `ok` |
| `SMOKE_HEADLESS` | Playwright 是否无头 | `1` |
| `SMOKE_ORG_ID` / `SMOKE_SITE_ID` | 业务表 org/site（虚构 UUID） | `.env.example` |
| `SMOKE_KEEP_DATA` | `1` 时跳过自动清理，仅供 AC3 前后对比取证 | 未设置 |

## 12 步与断言

| # | 步骤 | 执行方 | 方式 | 关键断言 |
|---|------|--------|------|----------|
| 1 | 官网提交申请 | 官网访客 | 浏览器表单 | 申请单 UUID、状态 `submitted` |
| 2 | 线索按规则分配 | 销售中台 | API | 命中 `region=east→ADV-101`、状态 `assigned` |
| 3 | 顾问首次联系 | 招商顾问 | 浏览器点击 | 工作台标签「已联系」、状态 `contacted`、回显联系记录 ID |
| 4 | 推进到预约参观 | 招商顾问 | API | 6 位访客码、状态 `visit_booked` |
| 5 | 前台核销访客码 | 前台 | 浏览器输入 | 码一致、文案「核销成功」、状态 `visited` |
| 6 | 纪要确认 | 招商顾问 | API | 状态 `minutes_confirmed` |
| 7 | 9.5 折以内报价 | 招商顾问 | API | 折扣 ≤ 500bp 且成交价 ≥ 挂牌价 95%、状态 `quoted` |
| 8 | 电子签 | 签约双方 | 浏览器签约台 | 两方签署完成、信封 `signed`、主状态 `signed` |
| 9 | 房态变为已租 | 运营中台 | API | 房态 `rented`、主状态 `rented` |
| 10 | 会员经理领取交接 | 会员经理 | API | 承接人 MM-021、会员档案创建、状态 `handed_over` |
| 11 | 小程序完成认证 | 企业联系人 | API 桩 | `certified`（`--skip-miniprogram` 时跳过） |
| 12 | 小程序首页首月资源推荐 | 企业联系人 | API 桩 | 当月、≥3 项、配额 >0、状态 `activated`（同上可跳过） |

状态机见 `app/workflow.py`；每一步先校验入口状态，非法推进返回 `409 STATE_CONFLICT`。

## 报告与证据

每次运行产出：

- `reports/run_<run_id>.json` / `.md`：结论、逐步 start/end/duration、总计、失败步骤、已创建 ID、清理明细
- `reports/artifacts/<run_id>/`：每个 UI 步骤一份 `step_XX_*_trace.zip`，每个步骤一份 `step_XX_*_http.json`；
  失败步骤额外有 `*_failure.png` 与 `*_failure.html`

看 trace：`.venv/bin/playwright show-trace reports/artifacts/<run_id>/step_08_esign_trace.zip`

已提交的真跑证据见 `EVIDENCE/README.md` 与 `DELIVERY.md`。

## 外部系统对接点（当前为 mock / 桩）

| 依赖 | 当前实现 | 对接点（替换位置） |
| --- | --- | --- |
| S4-SITE 官网与入会申请 | mock 平台自带官网页面 | `app/main.py` `/site/apply*`；用例 `tests/core/runner.py:step_01` |
| S3-SALES 业务员工作台 v1 | mock 工作台页面 + 接口 | `/advisor/console`、`/api/leads/*`、`/api/visits/*`、`/api/quotes` |
| S2-CRM 电子签 | `EsignStub`（`SIGN_STUB_MODE`） | `app/stubs.py:sign_envelope` |
| S3-MINI 会员小程序 v1 | 官方 `miniprogram-simulate`（组件级） | 仓库内 `miniapp/` + `/api/miniapp/*`；页面级需 miniprogram-automator |

## 已知短板

- 小程序两步由微信官方 `miniprogram-simulate` 执行**组件级真跑**（21 条断言全 PASS）；**页面壳与路由未覆盖**，
  要页面级/真机级需微信开发者工具 + `miniprogram-automator`（AppID + 扫码，属外部条件）。`--skip-miniprogram` 逻辑不变。
- 除 4 步浏览器点击 + 2 步官方模拟器外，其余 6 步走接口；这是为了让链条在无 UI 的存量模块上也能跑，全链路口径仍是一条用例串行。
- 耗时基线 4.5s（5 次平均）是本机 mock 的数值，接入真实系统后需重新标定 10 分钟阈值。
- `smoke_runs` 运行台账在清理后保留 1 行（含 `cleaned_at`），便于审计；12 张业务表为 0。

## 小程序两步的执行方式（组件级真跑；页面级未覆盖）

第 11、12 步（小程序内完成认证 / 首页首月资源推荐）由**微信官方 `miniprogram-simulate`** 在 Node 端执行：

| 项 | 现状 |
| --- | --- |
| 小程序工程 | 仓库内 `miniapp/`（`app.js`/`app.json`/`app.wxss`/`pages/entry`/`components/member-entry`） |
| 执行器 | `miniprogram-simulate`，内部由官方 `miniprogram-compiler` 编译真实 WXML/WXSS |
| `wx.request` | 驱动脚本用 Node `http` 桥接，经 loopback 打到本仓自起平台（不出公网） |
| 产出 | 三阶段渲染树、事件序列、请求/响应、21 条断言 → `reports/artifacts/<run_id>/miniapp/` |
| 一条命令 | `bash scripts/setup_miniapp.sh` 后 `node scripts/miniapp_smoke.js --base-url http://127.0.0.1:5600 --member-id <uuid>` |

**未覆盖**（要补需微信开发者工具 + `miniprogram-automator`，属外部条件）：

- `pages/entry` 页面壳与 `app.json` 路由——`wx.navigateTo` 未执行，simulate 不支持页面路由；
- 像素截图——模拟器只输出渲染树，不产生位图；
- 微信登录态——`code2session` 由平台桩替代，`openid` 为确定性桩值。

要只跑其余 10 步（CI 的跑法）：加 `--skip-miniprogram`，两步骤记 `skipped`，链路仍串行。
