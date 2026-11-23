# 招商全链路冒烟报告 · smk-5x-r1-20261124-033650-4ec2

- 结论：**通过**
- 模式：full（小程序步骤执行）
- 平台地址：http://127.0.0.1:5600
- 开始：2026-11-23T19:36:50.816+00:00　结束：2026-11-23T19:36:55.380+00:00
- 总耗时：**4.56s**（阈值 600s）
- 通过 / 跳过 / 失败：12 / 0 / 0

| # | 步骤 | 执行方 | 方式 | 状态 | 耗时 | 关键断言 |
|---|------|--------|------|------|------|----------|
| 1 | 官网提交申请 | 官网访客 | ui | 通过 | 0.86s | 官网提交成功，申请单状态=submitted，返回 UUID 单号 |
| 2 | 线索按规则分配 | 销售中台 | api | 通过 | 0.01s | 线索分配命中规则 region=east->ADV-101，状态 assigned |
| 3 | 顾问首次联系 | 招商顾问 | ui | 通过 | 0.73s | 工作台点击后线索状态=contacted，页面回显联系记录 ID |
| 4 | 推进到预约参观 | 招商顾问 | api | 通过 | 0.01s | 预约参观创建成功，生成 6 位访客码，状态=visit_booked |
| 5 | 前台核销访客码 | 前台 | ui | 通过 | 0.74s | 访客码在 A 座前台核销成功，状态=visited |
| 6 | 纪要确认 | 招商顾问 | api | 通过 | 0.01s | 参观纪要确认落库，状态=minutes_confirmed |
| 7 | 9.5 折以内报价 | 招商顾问 | api | 通过 | 0.01s | 成交价为挂牌价 95.0%（9.5 折以内），成交价 1767000 分，状态=quoted |
| 8 | 电子签 | 签约双方 | ui | 通过 | 0.69s | 签约台完成两方签署（出租方+承租方），信封状态=signed，主状态=signed |
| 9 | 房态变为已租 | 运营中台 | api | 通过 | 0.01s | 房源 12F-1801 房态=rented，主状态=rented |
| 10 | 会员经理领取交接 | 会员经理 | api | 通过 | 0.01s | 会员经理 MM-021 领取交接，会员档案创建，状态=handed_over |
| 11 | 签约企业联系人在小程序完成认证 | 企业联系人 | miniapp | 通过 | 0.91s | 小程序内提交验证码完成企业联系人认证：POST /api/miniapp/certify → 200（20ms），组件 phase=idle→certified，触发 certified 事件，状态=certified |
| 12 | 小程序首页看到首月资源推荐 | 企业联系人 | miniapp | 通过 | 0.00s | 小程序首页渲染 2026-11 首月资源包 3 项（渲染树条目数与数据一致），GET /api/miniapp/home → 200（12ms），链路状态=activated |

## 已创建数据 ID

```json
{
  "rooms": "ab648b1f-51f4-490e-a08c-0f0743c6d797,45337764-bd32-4d99-a8cf-095187e0bd21",
  "room_primary": "ab648b1f-51f4-490e-a08c-0f0743c6d797",
  "room_secondary": "45337764-bd32-4d99-a8cf-095187e0bd21",
  "application_id": "9ea75949-1d50-4c8f-bdc6-99a5439ad4ca",
  "lead_id": "dc41da85-93ed-460e-8ba5-3f119b270999",
  "advisor_id": "ADV-101",
  "contact_id": "50d4c277-68ac-4d96-9049-2500d9740892",
  "visit_id": "0d683cb7-3419-4934-bc01-cc7bbd0f120a",
  "visit_code": "875268",
  "minutes_id": "0e2d0c4f-5fe4-4016-8353-07803e9946e5",
  "quote_id": "8dfb3a29-74bf-456c-bd38-50c2160a9cd6",
  "envelope_id": "19f379fa-ccf5-4796-90d5-98748bbc80e9",
  "handover_id": "5efa3e4a-f160-494d-ab2b-0136388c50a0",
  "member_id": "f5488d22-49da-424f-b34e-d13da85d339d",
  "recommendation_id": "d882e997-9b44-43e5-af97-b9ea2bd1c17f"
}
```

## run_id 清理校验

- 清理时间：2026-11-23T19:36:55.417+00:00
- 删除行数合计：24
- 剩余行数合计：**0**

| 表 | 删除 | 剩余 |
|----|------|------|
| resource_recommendations | 1 | 0 |
| members | 1 | 0 |
| handovers | 1 | 0 |
| rooms | 2 | 0 |
| esign_envelopes | 1 | 0 |
| quotes | 1 | 0 |
| visit_minutes | 1 | 0 |
| visits | 1 | 0 |
| contacts | 1 | 0 |
| leads | 1 | 0 |
| applications | 1 | 0 |
| audit_events | 12 | 0 |

## 证据文件

- artifacts_dir: `reports/artifacts/smk-5x-r1-20261124-033650-4ec2`
- report_json: `reports/run_smk-5x-r1-20261124-033650-4ec2.json`
- report_md: `reports/run_smk-5x-r1-20261124-033650-4ec2.md`
