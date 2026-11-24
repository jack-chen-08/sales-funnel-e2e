/**
 * 会员入会两步交互组件（第 11 步认证 / 第 12 步首月资源）。
 *
 * 组件不依赖页面上下文，只通过 properties 接收平台地址与会员标识，
 * 因此既可挂在 pages/entry/index 上以真机运行，也可被自动化宿主单独加载。
 */
const PHASE_LABEL = {
  idle: "待认证",
  certifying: "认证中",
  certified: "已认证",
  loading_home: "加载首页",
  home: "已进入首页",
  error: "认证失败"
};

Component({
  properties: {
    baseUrl: { type: String, value: "http://127.0.0.1:5600" },
    memberId: { type: String, value: "" },
    runId: { type: String, value: "" },
    phone: { type: String, value: "" },
    company: { type: String, value: "" },
    contact: { type: String, value: "" },
    brand: { type: String, value: "园区会员服务" }
  },

  data: {
    phase: "idle",
    phaseLabel: PHASE_LABEL.idle,
    verifyCode: "",
    errorMsg: "",
    certifyStatus: "",
    channel: "",
    openidStub: "",
    month: "",
    headline: "",
    items: [],
    events: []
  },

  methods: {
    /** 输入验证码（真机由键盘触发，自动化宿主可直接 setData 或派发 input） */
    onCodeInput(e) {
      const value = (e && e.detail && e.detail.value) || "";
      this.setData({ verifyCode: value, errorMsg: "" });
    },

    /** 第 11 步：提交企业联系人认证 */
    onCertify() {
      const code = String(this.data.verifyCode || "").trim();
      const startedAt = Date.now();
      this._pushEvent("tap.certify");
      if (!/^\d{6}$/.test(code)) {
        this.setData({ phase: "error", phaseLabel: PHASE_LABEL.error, errorMsg: "请输入 6 位数字验证码" });
        this.triggerEvent("failed", { step: "certify", reason: "verify_code_format" });
        return Promise.resolve({ ok: false, reason: "verify_code_format" });
      }
      if (!this.data.memberId) {
        this.setData({ phase: "error", phaseLabel: PHASE_LABEL.error, errorMsg: "缺少会员标识（member_id）" });
        this.triggerEvent("failed", { step: "certify", reason: "missing_member_id" });
        return Promise.resolve({ ok: false, reason: "missing_member_id" });
      }

      this.setData({ phase: "certifying", phaseLabel: PHASE_LABEL.certifying, errorMsg: "" });
      return this._request({
        method: "POST",
        path: "/api/miniapp/certify",
        data: { member_id: this.data.memberId, verify_code: code }
      }).then((res) => {
        const body = res.data || {};
        if (res.statusCode === 200 && body.certify_status === "certified") {
          this.setData({
            phase: "certified",
            phaseLabel: PHASE_LABEL.certified,
            certifyStatus: body.certify_status,
            channel: body.channel || "",
            openidStub: body.openid_stub || "",
            errorMsg: ""
          });
          this._pushEvent("certify.ok");
          this.triggerEvent("certified", Object.assign({}, body, { duration_ms: Date.now() - startedAt }));
          return { ok: true, body };
        }
        const detail = (body.detail && body.detail.code) || body.detail || "unknown";
        this.setData({
          phase: "error",
          phaseLabel: PHASE_LABEL.error,
          errorMsg: `认证失败：${res.statusCode} ${detail}`
        });
        this._pushEvent("certify.fail");
        this.triggerEvent("failed", { step: "certify", statusCode: res.statusCode, detail });
        return { ok: false, statusCode: res.statusCode, detail };
      });
    },

    /** 第 12 步：进入首页领取首月资源推荐 */
    onEnterHome() {
      this._pushEvent("tap.enter-home");
      this.setData({ phase: "loading_home", phaseLabel: PHASE_LABEL.loading_home, errorMsg: "" });
      return this._request({
        method: "GET",
        path: "/api/miniapp/home",
        data: { member_id: this.data.memberId }
      }).then((res) => {
        const body = res.data || {};
        if (res.statusCode === 200 && Array.isArray(body.items)) {
          this.setData({
            phase: "home",
            phaseLabel: PHASE_LABEL.home,
            month: body.month || "",
            headline: body.headline || "",
            items: body.items,
            errorMsg: ""
          });
          this._pushEvent("home.ok");
          this.triggerEvent("home-ready", body);
          return { ok: true, body };
        }
        const detail = (body.detail && body.detail.code) || body.detail || "unknown";
        this.setData({
          phase: "error",
          phaseLabel: PHASE_LABEL.error,
          errorMsg: `首页加载失败：${res.statusCode} ${detail}`
        });
        this._pushEvent("home.fail");
        this.triggerEvent("failed", { step: "home", statusCode: res.statusCode, detail });
        return { ok: false, statusCode: res.statusCode, detail };
      });
    },

    /** wx.request 的 Promise 包装：真机走微信网络，自动化宿主可替换 wx.request 实现 */
    _request({ method, path, data }) {
      const url = this.data.baseUrl.replace(/\/+$/, "") + path;
      const query = method === "GET" && data
        ? "?" + Object.keys(data)
            .filter((k) => data[k] !== undefined && data[k] !== "")
            .map((k) => encodeURIComponent(k) + "=" + encodeURIComponent(data[k]))
            .join("&")
        : "";
      const headers = { "content-type": "application/json" };
      if (this.data.runId) {
        headers["x-run-id"] = this.data.runId;
      }
      return new Promise((resolve) => {
        wx.request({
          url: url + query,
          method,
          data: method === "GET" ? undefined : data,
          header: headers,
          success: (res) => resolve({ statusCode: res.statusCode, data: res.data }),
          fail: (err) => resolve({
            statusCode: 0,
            data: {},
            errMsg: (err && err.errMsg) || "request:fail"
          })
        });
      });
    },

    _pushEvent(name) {
      const events = (this.data.events || []).concat([{ seq: (this.data.events || []).length + 1, name }]);
      this.setData({ events });
    }
  }
});
