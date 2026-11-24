# 招商全链路冒烟报告 · smk-5x-r4-20261124-144138-5860

- 结论：**通过**
- 模式：full（小程序步骤执行）
- 平台地址：http://127.0.0.1:5600
- 开始：2026-11-24T06:41:38.494+00:00　结束：2026-11-24T06:42:03.364+00:00
- 总耗时：**24.87s**（阈值 600s）
- 通过 / 跳过 / 失败：12 / 0 / 0

| # | 步骤 | 执行方 | 方式 | 状态 | 耗时 | 关键断言 |
|---|------|--------|------|------|------|----------|
| 1 | 官网提交申请 | 官网访客 | ui | 通过 | 0.87s | 官网提交成功，申请单状态=submitted，返回 UUID 单号 |
| 2 | 线索按规则分配 | 销售中台 | api | 通过 | 0.04s | 线索分配命中规则 region=east->ADV-101，状态 assigned |
| 3 | 顾问首次联系 | 招商顾问 | ui | 通过 | 0.99s | 工作台点击后线索状态=contacted，页面回显联系记录 ID |
| 4 | 推进到预约参观 | 招商顾问 | api | 通过 | 0.02s | 预约参观创建成功，生成 6 位访客码，状态=visit_booked |
| 5 | 前台核销访客码 | 前台 | ui | 通过 | 1.30s | 访客码在 A 座前台核销成功，状态=visited |
| 6 | 纪要确认 | 招商顾问 | api | 通过 | 0.03s | 参观纪要确认落库，状态=minutes_confirmed |
| 7 | 9.5 折以内报价 | 招商顾问 | api | 通过 | 0.04s | 成交价为挂牌价 95.0%（9.5 折以内），成交价 1767000 分，状态=quoted |
| 8 | 电子签 | 签约双方 | ui | 通过 | 1.02s | 签约台完成两方签署（出租方+承租方），信封状态=signed，主状态=signed |
| 9 | 房态变为已租 | 运营中台 | api | 通过 | 0.03s | 房源 12F-1801 房态=rented，主状态=rented |
| 10 | 会员经理领取交接 | 会员经理 | api | 通过 | 0.02s | 会员经理 MM-021 领取交接，会员档案创建，状态=handed_over |
| 11 | 签约企业联系人在小程序完成认证 | 企业联系人 | miniapp | 通过 | 19.42s | 小程序内提交验证码完成企业联系人认证：POST /api/miniapp/certify → 200（22ms），页面 pages/entry/index 上真实输入并点击提交，phase=idle→certified，触发 certified 事件，状态=certified |
| 12 | 小程序首页看到首月资源推荐 | 企业联系人 | miniapp | 通过 | 0.00s | 小程序首页渲染 2026-11 首月资源包 3 项（页面上数到 3 个节点，与数据一致），GET /api/miniapp/home → 200（72ms），链路状态=activated |

## 已创建数据 ID

```json
{
  "rooms": "210e0715-a2ed-49f3-8711-b93190764b7f,e8bdc08f-b93d-419b-b694-68e92166825b",
  "room_primary": "210e0715-a2ed-49f3-8711-b93190764b7f",
  "room_secondary": "e8bdc08f-b93d-419b-b694-68e92166825b",
  "application_id": "d55b20b7-7865-4ce7-822a-2c547fc01da2",
  "lead_id": "b6c7aebb-03cf-4b19-b4a8-d5f6222830bb",
  "advisor_id": "ADV-101",
  "contact_id": "3d57cb2e-a30a-41f6-8bdb-a6b3aa459026",
  "visit_id": "f016bf33-8715-4162-823a-a50c35e168b0",
  "visit_code": "614875",
  "minutes_id": "059714d6-b7ff-4fe1-b3ec-23be4cb50886",
  "quote_id": "f0a69da2-66e0-4808-99fd-ca24366785fb",
  "envelope_id": "cccd7c55-5009-4265-9643-3a28bb57f2f1",
  "handover_id": "f9c8fa00-b1ad-47b0-98a3-a949872bdd4c",
  "member_id": "73469760-b8d7-41b6-98bb-c94d892c4d96",
  "recommendation_id": "aeb7229b-ec0e-42ab-9d04-e38d4bd709b6"
}
```

## run_id 清理校验

- 清理时间：2026-11-24T06:42:03.415+00:00
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

- artifacts_dir: `reports/artifacts/smk-5x-r4-20261124-144138-5860`
- report_json: `reports/run_smk-5x-r4-20261124-144138-5860.json`
- report_md: `reports/run_smk-5x-r4-20261124-144138-5860.md`
