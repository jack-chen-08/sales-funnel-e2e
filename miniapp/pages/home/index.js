/**
 * 小程序首页（第 12 步）：首月资源推荐。
 *
 * 由入口页认证成功后 wx.navigateTo 进入，参数沿用入口页：
 *   /pages/home/index?member_id=<会员ID>&run_id=<本次冒烟 run_id>
 *
 * 页面自己发起 GET /api/miniapp/home 并把响应渲染成 resource-item 列表，
 * 因此 automator 在页面上数到的条目数就是真实渲染结果，而不是组件内部状态。
 */
Page({
  data: {
    baseUrl: "",
    memberId: "",
    runId: "",
    month: "",
    headline: "",
    items: [],
    applicationStatus: "",
    phase: "loading",
    lastHome: null,
    lastHomeMs: null,
    errorMsg: "",
    events: []
  },

  onLoad(query) {
    const app = getApp();
    const base = (app && app.globalData && app.globalData.baseUrl) || "http://127.0.0.1:5600";
    this.setData({
      baseUrl: base,
      memberId: (query && query.member_id) || "",
      runId: (query && query.run_id) || (app && app.globalData && app.globalData.runId) || ""
    });
    this._pushEvent("page.home.load");
    this._load();
  },

  _load() {
    if (!this.data.memberId) {
      this.setData({ phase: "error", errorMsg: "缺少会员标识（member_id）" });
      this._pushEvent("page.home.fail");
      return;
    }
    const url =
      this.data.baseUrl.replace(/\/+$/, "") +
      "/api/miniapp/home?member_id=" + encodeURIComponent(this.data.memberId);
    const header = { "content-type": "application/json" };
    if (this.data.runId) {
      header["x-run-id"] = this.data.runId;
    }
    const startedAt = Date.now();
    wx.request({
      url,
      method: "GET",
      header,
      success: (res) => {
        const ms = Date.now() - startedAt;
        const body = res.data || {};
        if (res.statusCode === 200 && Array.isArray(body.items)) {
          this.setData({
            phase: "home",
            month: body.month || "",
            headline: body.headline || "",
            items: body.items,
            applicationStatus: body.application_status || "",
            lastHome: body,
            lastHomeMs: ms,
            errorMsg: ""
          });
          this._pushEvent("page.home.ok");
          console.log("[miniapp] home-rendered", JSON.stringify({ month: body.month, count: body.items.length }));
        } else {
          const detail = (body.detail && body.detail.code) || body.detail || "unknown";
          this.setData({ phase: "error", errorMsg: "首页加载失败：" + res.statusCode + " " + detail });
          this._pushEvent("page.home.fail");
        }
      },
      fail: (err) => {
        this.setData({ phase: "error", errorMsg: "首页加载失败：" + ((err && err.errMsg) || "request:fail") });
        this._pushEvent("page.home.fail");
      }
    });
  },

  _pushEvent(name) {
    const events = (this.data.events || []).concat([{ seq: (this.data.events || []).length + 1, name }]);
    this.setData({ events });
  }
});
