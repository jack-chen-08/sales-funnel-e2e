#!/usr/bin/env node
/**
 * 会员入会小程序两步自动化执行器（第 11 步认证 / 第 12 步首月资源）。
 *
 * 执行环境说明（对外口径，勿夸大）
 * - 使用微信官方 miniprogram-simulate（内部依赖官方 miniprogram-compiler 编译 WXML/WXSS）
 *   在 Node 端加载真实小程序组件，得到真实渲染树、真实事件派发、真实 setData 逻辑。
 * - wx.request 由 Node http 模块桥接，经 loopback（默认 127.0.0.1:5600）打到本仓自起的 mock 平台，
 *   响应为服务端真实返回；不出公网。
 * - 能力边界：不是真机、不是微信宿主；只加载组件，页面壳（pages/entry）与 app.json 路由未执行；
 *   无像素截图、无微信登录态（code2session 由平台桩替代）。
 *   这些缺口已写入 DELIVERY.md 与 EVIDENCE/miniprogram/summary.md。
 *
 * 用法
 *   node scripts/miniapp_smoke.js --base-url http://127.0.0.1:5600 \
 *        --member-id <uuid> --run-id <run_id> [--verify-code 123456] [--out EVIDENCE/miniprogram]
 *
 * 退出码：0 全部断言通过；1 存在失败断言或执行异常。
 */

"use strict";

const fs = require("fs");
const path = require("path");
const http = require("http");
const https = require("https");
const crypto = require("crypto");

const ROOT = path.resolve(__dirname, "..");
const COMPONENT = path.join(ROOT, "miniapp", "components", "member-entry", "index");

// ---------------------------------------------------------------- 参数

function parseArgs(argv) {
  const out = {
    "base-url": "http://127.0.0.1:5600",
    "member-id": "",
    "run-id": "",
    "verify-code": "123456",
    phone: "13800000001",
    company: "星澜数字科技（虚构）",
    contact: "林知远（虚构）",
    out: path.join(ROOT, "EVIDENCE", "miniprogram"),
    timeout: "15000"
  };
  for (let i = 2; i < argv.length; i += 1) {
    const key = argv[i].replace(/^--/, "");
    const val = argv[i + 1];
    if (key in out && val !== undefined && !val.startsWith("--")) {
      out[key] = val;
      i += 1;
    }
  }
  return out;
}

const ARGS = parseArgs(process.argv);
if (!ARGS["member-id"]) {
  console.error("[miniapp] 缺少 --member-id（会员档案 ID，由平台第 10 步「会员经理领取交接」返回）");
  process.exit(2);
}

// ---------------------------------------------------------------- 宿主环境

// 依赖装在 miniapp/node_modules（小程序工程自带 devDependencies），
// 本脚本位于 scripts/，需显式以 miniapp 为解析根。
const { createRequire } = require("module");
const miniappRequire = createRequire(path.join(ROOT, "miniapp", "package.json"));

miniappRequire("jsdom-global")("<!doctype html><html><body></body></html>", { pretendToBeVisual: true });
const simulate = miniappRequire("miniprogram-simulate"); // 先 require：wx 全局由它注入

const requests = [];
const events = [];
const assertions = [];

function recordAssertion(name, ok, detail) {
  assertions.push({ name, ok: !!ok, detail: detail === undefined ? null : detail });
  return !!ok;
}

function digest(text) {
  return crypto.createHash("sha256").update(text, "utf8").digest("hex");
}

/**
 * 用 Node http 实现真实 wx.request。
 * 组件侧代码不做任何改动 —— 真机上由微信客户端提供同一接口。
 */
