# 招商全链路冒烟（12 步链式 E2E）

把「官网提交申请 → 首次进入会员小程序」串成 1 条链式用例，用作发版前闸门与夜间冒烟。
框架：Playwright 1.49 + pytest 8.3 + FastAPI mock 平台 + PostgreSQL 16；小程序两步由微信官方
`miniprogram-automator`（页面级，经微信开发者工具自动化端口）驱动真实页面与路由，`miniprogram-simulate`
（组件级）作无开发者工具环境的补充；两者都可用 `--skip-miniprogram` 跳过。

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

# 3) 跑 12 步链式用例（AC1；小程序两步默认 auto：有开发者工具走 automator，否则回退 simulate）
bash scripts/run_chain.sh
#   指定页面级执行器：bash scripts/run_chain.sh --miniapp-executor automator
#   等价：.venv/bin/python -m pytest -m chain -q

# 4) 跳过小程序两步（AC4）：其余 10 步照常执行
bash scripts/run_skip_miniprogram.sh
#   等价：.venv/bin/python -m pytest -m skip_mode -q --skip-miniprogram

# 5) 电子签桩拒签失败演示（AC2）：另起一个 SIGN_STUB_MODE=reject 实例（:5601）
bash scripts/run_reject_demo.sh

# 6) 连续 5 次 + 汇总（AC1）：报告、日志、产物落到 EVIDENCE/run_5x/
bash scripts/run_5x.sh --miniapp-executor automator   # 页面级（需开发者工具，见下节环境变量）
#   没有开发者工具的机器：bash scripts/run_5x.sh --miniapp-executor simulate

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
| S3-MINI 会员小程序 v1 | 官方 `miniprogram-automator`（页面级，主）/ `miniprogram-simulate`（组件级，补充） | 仓库内 `miniapp/` + `/api/miniapp/*`；真实 AppID 与扫码登录属外部条件 |

## 已知短板

- 小程序两步默认走 `miniprogram-automator`（页面级：真实页面、真实路由、真实节点、像素截图）。
  本机/CI 无微信开发者工具时（`auto` 模式）自动回退 `miniprogram-simulate`（组件级），**回退原因写入报告**
  （`miniapp_executor_fallback`），报告与交付说明里不会把回退写成 automator 已跑。`--skip-miniprogram` 逻辑不变。
- 两个执行器都不是真机：未接真实 AppID 与微信登录态，`code2session` 由平台桩替代（`openid` 为确定性桩值）。
- 除 4 步浏览器点击 + 2 步官方模拟器外，其余 6 步走接口；这是为了让链条在无 UI 的存量模块上也能跑，全链路口径仍是一条用例串行。
- 耗时基线：页面级 automator 5 次平均 24.57s（第 11 步约 20s 主要是开发者工具窗口启动与首屏编译）；
  组件级 simulate 5 次平均 4.69s。均为本机 mock 数值，接入真实系统后需重新标定 10 分钟阈值。
- `smoke_runs` 运行台账在清理后保留 1 行（含 `cleaned_at`），便于审计；12 张业务表为 0。

## 小程序两步的执行方式（页面级 automator 为主，组件级 simulate 为补充）

第 11、12 步（小程序内完成认证 / 首页首月资源推荐）有两个执行器，由 `--miniapp-executor`（或环境变量
`MINIAPP_EXECUTOR`）选择，默认 `auto`：

| 执行器 | 驱动 | 覆盖范围 | 产出 |
| --- | --- | --- | --- |
| `automator`（主） | 微信官方 `miniprogram-automator` 经**微信开发者工具**自动化端口 | **页面级**：`app.json` 路由、`pages/entry` 真实 `<input>`/`<button>`、`wx.navigateTo` 真实跳转、`pages/home` 真实渲染节点、真实截图 | `01_entry.png`、`01b_entry_certified.png`、`02_home.png`、`03_home_full.png` + `trace.json`（含页面路径、节点计数、耗时）+ 服务端 audit 反证 |
| `simulate`（补充） | 微信官方 `miniprogram-simulate` + `miniprogram-compiler` | **组件级**：单独加载 `components/member-entry`，真实 WXML/WXSS 渲染树、真实事件；不含页面壳/路由 | 三阶段渲染树 HTML + 事件序列 + 21 条断言 |

`auto` 规则：开发者工具与依赖齐备 → `automator`；否则回退 `simulate`，并把
`miniapp_executor` / `miniapp_executor_fallback` 写进 `reports/chain_<run_id>.json`，不静默声称跑过 automator。

小程序工程：仓库内 `miniapp/`（`app.json` 两页：`pages/entry/index` → `pages/home/index`，加 `components/member-entry`）。
`wx.request` 由小程序运行时真实发出，打到本仓自起平台（`SMOKE_BASE_URL`，loopback，不出公网），请求头带本次 `x-run-id`。

### 跑 automator（页面级）

分两步：**先把自动化端口打开**，再跑用例。驱动不会半路去重启开发者工具——上一版试过让驱动自愈，
工具被中途拉起时 automator 会挂在 `getPageMetaByWebviewId` 返回 `null` 上，状态不可预期，所以改成显式两步。

