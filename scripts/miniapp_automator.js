#!/usr/bin/env node
/**
 * 小程序两步（第 11、12 步）页面级真实执行入口 —— 微信官方 miniprogram-automator。
 *
 * 与 scripts/miniapp_smoke.js（组件级 miniprogram-simulate）的区别：
 *   simulate：在 Node 里单独加载组件，验证组件逻辑，不涉及页面壳与路由。
 *   automator：通过微信开发者工具自动化端口驱动**整个小程序项目**，
 *              真实页面（pages/entry → pages/home）、真实 <input>/<button> 交互、
 *              真实 wx.navigateTo 路由、真实渲染节点。
 *
 * 前置条件（缺任一项由 tests/core/miniapp.py 的 availability() 先行判定并给出修复指引）：
 *   1. 已安装微信开发者工具，且「设置 → 安全设置 → 服务端口」已开启；
 *   2. 开发者工具已用微信扫码登录一次（自动化启动复用登录态，无需每次扫码）；
 *   3. miniapp/node_modules 内已装 miniprogram-automator（bash scripts/setup_miniapp.sh）。
 *
 * 用法：
 *   node scripts/miniapp_automator.js --base-url http://127.0.0.1:5600 \
 *     --run-id <run_id> --member-id <member_id> --out reports/<...>/miniapp \
 *     [--devtools-cli "<cli 路径>"] [--port 9420] [--verify-code 123456]
 *
 * 产物（与 simulate 执行器同构，便于报告层复用）：
 *   trace.json / requests.jsonl / summary.md / 01_entry.png / 02_home.png / 03_home_full.png
 */

"use strict";

const fs = require("fs");
const path = require("path");
const http = require("http");
const https = require("https");
const crypto = require("crypto");

const ROOT = path.resolve(__dirname, "..");
const MINIAPP_DIR = path.join(ROOT, "miniapp");

function parseArgs(argv) {
  const out = {};
  for (let i = 2; i < argv.length; i += 1) {
    const token = argv[i];
    if (!token.startsWith("--")) continue;
    const key = token.slice(2);
    const next = argv[i + 1];
    if (next === undefined || next.startsWith("--")) {
      out[key] = true;
    } else {
      out[key] = next;
      i += 1;
    }
  }
  return out;
}

const ARGS = parseArgs(process.argv);
const OUT_DIR = path.resolve(ARGS.out || path.join(ROOT, "reports", "miniapp-automator"));
const BASE_URL = String(ARGS["base-url"] || "http://127.0.0.1:5600").replace(/\/+$/, "");
const RUN_ID = ARGS["run-id"] || "";
const MEMBER_ID = ARGS["member-id"] || "";
const VERIFY_CODE = String(ARGS["verify-code"] || "123456");
const PORT = Number(ARGS.port || 9420);
const LAUNCH_TIMEOUT = Number(ARGS["launch-timeout"] || 90000);
const STEP_TIMEOUT = Number(ARGS["step-timeout"] || 30000);
const DEVTOOLS_CLI = ARGS["devtools-cli"] || process.env.WECHAT_DEVTOOLS_CLI || "";
// 自动化端口直连（可选）：开发者工具已经用 `cli auto --project <dir> --auto-port <port>` 打开，
// 驱动只需连上去。Node ≥ 18.20.2 / 20.12.2 之后 child_process 不再允许直接 spawn .bat/.cmd，
// 官方 automator.launch(cliPath=cli.bat) 会 EINVAL，因此提供端口直连作为等价路径。
const WS_ENDPOINT = ARGS.ws || process.env.WECHAT_AUTOMATOR_WS || "";

fs.mkdirSync(OUT_DIR, { recursive: true });

const startedAt = new Date().toISOString();
const steps = [];
const events = [];
const requests = [];
const assertions = [];
const consoleTail = [];

function recordAssertion(name, ok, detail) {
  assertions.push({ name, ok: !!ok, detail: detail === undefined ? null : detail });
  console.log(`[automator] ${ok ? "PASS" : "FAIL"} ${name}`);
}

