# 小程序两步执行记录

- 执行时间（UTC）：2026-11-23T19:37:00.114Z → 2026-11-23T19:37:00.348Z
- 执行环境：Node v22.22.3 + 微信官方 miniprogram-simulate（非真机）
- 平台地址：http://127.0.0.1:5600
- run_id：smk-5x-r2-20261124-033655-33ba　member_id：9ed42eb8-d65f-4907-9841-1934007542bd
- 结论：**passed**（断言 21 条，失败 0 条）

## 步骤与渲染树

| 阶段 | 组件 phase | 渲染树 SHA256（前 16 位） | 字节数 | 快照文件 |
| --- | --- | --- | --- | --- |
| 初始 | idle | 4ced3a671a762587 | 962 | 01_initial_render.html |
| 第 11 步 认证后 | certified | e1fffa1d69bd166b | 1309 | 02_after_certify.html |
| 第 12 步 首页后 | home | cb0d14edb3fcffec | 2285 | 03_after_home.html |

## 真实 HTTP 请求

| # | 方法 | 路径 | 状态码 | 耗时(ms) | 响应要点 |
| --- | --- | --- | --- | --- | --- |
| 1 | POST | /api/miniapp/certify | 200 | 20 | certify_status=certified, openid=wx_stub_96b7717fe29b |
| 2 | GET | /api/miniapp/home?member_id=9ed42eb8-d65f-4907-9841-1934007542bd | 200 | 12 | month=2026-11, items=3 |

## 交互事件序列

1. `certified`
2. `home-ready`

## 断言明细

| 断言 | 结果 | 实际值 |
| --- | --- | --- |
| 初始渲染出现「第 11 步 · 企业联系人认证」标题 | PASS | — |
| 初始渲染阶段为待认证（phase=idle） | PASS | `"idle"` |
| 找到验证码输入框 .code-input | PASS | — |
| 找到「提交认证」按钮 .certify-btn | PASS | — |
| 第 11 步向平台发起真实 HTTP 请求 POST /api/miniapp/certify | PASS | `"/api/miniapp/certify"` |
| 认证请求带 x-run-id 头（run 数据隔离） | PASS | `{"content-type":"application/json","x-run-id":"smk-5x-r2-20261124-033655-33ba"}` |
| 认证接口返回 200 | PASS | `200` |
| 认证接口返回 certify_status=certified | PASS | `{"step":"签约企业联系人在小程序完成认证","member_id":"9ed42eb8-d65f-4907-9841-1934007542bd","certify_status":"certified","openid_stub":"wx_stub_96b7717fe29b","channel":"miniprogram-stub","application_status":"certified"}` |
| 组件阶段切换为已认证（phase=certified） | PASS | `"certified"` |
| 渲染树显示认证状态 certified | PASS | — |
| 组件触发 certified 事件 | PASS | `["certified"]` |
| 找到「进入首页」按钮 .home-btn | PASS | — |
| 第 12 步向平台发起真实 HTTP 请求 GET /api/miniapp/home | PASS | `"/api/miniapp/home?member_id=9ed42eb8-d65f-4907-9841-1934007542bd"` |
| 首页接口返回 200 | PASS | `200` |
| 组件阶段切换为已进入首页（phase=home） | PASS | `"home"` |
| 首月资源条目不少于 3 项 | PASS | `3` |
| 每条资源配额为正数 | PASS | `[8,500,4]` |
| 资源月份与接口返回一致 | PASS | `{"dom":"2026-11","api":"2026-11"}` |
| 渲染树中资源条目数量与数据一致 | PASS | `{"rendered":3,"data":3}` |
| 渲染树包含资源月份与条目数文案 | PASS | `{"month":"2026-11","count":3}` |
| 组件触发 home-ready 事件 | PASS | `["certified","home-ready"]` |

## 能力边界（如实声明）

1. 非真机：执行环境是 Node 端微信官方模拟器，不是微信客户端。
2. 无像素截图：模拟器只输出渲染树（WXML 解析结果），不产生位图。需要截图请在微信开发者工具/真机执行。
3. 无微信登录态：`code2session` 由平台侧桩替代，openid 为确定性桩值。
4. wx.request 由 Node http 桥接，经 loopback 打到本仓自起平台（不出公网）；真机由微信客户端发起同一请求。
5. 只加载组件：`pages/entry` 页面壳与 `app.json` 路由（wx.navigateTo）未执行；simulate 不支持路由。页面级需微信开发者工具 + miniprogram-automator（AppID + 扫码，属外部条件）。