global.wx.request = function (opts) {
  const startedAt = Date.now();
  const url = new URL(opts.url);
  const isHttps = url.protocol === "https:";
  const payload = opts.data === undefined || opts.data === null
    ? ""
    : typeof opts.data === "string" ? opts.data : JSON.stringify(opts.data);
  const headers = Object.assign(
    { "content-type": "application/json", "content-length": Buffer.byteLength(payload) },
    opts.header || {}
  );
  const record = {
    seq: requests.length + 1,
    at: new Date().toISOString(),
    method: (opts.method || "GET").toUpperCase(),
    url: opts.url,
    path: url.pathname + (url.search || ""),
    requestHeaders: opts.header || {},
    requestBody: opts.data === undefined ? null : opts.data,
    statusCode: null,
    responseBody: null,
    durationMs: null
  };
  requests.push(record);

  const client = isHttps ? https : http;
  const req = client.request(
    {
      hostname: url.hostname,
      port: url.port || (isHttps ? 443 : 80),
      path: url.pathname + (url.search || ""),
      method: record.method,
      headers
    },
    (res) => {
      let raw = "";
      res.on("data", (chunk) => (raw += chunk));
      res.on("end", () => {
        let data = raw;
        try {
          data = JSON.parse(raw);
        } catch (_) {
          /* 保留原文 */
        }
        record.statusCode = res.statusCode;
        record.responseBody = data;
        record.durationMs = Date.now() - startedAt;
        (opts.success || (() => {}))({ statusCode: res.statusCode, header: res.headers, data });
      });
    }
  );
  req.on("error", (err) => {
    record.statusCode = 0;
    record.error = err.message;
    record.durationMs = Date.now() - startedAt;
    (opts.fail || (() => {}))({ errMsg: "request:fail " + err.message });
  });
  if (payload) {
    req.write(payload);
  }
  req.end();
};

// ---------------------------------------------------------------- 工具

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

async function waitFor(predicate, label, timeoutMs) {
  const deadline = Date.now() + Number(timeoutMs || ARGS.timeout);
  while (Date.now() < deadline) {
    if (predicate()) {
      return true;
    }
    await sleep(50);
  }
  recordAssertion(`等待条件超时：${label}`, false, { label, timeoutMs: Number(timeoutMs) });
  return false;
}

function snapshot(comp) {
  const html = comp.dom.innerHTML;
  return { html, sha256: digest(html), bytes: Buffer.byteLength(html, "utf8") };
}

// ---------------------------------------------------------------- 主流程

