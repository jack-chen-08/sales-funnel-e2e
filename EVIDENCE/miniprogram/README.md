# 小程序两步（第 11、12 步）执行证据

本目录的 6 个文件由一次真实运行原样落盘，未做任何手工编辑。

| 文件 | 内容 |
| --- | --- |
| `01_initial_render.html` | 组件渲染树初始态（phase=idle，仅认证表单） |
| `02_after_certify.html` | 提交验证码后的渲染树（phase=certified，出现「进入首页」） |
| `03_after_home.html` | 进入首页后的渲染树（phase=home，3 条首月资源） |
| `requests.jsonl` | 小程序内发出的真实 HTTP 请求/响应逐条记录 |
| `trace.json` | 完整轨迹：渲染树 SHA256、交互事件序列、请求、21 条断言的机器可读结果 |
| `summary.md` | 同上的人类可读版本（含能力边界声明） |

## 执行环境（如实口径）

- 微信官方 `miniprogram-simulate`（内部依赖官方 `miniprogram-compiler` 编译仓库内真实 WXML/WXSS）
- Node v22.22.3；组件取自 `miniapp/components/member-entry`，与真机运行的组件是同一份代码
- 组件内 `wx.request` 由驱动脚本用 Node http 桥接，**经 loopback（127.0.0.1:5600）打到本仓自起平台**，不出公网

## 能力边界（不需要客户追问的部分）

1. **非真机**：执行环境是 Node 端官方模拟器，不是微信客户端。
2. **无像素截图**：模拟器输出渲染树（WXML 解析 + WXSS 作用域后的 DOM 结构），不产生位图。需要像素级界面留证请在微信开发者工具或真机执行。
3. **无微信登录态**：`code2session` 由平台侧桩替代，`openid` 为确定性桩值（`wx_stub_*`）。
4. 渲染树中的手机号 `13800000001` 为演示占位号，非真实号码。
5. **只加载组件**：执行入口是 `miniapp/components/member-entry`，`pages/entry` 页面壳与 `app.json` 路由（`wx.navigateTo`）**未执行**——`miniprogram-simulate` 不支持页面路由。要页面级只有微信开发者工具 + `miniprogram-automator`（AppID + 扫码，属外部条件）。

## 复现

```bash
bash scripts/start_env.sh          # 起 mock 平台
bash scripts/setup_miniapp.sh      # 安装 Node 侧依赖（首次）
.venv/bin/python -m pytest -m chain -q   # 第 11、12 步即由小程序模拟器执行
```

单独驱动小程序两步（需要先有 member_id）：

```bash
node scripts/miniapp_smoke.js \
  --base-url http://127.0.0.1:5600 \
  --member-id <会员ID> \
  --run-id <本次 run_id> \
  --out reports/artifacts/<run_id>/miniapp
```
