/**
 * 小程序入口。
 *
 * baseUrl 为平台服务地址：真机联调时替换为实际网关地址；
 * 开发者工具本地联调可用 http://127.0.0.1:5600（需在工具中关闭「域名校验」）。
 */
App({
  globalData: {
    baseUrl: "http://127.0.0.1:5600",
    memberId: ""
  },

  onLaunch(options) {
    // 扫码进入时 memberId 由页面参数携带，这里只做兜底保存
    const query = (options && options.query) || {};
    if (query.member_id) {
      this.globalData.memberId = query.member_id;
    }
  }
});