(async function main() {
  const startedAt = new Date().toISOString();
  const outDir = path.isAbsolute(ARGS.out) ? ARGS.out : path.join(ROOT, ARGS.out);
  fs.mkdirSync(outDir, { recursive: true });

  const id = simulate.load(COMPONENT);
  const comp = simulate.render(id, {
    baseUrl: ARGS["base-url"],
    memberId: ARGS["member-id"],
    runId: ARGS["run-id"],
    phone: ARGS.phone,
    company: ARGS.company,
    contact: ARGS.contact
  });
  comp.attach(document.createElement("parent-wrapper"));

  // 捕获组件触发的事件（真机由页面 bind: 接收）
  ["certified", "home-ready", "failed"].forEach((name) => {
    comp.addEventListener(name, (e) => {
      events.push({ seq: events.length + 1, name, detail: e.detail });
    });
  });

  const steps = [];

  // ── 步骤 A：初始渲染 ──────────────────────────────────────────
  const s0 = snapshot(comp);
  fs.writeFileSync(path.join(outDir, "01_initial_render.html"), s0.html, "utf8");
  recordAssertion("初始渲染出现「第 11 步 · 企业联系人认证」标题", s0.html.includes("第 11 步"));
  recordAssertion("初始渲染阶段为待认证（phase=idle）", comp.instance.data.phase === "idle", comp.instance.data.phase);
  steps.push({ stage: "initial", phase: comp.instance.data.phase, domSha256: s0.sha256, domBytes: s0.bytes });

  // ── 步骤 B：输入验证码并点击「提交认证」（第 11 步）──────────
  const input = comp.querySelector(".code-input");
  if (!recordAssertion("找到验证码输入框 .code-input", !!input)) {
    throw new Error("渲染树中缺少 .code-input");
  }
  input.dispatchEvent("input", { detail: { value: ARGS["verify-code"] } });
  await waitFor(() => comp.instance.data.verifyCode === ARGS["verify-code"], "验证码写入组件数据");

  const certifyBtn = comp.querySelector(".certify-btn");
  if (!recordAssertion("找到「提交认证」按钮 .certify-btn", !!certifyBtn)) {
    throw new Error("渲染树中缺少 .certify-btn");
  }
  certifyBtn.dispatchEvent("tap");
  await waitFor(() => comp.instance.data.phase === "certified" || comp.instance.data.phase === "error",
    "认证请求返回并更新阶段");

  const s1 = snapshot(comp);
  fs.writeFileSync(path.join(outDir, "02_after_certify.html"), s1.html, "utf8");
  const certifyReq = requests.find((r) => r.path.startsWith("/api/miniapp/certify"));
  recordAssertion("第 11 步向平台发起真实 HTTP 请求 POST /api/miniapp/certify",
    !!certifyReq && certifyReq.method === "POST", certifyReq ? certifyReq.path : "未发出请求");
  recordAssertion("认证请求带 x-run-id 头（run 数据隔离）",
    !!(certifyReq && certifyReq.requestHeaders && certifyReq.requestHeaders["x-run-id"]),
    certifyReq ? certifyReq.requestHeaders : null);
  recordAssertion("认证接口返回 200", !!(certifyReq && certifyReq.statusCode === 200),
    certifyReq ? certifyReq.statusCode : null);
  recordAssertion("认证接口返回 certify_status=certified",
    !!(certifyReq && certifyReq.responseBody && certifyReq.responseBody.certify_status === "certified"),
    certifyReq ? certifyReq.responseBody : null);
  recordAssertion("组件阶段切换为已认证（phase=certified）", comp.instance.data.phase === "certified",
    comp.instance.data.phase);
  recordAssertion("渲染树显示认证状态 certified", s1.html.includes("certified"));
  recordAssertion("组件触发 certified 事件", events.some((e) => e.name === "certified"),
    events.map((e) => e.name));
  steps.push({ stage: "certify", phase: comp.instance.data.phase, domSha256: s1.sha256, domBytes: s1.bytes });

  if (comp.instance.data.phase !== "certified") {
    throw new Error(`认证阶段失败：${comp.instance.data.errorMsg || comp.instance.data.phase}`);
  }

  // ── 步骤 C：点击「进入首页领取首月资源」（第 12 步）─────────
  const homeBtn = comp.querySelector(".home-btn");
  if (!recordAssertion("找到「进入首页」按钮 .home-btn", !!homeBtn)) {
    throw new Error("渲染树中缺少 .home-btn");
  }
  homeBtn.dispatchEvent("tap");
  await waitFor(() => comp.instance.data.phase === "home" || comp.instance.data.phase === "error",
    "首页请求返回并更新阶段");

  const s2 = snapshot(comp);
  fs.writeFileSync(path.join(outDir, "03_after_home.html"), s2.html, "utf8");
  const homeReq = requests.find((r) => r.path.startsWith("/api/miniapp/home"));
  recordAssertion("第 12 步向平台发起真实 HTTP 请求 GET /api/miniapp/home",
    !!homeReq && homeReq.method === "GET", homeReq ? homeReq.path : "未发出请求");
  recordAssertion("首页接口返回 200", !!(homeReq && homeReq.statusCode === 200),
    homeReq ? homeReq.statusCode : null);
  recordAssertion("组件阶段切换为已进入首页（phase=home）", comp.instance.data.phase === "home",
    comp.instance.data.phase);

  const items = comp.instance.data.items || [];
  recordAssertion("首月资源条目不少于 3 项", items.length >= 3, items.length);
  recordAssertion("每条资源配额为正数", items.every((it) => Number(it.quota) > 0),
    items.map((it) => it.quota));
  const month = (homeReq && homeReq.responseBody && homeReq.responseBody.month) || "";
  recordAssertion("资源月份与接口返回一致", !!month && comp.instance.data.month === month,
    { dom: comp.instance.data.month, api: month });

  // 渲染树里实际渲染出的资源条目数量必须与数据一致（证明 WXML 列表真实生效）
  const renderedItems = (s2.html.match(/class="[^"]*resource-item[^"]*"/g) || []).length;
  recordAssertion("渲染树中资源条目数量与数据一致", renderedItems === items.length,
    { rendered: renderedItems, data: items.length });
  recordAssertion("渲染树包含资源月份与条目数文案",
    s2.html.includes(month) && s2.html.includes(`共 ${items.length} 项资源`), { month, count: items.length });
  recordAssertion("组件触发 home-ready 事件", events.some((e) => e.name === "home-ready"),
    events.map((e) => e.name));
  steps.push({ stage: "home", phase: comp.instance.data.phase, domSha256: s2.sha256, domBytes: s2.bytes });

  // ── 落盘 ────────────────────────────────────────────────────
  const failed = assertions.filter((a) => !a.ok);
  const trace = {
    tool: "miniprogram-simulate",
    note: "Node 端微信官方小程序模拟器；真实渲染树 + 真实事件 + 真实 HTTP 出网。非真机、无像素截图、无微信登录态。",
    startedAt,
    endedAt: new Date().toISOString(),
    baseUrl: ARGS["base-url"],
    memberId: ARGS["member-id"],
    runId: ARGS["run-id"],
    verifyCode: ARGS["verify-code"],
    steps,
    events,
    requests,
    assertions,
    result: failed.length === 0 ? "passed" : "failed",
    failedAssertions: failed.map((a) => a.name)
  };
  fs.writeFileSync(path.join(outDir, "trace.json"), JSON.stringify(trace, null, 2), "utf8");
  fs.writeFileSync(
    path.join(outDir, "requests.jsonl"),
    requests.map((r) => JSON.stringify(r)).join("\n") + "\n",
    "utf8"
  );

  const lines = [
    "# 小程序两步执行记录",
    "",
    `- 执行时间（UTC）：${startedAt} → ${trace.endedAt}`,
    `- 执行环境：Node ${process.version} + 微信官方 miniprogram-simulate（非真机）`,
    `- 平台地址：${ARGS["base-url"]}`,
    `- run_id：${ARGS["run-id"] || "(未传)"}　member_id：${ARGS["member-id"]}`,
    `- 结论：**${trace.result}**（断言 ${assertions.length} 条，失败 ${failed.length} 条）`,
    "",
    "## 步骤与渲染树",
    "",
    "| 阶段 | 组件 phase | 渲染树 SHA256（前 16 位） | 字节数 | 快照文件 |",
    "| --- | --- | --- | --- | --- |",
    `| 初始 | ${steps[0].phase} | ${steps[0].domSha256.slice(0, 16)} | ${steps[0].domBytes} | 01_initial_render.html |`,
    `| 第 11 步 认证后 | ${steps[1].phase} | ${steps[1].domSha256.slice(0, 16)} | ${steps[1].domBytes} | 02_after_certify.html |`,
    `| 第 12 步 首页后 | ${steps[2].phase} | ${steps[2].domSha256.slice(0, 16)} | ${steps[2].domBytes} | 03_after_home.html |`,
    "",
    "## 真实 HTTP 请求",
    "",
    "| # | 方法 | 路径 | 状态码 | 耗时(ms) | 响应要点 |",
    "| --- | --- | --- | --- | --- | --- |"
  ];
  requests.forEach((r) => {
    const body = r.responseBody || {};
    const brief = r.path.startsWith("/api/miniapp/certify")
      ? `certify_status=${body.certify_status}, openid=${body.openid_stub || ""}`
      : r.path.startsWith("/api/miniapp/home")
        ? `month=${body.month}, items=${(body.items || []).length}`
        : JSON.stringify(body).slice(0, 60);
    lines.push(`| ${r.seq} | ${r.method} | ${r.path} | ${r.statusCode} | ${r.durationMs} | ${brief} |`);
  });
  lines.push("", "## 交互事件序列", "");
  events.forEach((e) => lines.push(`${e.seq}. \`${e.name}\``));
  lines.push("", "## 断言明细", "", "| 断言 | 结果 | 实际值 |", "| --- | --- | --- |");
  assertions.forEach((a) => {
    lines.push(`| ${a.name} | ${a.ok ? "PASS" : "FAIL"} | ${a.detail === null ? "—" : `\`${JSON.stringify(a.detail)}\``} |`);
  });
  lines.push(
    "",
    "## 能力边界（如实声明）",
    "",
    "1. 非真机：执行环境是 Node 端微信官方模拟器，不是微信客户端。",
    "2. 无像素截图：模拟器只输出渲染树（WXML 解析结果），不产生位图。需要截图请在微信开发者工具/真机执行。",
    "3. 无微信登录态：`code2session` 由平台侧桩替代，openid 为确定性桩值。",
    "4. wx.request 由 Node http 桥接，经 loopback 打到本仓自起平台（不出公网）；真机由微信客户端发起同一请求。",
    "5. 只加载组件：`pages/entry` 页面壳与 `app.json` 路由（wx.navigateTo）未执行；simulate 不支持路由。页面级需微信开发者工具 + miniprogram-automator（AppID + 扫码，属外部条件）。",
    ""
  );
  fs.writeFileSync(path.join(outDir, "summary.md"), lines.join("\n"), "utf8");

  console.log(`[miniapp] 执行完成：${trace.result}（断言 ${assertions.length} 条，失败 ${failed.length} 条）`);
  console.log(`[miniapp] 证据目录：${outDir}`);
  if (failed.length) {
    failed.forEach((a) => console.error(`  FAIL ${a.name} → ${JSON.stringify(a.detail)}`));
    process.exit(1);
  }
  process.exit(0);
})().catch((err) => {
  console.error("[miniapp] 执行异常：" + (err && err.stack ? err.stack : err));
  process.exit(1);
});
