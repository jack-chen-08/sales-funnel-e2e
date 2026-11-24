/**
 * 会员入会入口页（第 11 步起点）。
 *
 * 真机/开发者工具进入方式：
 *   /pages/entry/index?member_id=<会员ID>&run_id=<本次冒烟 run_id>&phone=&company=&contact=
 *
 * 认证动作由页面上的 member-entry 组件完成；组件认证成功后页面负责真实路由跳转到首页
 * （pages/home/index），这一步是 automator 页面级用例的关键断言点：小程序真的发生了
 * wx.navigateTo，而不是仅把组件内部状态改成了 home。
 */
Page({
  data: {
    baseUrl: "",
    memberId: "",
    runId: "",
    phone: "",
    company: "",
    contact: "",
    phase: "idle",
    phaseLabel: "待认证",
    lastCertify: null,
    lastCertifyMs: null,
    navigatedAt: null,
    homePath: "",
    errorMsg: "",
    events: []
  },

  onLoad(query) {
    const app = getApp();
    const base = (app && app.globalData && app.globalData.baseUrl) || "http://127.0.0.1:5600";
    this.setData({
      baseUrl: base,
      memberId: (query && query.member_id) || "",
      runId: (query && query.run_id) || "",
      phone: (query && query.phone) || "",
      company: (query && query.company) || "",
      contact: (query && query.contact) || ""
    });
  },

  /** 组件认证成功 → 页面真实跳转到首页 */
  onCertified(e) {
    const detail = (e && e.detail) || {};
    this.setData({
      phase: "certified",
      phaseLabel: "已认证",
      lastCertify: detail,
      lastCertifyMs: typeof detail.duration_ms === "number" ? detail.duration_ms : null
    });
    this._pushEvent("page.certified");
    // 认证响应落 storage：页面紧接着 navigateTo，页面 data 会随卸载消失，
    // 自动化用例（第 11 步）从这里回读真实接口响应作为证据。
    try {
      wx.setStorageSync("smoke_last_certify", Object.assign({}, detail, { at: Date.now() }));
    } catch (err) {
      console.error("[miniapp] persist certify failed", err);
    }
    const url =
      "/pages/home/index?member_id=" + encodeURIComponent(this.data.memberId) +
      "&run_id=" + encodeURIComponent(this.data.runId) +
      "&phone=" + encodeURIComponent(this.data.phone) +
      "&company=" + encodeURIComponent(this.data.company) +
      "&contact=" + encodeURIComponent(this.data.contact);
    wx.navigateTo({
      url,
      success: () => {
        this.setData({ navigatedAt: Date.now(), homePath: "/pages/home/index" });
        this._pushEvent("page.navigate.home");
      },
      fail: (err) => {
        this.setData({ errorMsg: "跳转首页失败：" + ((err && err.errMsg) || "unknown") });
        this._pushEvent("page.navigate.fail");
      }
    });
  },

  onHomeReady(e) {
    this._pushEvent("page.home-ready");
    console.log("[miniapp] home-ready", JSON.stringify(e && e.detail));
  },

  onFailed(e) {
    const detail = (e && e.detail) || {};
    this.setData({ errorMsg: "认证失败：" + JSON.stringify(detail) });
    this._pushEvent("page.failed");
  },

  _pushEvent(name) {
    const events = (this.data.events || []).concat([{ seq: (this.data.events || []).length + 1, name }]);
    this.setData({ events });
  }
});
