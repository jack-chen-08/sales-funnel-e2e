# 第 11、12 步 · 页面级执行证据（微信开发者工具 + miniprogram-automator）

本目录文件由一次真实运行原样落盘，未做任何手工编辑：`trace.json`、`summary.md`、
`requests.jsonl`、`01_entry.png`、`01b_entry_certified.png`、`02_home.png`、`03_home_full.png`、
`report.json` / `report.md`（12 步整链报告，第 11、12 步 `evidence.executor = miniprogram-automator`）。

- 运行标识：`smk-auto14-20261124-142939-a30c`
- 结论：**passed**，整链 12/12，小程序两步断言 13 条全过、0 失败
- 执行环境：微信官方 `miniprogram-automator` + 微信开发者工具自动化端口（Windows，端口 9420），Node v22.14.0
- 平台：`http://127.0.0.1:5600`（本仓自起 mock，loopback，不出公网）
- 小程序工程：Windows 侧副本 `2828_auto/miniapp`（`project.config.json` 用测试号真实 AppID；仓库内仍为 `touristappid`，AppID/AppSecret 不入库）

## 这两步到底跑了什么（页面级，非组件级）

| 阶段 | 页面/端口 | 证据 |
| --- | --- | --- |
| 连接 | `ws://127.0.0.1:9420` | 复用 `cli.bat auto` 打开的项目窗口，19ms |
| 进入真实页面 | `pages/entry/index` | `wx.reLaunch` 带 `member_id`/`run_id`，页面 `data.phase=idle`，4456ms |
| 真实输入 + 真实点击 | 同上 | 组件内真实 `<input class="code-input">` 输入 123456（节点 WXML 原文入证据）；真 `<button class="certify-btn">提交认证</button>` 点击 → `POST /api/miniapp/certify` → 200，`certify_status=certified`，接口耗时 31ms，1751ms |
| 真实路由 | `pages/home/index` | `wx.navigateTo` 后 `currentPage.path = pages/home/index`，`phase=home`，1456ms |
| 真实渲染节点 | 同上 | 页面上数到 3 个 `.resource-item`（黑白打印 500 页 / 固定车位 2 个 / 共享会议室 4 小时），与接口 `items` 数一致；月份行 `资源月份：2026-11`、合计行 `共 3 项资源` |

## 复现（一条命令链）

```bash
export WECHAT_DEVTOOLS_CLI='C:\Program Files (x86)\Tencent\微信web开发者工具\cli.bat'
export MINIAPP_PROJECT_DIR='C:\work\2828_miniapp'      # 带真实 appid 的工程目录
export MINIAPP_NODE='C:\Program Files\nodejs\node.exe'
export MINIAPP_AUTOMATOR_DRIVER='C:\work\2828_scripts\miniapp_automator.js'
export MINIAPP_AUTOMATOR_WS='ws://127.0.0.1:9420'

bash scripts/open_automator_port.sh                    # 显式打开自动化端口
.venv/bin/python -m pytest -m chain -q --miniapp-executor automator
```

## 连续 5 次（AC1，页面级 automator）

2026-11-24 14:51–14:53 用 `bash scripts/run_5x.sh --miniapp-executor automator` 连跑 5 次，5/5 通过，
每次 12/12、清理残留 0、第 11/12 步执行器均为 `miniprogram-automator`，单次 23.64–26.48s（平均 24.57s）。
run_id：`smk-5x-r1-20261124-145119-2595`(26.48s) / `r2-145157-e059`(24.50s) / `r3-145234-b7e4`(24.47s) /
`r4-145310-6cdc`(23.76s) / `r5-145345-a6e2`(23.64s)。
每次的 4 张截图、`trace.json`、`requests.jsonl` 原样落在 `EVIDENCE/run_5x/run_{1..5}/artifacts/miniapp/`。

## 能力边界（如实，不回避）

1. **非真机**：执行环境是微信开发者工具（桌面版），不是手机微信客户端；真机验收需真实 AppID + 手机扫码安装。
2. **无微信登录态**：`code2session` 由平台桩替代，`openid` 为确定性桩值（`wx_stub_*`），未走真实 `jscode2session`。
3. **一次性窗口**：一次 automator 会话结束后开发者工具的项目窗口会随之关闭（自动化端口关闭），
   因此每次运行前需重跑 `scripts/open_automator_port.sh`；登录态持久化，**不需要重新扫码**。
4. 手机号 `13800000001` 为演示占位号；验证码 `123456` 是平台桩校验码，不经过任何真实短信。
