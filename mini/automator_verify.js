#!/usr/bin/env node
/**
 * miniprogram-automator 执行器：操作真微信小程序完成会员认证。
 *
 * 前置（本仓 CI 不满足，故该路径未在本机验证）：
 *   1. 安装微信开发者工具并登录
 *   2. 工具 -> 设置 -> 安全设置 -> 打开「服务端口」
 *   3. 项目已导入（默认 ./mini/app，可用 MINI_PROJECT_PATH 覆盖）
 *   4. npm i miniprogram-automator
 *
 * 用法：node mini/automator_verify.js
 * 输出（最后一行 JSON）：{"member_id":"mb-xxxx","driver":"miniprogram-automator"}
 */
const automator = require('miniprogram-automator');

(async () => {
  const projectPath = process.env.MINI_PROJECT_PATH || './mini/app';
  const cliPath = process.env.WX_DEVTOOLS_CLI || undefined;
  const leadId = process.env.MINI_LEAD_ID || '';
  const phone = process.env.MINI_PHONE || '';
  const code = process.env.MINI_CODE || '';

  const miniProgram = await automator.launch({
    projectPath,
    cliPath,
    timeout: 120000,
  });

  try {
    const page = await miniProgram.reLaunch(`/pages/login/index?lead_id=${leadId}`);
    await page.waitFor(500);
    const phoneInput = await page.$('#phone');
    await phoneInput.input(phone);
    const codeInput = await page.$('#code');
    await codeInput.input(code);
    const submit = await page.$('#submit-mini');
    await submit.tap();
    await page.waitFor(1500);

    const memberEl = await page.$('#member-id');
    if (!memberEl) {
      throw new Error('认证后未找到 #member-id，检查认证页实现或后端地址');
    }
    const memberId = (await memberEl.text()).trim();
    console.log(JSON.stringify({ member_id: memberId, driver: 'miniprogram-automator' }));
  } finally {
    await miniProgram.close();
  }
})().catch((err) => {
  console.error(String(err && err.stack || err));
  process.exit(1);
});