```bash
# 1) 依赖：miniprogram-automator（Node ≥ 16）
bash scripts/setup_miniapp.sh

# 2) 一次性前置（只做一次，之后长期有效）
#    a) 微信开发者工具已安装，并已用微信扫码登录；
#       —— 登录态持久化在本机资料目录，重启工具不用重新扫码，也不涉及手机号/短信。
#    b) 工具内「设置 → 安全设置 → 服务端口」已打开；
#    c) 小程序工程 project.config.json 的 appid 必须是当前登录账号有权访问的。
#       仓库为可移植性保留 touristappid（AppID/AppSecret 一律不入库），
#       真实跑通时把 miniapp/ 复制一份、只改 appid，再用 MINIAPP_PROJECT_DIR 指过去。

export WECHAT_DEVTOOLS_CLI='C:\Program Files (x86)\Tencent\微信web开发者工具\cli.bat'
export MINIAPP_PROJECT_DIR='C:\work\2828_miniapp'        # 带真实 appid 的工程目录（Windows 形式路径）
export MINIAPP_NODE='C:\Program Files\nodejs\node.exe'   # WSL 里跑 pytest 时必须显式指定 Windows 侧 node
export MINIAPP_AUTOMATOR_DRIVER='C:\work\2828_scripts\miniapp_automator.js'
export MINIAPP_AUTOMATOR_WS='ws://127.0.0.1:9420'
#
# 本文实测这组具体取值（2026-11-24，Windows 侧）——
#   WECHAT_DEVTOOLS_CLI = C:\wdt\cli.bat            （cli.bat 的短路径，避免中文目录名/空格）
#   MINIAPP_PROJECT_DIR = C:\Users\<user>\AppData\Local\Temp\2828_auto\miniapp
#   MINIAPP_NODE        = C:\Users\<user>\AppData\Local\Temp\nodejs\node-v26.13.1-win-x64\node.exe
# 路径里有空格或中文时，优先换成 8.3 短路径或复制到纯 ASCII 临时目录。

# 3) 打开自动化端口（显式一步；端口没开就明确报错，不会静默回退）
bash scripts/open_automator_port.sh

# 4) 平台与数据库（开发者工具要连得到，uvicorn 必须监听 0.0.0.0，不能只绑 127.0.0.1）
bash scripts/start_env.sh

# 5) 跑完整 12 步链（第 11、12 步走页面级 automator）
.venv/bin/python -m pytest -m chain -q --miniapp-executor automator

# 也可以只跑小程序两步（已有 run_id/member_id 时）：
# node scripts/miniapp_automator.js --base-url http://127.0.0.1:5600 \
#   --run-id <run_id> --member-id <member_uuid> --out reports/miniapp_autotest \
#   --ws "$MINIAPP_AUTOMATOR_WS" --devtools-cli "$WECHAT_DEVTOOLS_CLI"
```

环境变量全部可选，缺省值：`MINIAPP_NODE=node`、`MINIAPP_PROJECT_DIR=<仓库>/miniapp`、
`MINIAPP_AUTOMATOR_DRIVER=<仓库>/scripts/miniapp_automator.js`、`MINIAPP_AUTOMATOR_PORT=9420`。
非 WSL 环境（Linux/macOS 原生 Node + 本地工程）无需设置前四个。

实现说明（踩过的坑，已在代码里规避）：

- 自定义组件内部节点：开发者工具把组件在页面树里暴露成 `<components/member-entry/index>`，
  `page.$("member-entry")` 匹配不到，需遍历顶层节点按 `outerWxml` 前缀识别，再 `comp.$(".code-input")`。
- 认证后页面立刻 `wx.navigateTo` 卸载，页面 `data` 会跟着消失；认证响应由页面落 `wx.setStorageSync`，
  用例在路由完成后从 storage 回读，作为第 11 步的真实响应证据。
- `miniprogram-automator` 自带 `launch()` 在 Node ≥ 18.20.2 / 20.12.2 上无法 `spawn .bat`（CVE 补丁后禁无 shell 调 .bat），
  所以统一改成「`cli.bat auto` 起窗口 + `automator.connect` 连端口」。


### 跑 simulate（组件级，CI 默认）

```bash
bash scripts/setup_miniapp.sh
.venv/bin/python -m pytest -m chain -q --miniapp-executor simulate
```

### 能力边界（两个执行器共同）

- **非真机**：执行环境是开发者工具 / Node 模拟器，不是手机微信客户端；真机验收需真实 AppID + 扫码。
- **无微信登录态**：`code2session` 由平台桩替代，`openid` 为确定性桩值（`wx_stub_*`）。
- `automator` 的运行记录（12/12 报告、`trace.json`、4 张截图、`requests.jsonl`）见
  `EVIDENCE/miniprogram/automator/`（入口 `RUN.md`）；未实际跑过的环境不做任何「已跑通」表述。

要只跑其余 10 步（CI 的跑法）：加 `--skip-miniprogram`，两步骤记 `skipped`，链路仍串行。
