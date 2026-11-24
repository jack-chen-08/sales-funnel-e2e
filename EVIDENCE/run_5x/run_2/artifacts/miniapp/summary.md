# 小程序两步执行记录（页面级 · miniprogram-automator）

- 执行时间（UTC）：2026-11-24T06:40:31.541Z → 2026-11-24T06:40:49.808Z
- 执行环境：Node v22.23.5 + 微信开发者工具自动化端口（port 9420）
- 项目路径：\\wsl.localhost\Ubuntu\home\ubuntuuser\clawhunt_delivery\2828_recruitment_smoke\miniapp
- 平台地址：http://127.0.0.1:5600
- run_id：smk-5x-r2-20261124-144026-f594　member_id：ef69129a-f0f1-4fd2-bcc9-e02a4ca778f4
- 结论：**passed**（断言 13 条，失败 0 条）

## 步骤与耗时

| 阶段 | 页面 | 断言内容 | 耗时(ms) |
|---|---|---|---|
| connect | undefined | 连接已开启自动化端口的开发者工具窗口（复用已编译好的小程序项目） | 20 |
| entry | /pages/entry/index | reLaunch 到 pages/entry/index 并等待页面数据就绪 | 4155 |
| certify | /pages/entry/index | 页面内输入验证码并点击「提交认证」按钮（真实点击事件） | 1610 |
| home | pages/home/index | 首页渲染首月资源推荐（页面上真实节点计数） | 1244 |

## 页面上真实数到的节点

- 资源条目：3 项（接口 items=3）
- 条目明细：黑白打印 500 页/配额 500页；洽谈区使用 8 次/配额 8次；共享会议室 4 小时/配额 4小时
- 月份行：资源月份：2026-11　合计行：共 3 项资源

## 截图

- entry：01_entry.png
- certify：01b_entry_certified.png
- home：02_home.png
- homeFull：03_home_full.png

## 断言明细

- PASS 小程序从 pages/entry/index 进入（真实页面，非组件宿主）　`{"pagePath":"/pages/entry/index","phase":"idle","memberId":"ef69129a-f0f1-4fd2-bcc9-e02a4ca778f4","waitMs":12}`
- PASS 入口页渲染出验证码输入框与提交按钮　`{"inCustomComponent":true,"component":"components/member-entry/index","componentNodeHandle":true,"inputNodeFound":true,"buttonNodeFound":true,"inputOuterWxml":"<input class=\"code-input\" placeholder=\"6 位短信验证码\" value=\"\" maxlength=\"6\" type=\"number\"></input>","buttonOuterWxml":"<button class=\`
- PASS 页面 <input> 真实输入 6 位验证码　`{"inputValue":"123456","componentVerifyCode":"","expect":"123456"}`
- PASS 认证接口在页面内真实返回 certified　`{"certify_status":"certified","openid_stub":"wx_stub_96b7717fe29b","application_status":"certified"}`
- PASS 小程序桩 openid 形如 wx_stub_*　`"wx_stub_96b7717fe29b"`
- PASS 认证成功后 wx.navigateTo 真实跳转到 pages/home/index　`{"currentPath":"pages/home/index","waitMs":234}`
- PASS 首页在页面上渲染出 ≥3 个资源条目　`{"renderedItems":3,"itemTexts":[{"name":"黑白打印 500 页","quota":"配额 500页"},{"name":"洽谈区使用 8 次","quota":"配额 8次"},{"name":"共享会议室 4 小时","quota":"配额 4小时"}]}`
- PASS 页面可见条目数与接口 items 数一致　`{"renderedItems":3,"apiItems":3}`
- PASS 页面可见月份与接口返回月份一致　`{"monthText":"资源月份：2026-11","apiMonth":"2026-11"}`
- PASS 所有可见资源配额为正数　`[{"name":"黑白打印 500 页","quota":"配额 500页"},{"name":"洽谈区使用 8 次","quota":"配额 8次"},{"name":"共享会议室 4 小时","quota":"配额 4小时"}]`
- PASS 服务端 audit 记录到第 11 步事件（请求携带正确 x-run-id 才会命中本 run）　`{"step_no":11,"step_key":"miniapp_certify","event":"miniapp_certify:ok","payload":{"member_id":"ef69129a-f0f1-4fd2-bcc9-e02a4ca778f4","openid_stub":"wx_stub_96b7717fe29b"}}`
- PASS 服务端 audit 记录到第 12 步事件　`{"step_no":12,"step_key":"miniapp_home","event":"miniapp_home:ok","payload":{"recommendation_id":"20183d77-9f11-4558-8b2c-c5f2bf8fd3d4","month":"2026-11"}}`
- PASS 服务端 audit 的 member_id 与本次小程序会话一致　`{"auditMemberId":"ef69129a-f0f1-4fd2-bcc9-e02a4ca778f4","expected":"ef69129a-f0f1-4fd2-bcc9-e02a4ca778f4"}`
