Page({
  data: {
    baseUrl: "",
    memberId: "",
    runId: "",
    phone: "",
    company: "",
    contact: ""
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

  onCertified(e) {
    console.log("[miniapp] certified", JSON.stringify(e.detail));
  },

  onHomeReady(e) {
    console.log("[miniapp] home-ready", JSON.stringify(e.detail));
  },

  onFailed(e) {
    console.warn("[miniapp] failed", JSON.stringify(e.detail));
  }
});