function digest(text) {
  return crypto.createHash("sha256").update(String(text), "utf8").digest("hex");
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/** 轮询直到 fn 返回真值，返回 {ok, elapsedMs, value} */
async function waitUntil(fn, timeoutMs, label) {
  const t0 = Date.now();
  let lastErr = null;
  while (Date.now() - t0 < timeoutMs) {
    try {
      const value = await fn();
      if (value) return { ok: true, elapsedMs: Date.now() - t0, value };
    } catch (err) {
      lastErr = err;
    }
    await sleep(200);
  }
  return { ok: false, elapsedMs: Date.now() - t0, value: null, error: lastErr ? String(lastErr.message || lastErr) : null, label };
}

function httpJson(url) {
  return new Promise((resolve, reject) => {
    const target = new URL(url);
    const client = target.protocol === "https:" ? https : http;
    const req = client.get(
      { hostname: target.hostname, port: target.port || (target.protocol === "https:" ? 443 : 80), path: target.pathname + (target.search || "") },
      (res) => {
        let raw = "";
        res.on("data", (chunk) => (raw += chunk));
        res.on("end", () => {
          try {
            resolve({ statusCode: res.statusCode, body: JSON.parse(raw) });
          } catch (err) {
            reject(new Error(`非 JSON 响应（${res.statusCode}）：${raw.slice(0, 200)}`));
          }
        });
      }
    );
    req.on("error", reject);
    req.setTimeout(15000, () => req.destroy(new Error("timeout")));
  });
}

async function screenshot(miniProgram, name, note) {
  const file = path.join(OUT_DIR, name);
  try {
    await miniProgram.screenshot({ path: file });
    return { file: name, ok: true, note };
  } catch (err) {
    return { file: name, ok: false, error: String(err.message || err), note };
  }
}

/**
 * 定位自定义组件节点。
 *
 * 开发者工具把自定义组件在页面树里暴露成 <components/member-entry/index>，
 * page.$("member-entry") / page.$("components/member-entry/index") 都匹配不到，
 * 只能遍历页面顶层节点、按 outerWxml 前缀识别。识别到之后才能用 comp.$(sel)
 * 访问组件内部节点，provider 是真实渲染出来的 <input>/<button>，不是假节点。
 */
async function findComponentNode(page, tagPath) {
  const topNodes = await page.$$("*");
  for (const node of topNodes) {
    const wxml = String(await node.outerWxml().catch(() => ""));
    if (wxml.startsWith("<" + tagPath)) return node;
  }
  return null;
}

async function findNode(page, selector) {
  // 入口页的输入框/按钮在自定义组件 <member-entry> 内部：页面层查不到时进入组件内查。
  const direct = await page.$(selector);
  if (direct) return direct;
  const comp = await findComponentNode(page, "components/member-entry/index");
  if (!comp) return null;
  return await comp.$(selector);
}

const net = require("net");

function portOpen(port, timeoutMs = 800) {
  return new Promise((resolve) => {
    const sock = net.connect({ host: "127.0.0.1", port: port });
    const done = (v) => { try { sock.destroy(); } catch (e) {} resolve(v); };
    sock.setTimeout(timeoutMs);
    sock.once("connect", () => done(true));
    sock.once("timeout", () => done(false));
    sock.once("error", () => done(false));
  });
}

async function main() {
  let automator;
  try {
    automator = require(path.join(MINIAPP_DIR, "node_modules", "miniprogram-automator"));
  } catch (err) {
    throw new Error(
      "未安装 miniprogram-automator：请在 miniapp 目录执行 `npm install`（或 bash scripts/setup_miniapp.sh）"
    );
  }
  if (!WS_ENDPOINT) {
    if (!DEVTOOLS_CLI) {
      throw new Error(
        "缺少微信开发者工具 CLI 路径：请传 --devtools-cli 或设置环境变量 WECHAT_DEVTOOLS_CLI（Windows 默认 " +
          "C:\\\\Program Files (x86)\\\\Tencent\\\\微信web开发者工具\\\\cli.bat），" +
          "或用 --ws 直连已开启自动化端口的开发者工具"
      );
    }
    if (!fs.existsSync(DEVTOOLS_CLI)) {
      throw new Error(`微信开发者工具 CLI 不存在：${DEVTOOLS_CLI}`);
    }
  }

  const launchStartedAt = Date.now();
  let miniProgram;
  let launchStage;
  // 只连接、不自愈：自动化端口必须由 `cli.bat auto --project <目录> --auto-port <端口>`
  // 提前打开（见 scripts/open_automator_port.sh）。驱动半路重开工具会让窗口状态不可预期，
  // 上一版试过，会挂在 getPageMetaByWebviewId 返回 null 上，因此改成「没开就明确报错」。
  const wsEndpoint = WS_ENDPOINT || "ws://127.0.0.1:" + PORT;
  const autoPort = Number(String(wsEndpoint).split(":").pop());
  const portIsOpen = await portOpen(autoPort);
  if (!portIsOpen) {
    throw new Error(
      "[automator] 自动化端口 " + autoPort + " 未开启。请先执行：\n" +
        "  bash scripts/open_automator_port.sh   # 内部调用 cli.bat auto --project <项目目录> --auto-port " + autoPort + "\n" +
        "（开发者工具需已登录；登录态会持久化，重启工具不用重新扫码）"
    );
  }

  let lastErr = null;
  for (let attempt = 1; attempt <= 3 && !miniProgram; attempt += 1) {
    try {
      miniProgram = await automator.connect({ wsEndpoint });
    } catch (err) {
      lastErr = err;
      await new Promise((r) => setTimeout(r, 2000));
    }
  }
  if (!miniProgram) {
    throw new Error("[automator] 连接自动化端口失败（" + wsEndpoint + "）：" + (lastErr && lastErr.message));
  }
  launchStage = {
    stage: "connect",
    name: "连接已开启自动化端口的开发者工具窗口（复用已编译好的小程序项目）",
    phase: "connected",
    durationMs: Date.now() - launchStartedAt,
    projectPath: MINIAPP_DIR,
    wsEndpoint,
    autoPort,
    portWasOpen: true
  };
  steps.push(launchStage);

  try {
    // ── 第 11 步 前置：从真实页面 pages/entry 进入 ───────────────────────
    const entryUrl =
      "/pages/entry/index?member_id=" + encodeURIComponent(MEMBER_ID) +
      "&run_id=" + encodeURIComponent(RUN_ID);
    const entryT0 = Date.now();
    const entryPage = await miniProgram.reLaunch(entryUrl);
    const entryReady = await waitUntil(async () => {
      const data = await entryPage.data();
      return data && data.memberId === MEMBER_ID;
    }, STEP_TIMEOUT, "entry-ready");
    const entryData0 = await entryPage.data();
    const shotEntry = await screenshot(miniProgram, "01_entry.png", "入口页初始态");
    steps.push({
      stage: "entry",
      name: "reLaunch 到 pages/entry/index 并等待页面数据就绪",
      pagePath: "/pages/entry/index",
      durationMs: Date.now() - entryT0,
      waitMs: entryReady.elapsedMs,
      phase: entryData0.phase,
      domSha256: digest(JSON.stringify(entryData0))
    });
    events.push({ seq: events.length + 1, name: "page.entry.ready", detail: { phase: entryData0.phase } });
    recordAssertion("小程序从 pages/entry/index 进入（真实页面，非组件宿主）", entryReady.ok && entryData0.phase === "idle", {
      pagePath: "/pages/entry/index",
      phase: entryData0.phase,
      memberId: entryData0.memberId,
      waitMs: entryReady.elapsedMs
    });
    const entryComp = await findComponentNode(entryPage, "components/member-entry/index");
    const entryInputNode = await findNode(entryPage, ".code-input");
    const entryBtnNode = await findNode(entryPage, ".certify-btn");
    recordAssertion("入口页渲染出验证码输入框与提交按钮", entryInputNode !== null && entryBtnNode !== null, {
      inCustomComponent: true,
      component: "components/member-entry/index",
      componentNodeHandle: entryComp !== null,
      inputNodeFound: entryInputNode !== null,
      buttonNodeFound: entryBtnNode !== null,
      inputOuterWxml: entryInputNode ? String(await entryInputNode.outerWxml()).replace(/\s+/g, " ") : null,
      buttonOuterWxml: entryBtnNode ? String(await entryBtnNode.outerWxml()).replace(/\s+/g, " ") : null
    });

    // ── 第 11 步：输入验证码 → 点击提交 → 认证 ──────────────────────────
    const certifyT0 = Date.now();
    const codeInput = entryInputNode || (await findNode(entryPage, ".code-input"));
    await codeInput.input(VERIFY_CODE);
    const filledComp = entryComp ? await entryComp.data() : {};
    const filledInput = await codeInput.value().catch(() => null);
    const filledPage = await entryPage.data().catch(() => ({}));
    recordAssertion("页面 <input> 真实输入 6 位验证码", String(filledInput || filledComp.verifyCode || filledPage.verifyCode || "") === VERIFY_CODE, {
      inputValue: filledInput,
      componentVerifyCode: filledComp.verifyCode,
      pageVerifyCode: filledPage.verifyCode,
      expect: VERIFY_CODE
    });

    const certifyBtn = entryBtnNode || (await findNode(entryPage, ".certify-btn"));
    await certifyBtn.tap();
    events.push({ seq: events.length + 1, name: "tap.certify" });

    // 认证结果：页面在 onCertified 里把响应写进 storage 后立即 navigateTo，
    // 因此认证态不能只看页面 data（页面即将卸载），而是等真实路由完成后从 storage 回读。
    const nav = await waitUntil(async () => {
      const current = await miniProgram.currentPage();
      return current && current.path === "pages/home/index" ? current : null;
    }, STEP_TIMEOUT, "navigate-home");
    const entryData1 = await miniProgram
      .evaluate(() => {
        try { return wx.getStorageSync("smoke_last_certify") || null; } catch (e) { return null; }
      })
      .catch(() => null);
    const certified = { ok: !!entryData1, value: entryData1, elapsedMs: nav.elapsedMs };
    const shotCertify = await screenshot(miniProgram, "01b_entry_certified.png", "认证完成后（已真实跳转首页）");
    steps.push({
      stage: "certify",
      name: "页面内输入验证码并点击「提交认证」按钮（真实点击事件）",
      pagePath: "/pages/entry/index",
      durationMs: Date.now() - certifyT0,
      waitMs: certified.elapsedMs,
      phase: "certified",
      domSha256: digest(JSON.stringify(entryData1))
    });
    events.push({ seq: events.length + 1, name: "page.certified", detail: { certify_status: entryData1 && entryData1.certify_status } });

    const certifyBody = entryData1 || {};
    requests.push({
      seq: requests.length + 1,
      at: new Date().toISOString(),
      method: "POST",
      url: BASE_URL + "/api/miniapp/certify",
      path: "/api/miniapp/certify",
      statusCode: certifyBody.certify_status === "certified" ? 200 : null,
      requestHeaders: { "x-run-id": RUN_ID, "content-type": "application/json" },
      requestBody: { member_id: MEMBER_ID, verify_code: VERIFY_CODE },
      responseBody: certifyBody,
      durationMs: entryData1 && typeof entryData1.duration_ms === "number" ? entryData1.duration_ms : null,
      capture: "页面数据回读（wx.request 在开发者工具运行时内执行，响应由页面 setData 保存）"
    });

    recordAssertion("认证接口在页面内真实返回 certified", certifyBody.certify_status === "certified", {
      certify_status: certifyBody.certify_status,
      openid_stub: certifyBody.openid_stub,
      application_status: certifyBody.application_status,
      durationMs: entryData1.lastCertifyMs
    });
    recordAssertion("小程序桩 openid 形如 wx_stub_*", String(certifyBody.openid_stub || "").startsWith("wx_stub_"), certifyBody.openid_stub);

    // ── 第 12 步：真实路由到首页（等待已在上一段完成，这里只做断言） ──────
    const navT0 = nav.elapsedMs ? Date.now() - nav.elapsedMs : Date.now();
    const homePage = nav.value;
    recordAssertion("认证成功后 wx.navigateTo 真实跳转到 pages/home/index", nav.ok, {
      currentPath: homePage ? homePage.path : null,
      waitMs: nav.elapsedMs
    });

    if (!homePage) {
      steps.push({ stage: "home", name: "等待首页路由", durationMs: Date.now() - navT0, phase: "navigate_timeout" });
      throw new Error(`等待 pages/home/index 超时（${nav.elapsedMs}ms）`);
    }

    const homeRendered = await waitUntil(async () => {
      const data = await homePage.data();
      return data && data.phase === "home" && Array.isArray(data.items) && data.items.length >= 3 ? data : null;
    }, STEP_TIMEOUT, "home-rendered");
    const homeData = homeRendered.value || (await homePage.data());

    // 页面上真实数节点，而不是只看数据字段
    const itemNodes = await homePage.$$(".resource-item");
    const itemTexts = [];
    for (const node of itemNodes) {
      const nameNode = await node.$(".item-name");
      const quotaNode = await node.$(".item-quota");
      itemTexts.push({
        name: nameNode ? (await nameNode.text()).trim() : null,
        quota: quotaNode ? (await quotaNode.text()).trim() : null
      });
    }
    const monthNode = await homePage.$(".month");
    const countNode = await homePage.$(".item-count");
    const monthText = monthNode ? (await monthNode.text()).trim() : "";
    const countText = countNode ? (await countNode.text()).trim() : "";

    const shotHome = await screenshot(miniProgram, "02_home.png", "首页首月资源推荐");

    steps.push({
      stage: "home",
      name: "首页渲染首月资源推荐（页面上真实节点计数）",
      pagePath: "pages/home/index",
      durationMs: Date.now() - navT0,
      waitMs: homeRendered.elapsedMs,
      phase: homeData.phase,
      domSha256: digest(JSON.stringify(homeData)),
      renderedItems: itemNodes.length,
      monthText,
      countText
    });
    events.push({ seq: events.length + 1, name: "page.home.ok", detail: { items: itemNodes.length } });

    const homeBody = homeData.lastHome || {};
    requests.push({
      seq: requests.length + 1,
      at: new Date().toISOString(),
      method: "GET",
      url: BASE_URL + "/api/miniapp/home?member_id=" + encodeURIComponent(MEMBER_ID),
      path: "/api/miniapp/home?member_id=" + encodeURIComponent(MEMBER_ID),
      statusCode: homeBody.month ? 200 : null,
      requestHeaders: { "x-run-id": RUN_ID },
      requestBody: null,
      responseBody: homeBody,
      durationMs: homeData.lastHomeMs,
      capture: "页面数据回读（同 certify）"
    });

    recordAssertion("首页在页面上渲染出 ≥3 个资源条目", itemNodes.length >= 3, { renderedItems: itemNodes.length, itemTexts });
    recordAssertion("页面可见条目数与接口 items 数一致", itemNodes.length === (homeBody.items || []).length, {
      renderedItems: itemNodes.length,
      apiItems: (homeBody.items || []).length
    });
    recordAssertion("页面可见月份与接口返回月份一致", monthText.includes(String(homeBody.month || "\u0000")), { monthText, apiMonth: homeBody.month });
    recordAssertion("所有可见资源配额为正数", itemTexts.every((it) => /\d/.test(String(it.quota || ""))), itemTexts);

    // ── 服务端对账：证明小程序请求真的到达服务端并推进了链路 ────────────
    let serverAudit = null;
    try {
      const resp = await httpJson(BASE_URL + "/api/admin/run/" + encodeURIComponent(RUN_ID) + "/state");
      serverAudit = resp.body;
    } catch (err) {
      serverAudit = { error: String(err.message || err) };
    }
    const auditEvents = (serverAudit && Array.isArray(serverAudit.events)) ? serverAudit.events : [];
    const auditCertify = auditEvents.find((e) => e.step_key === "miniapp_certify") || null;
    const auditHome = auditEvents.find((e) => e.step_key === "miniapp_home") || null;
    const shotFull = await screenshot(miniProgram, "03_home_full.png", "首页完整截图（含事件日志）");

    recordAssertion("服务端 audit 记录到第 11 步事件（请求携带正确 x-run-id 才会命中本 run）", !!auditCertify, auditCertify);
    recordAssertion("服务端 audit 记录到第 12 步事件", !!auditHome, auditHome);
    recordAssertion(
      "服务端 audit 的 member_id 与本次小程序会话一致",
      !!auditCertify && String((auditCertify.payload || {}).member_id || "") === MEMBER_ID,
      { auditMemberId: auditCertify ? (auditCertify.payload || {}).member_id : null, expected: MEMBER_ID }
    );

    const failed = assertions.filter((a) => !a.ok);
    const trace = {
      tool: "miniprogram-automator",
      note:
        "微信官方 miniprogram-automator + 微信开发者工具自动化端口；真实页面（pages/entry → pages/home）、真实 input/button 事件、真实 wx.navigateTo 路由、真实渲染节点。非真机（未安装到手机），无微信登录态（code2session 由平台桩替代）。",
      startedAt,
      endedAt: new Date().toISOString(),
      baseUrl: BASE_URL,
      memberId: MEMBER_ID,
      runId: RUN_ID,
      verifyCode: VERIFY_CODE,
      devtoolsCli: DEVTOOLS_CLI,
      port: PORT,
      steps,
      events,
      requests,
      assertions,
      screenshots: { entry: shotEntry, certify: shotCertify, home: shotHome, homeFull: shotFull },
      rendered: { items: itemNodes.length, itemTexts, monthText, countText },
      serverAudit: {
        applicationStatus: serverAudit ? serverAudit.status : null,
        certify: auditCertify,
        home: auditHome,
        events: auditEvents.map((e) => ({ step_no: e.step_no, step_key: e.step_key, event: e.event }))
      },
      result: failed.length === 0 ? "passed" : "failed",
      failedAssertions: failed.map((a) => a.name)
    };
    fs.writeFileSync(path.join(OUT_DIR, "trace.json"), JSON.stringify(trace, null, 2), "utf8");
    fs.writeFileSync(path.join(OUT_DIR, "requests.jsonl"), requests.map((r) => JSON.stringify(r)).join("\n") + "\n", "utf8");

    const lines = [
      "# 小程序两步执行记录（页面级 · miniprogram-automator）",
      "",
      `- 执行时间（UTC）：${startedAt} → ${trace.endedAt}`,
      `- 执行环境：Node ${process.version} + 微信开发者工具自动化端口（port ${PORT}）`,
      `- 项目路径：${MINIAPP_DIR}`,
      `- 平台地址：${BASE_URL}`,
      `- run_id：${RUN_ID || "(未传)"}　member_id：${MEMBER_ID}`,
      `- 结论：**${trace.result}**（断言 ${assertions.length} 条，失败 ${failed.length} 条）`,
      "",
      "## 步骤与耗时",
      "",
      "| 阶段 | 页面 | 断言内容 | 耗时(ms) |",
      "|---|---|---|---|",
      ...steps.map((s) => `| ${s.stage} | ${s.pagePath} | ${s.name} | ${s.durationMs} |`),
      "",
      "## 页面上真实数到的节点",
      "",
      `- 资源条目：${itemNodes.length} 项（接口 items=${(homeBody.items || []).length}）`,
      `- 条目明细：${itemTexts.map((it) => `${it.name}/${it.quota}`).join("；") || "(无)"}`,
      `- 月份行：${monthText || "(无)"}　合计行：${countText || "(无)"}`,
      "",
      "## 截图",
      "",
      ...Object.entries(trace.screenshots).map(([k, v]) => `- ${k}：${v.ok ? v.file : "失败 " + v.error}`),
      "",
      "## 断言明细",
      "",
      ...assertions.map((a) => `- ${a.ok ? "PASS" : "FAIL"} ${a.name}${a.detail ? "　`" + JSON.stringify(a.detail).slice(0, 300) + "`" : ""}`),
      ""
    ];
    fs.writeFileSync(path.join(OUT_DIR, "summary.md"), lines.join("\n"), "utf8");

    console.log(`[automator] 执行完成：${trace.result}（断言 ${assertions.length} 条，失败 ${failed.length} 条）`);
    await miniProgram.close();
    process.exit(failed.length === 0 ? 0 : 1);
  } catch (err) {
    const failed = assertions.filter((a) => !a.ok);
    const trace = {
      tool: "miniprogram-automator",
      note: "执行中断：见 error 字段",
      startedAt,
      endedAt: new Date().toISOString(),
      baseUrl: BASE_URL,
      memberId: MEMBER_ID,
      runId: RUN_ID,
      devtoolsCli: DEVTOOLS_CLI,
      steps,
      events,
      requests,
      assertions,
      consoleTail,
      error: String((err && err.stack) || err),
      result: "failed",
      failedAssertions: failed.map((a) => a.name)
    };
    fs.writeFileSync(path.join(OUT_DIR, "trace.json"), JSON.stringify(trace, null, 2), "utf8");
    fs.writeFileSync(path.join(OUT_DIR, "requests.jsonl"), requests.map((r) => JSON.stringify(r)).join("\n") + "\n", "utf8");
    console.error("[automator] 失败：", err && err.message ? err.message : err);
    try {
      await miniProgram.close();
    } catch (_) {
      /* 忽略关闭异常 */
    }
    process.exit(1);
  }
}

main().catch((err) => {
  console.error("[automator] 启动失败：", (err && err.message) || err);
  process.exit(2);
});
