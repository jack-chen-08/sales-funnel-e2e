# 招商全链路冒烟报告 · smk-5x-r5-20261124-142852-9edd

- 结论：**通过**
- 模式：full（小程序步骤执行）
- 平台地址：http://127.0.0.1:5600
- 开始：2026-11-24T06:28:52.335+00:00　结束：2026-11-24T06:28:56.975+00:00
- 总耗时：**4.64s**（阈值 600s）
- 通过 / 跳过 / 失败：12 / 0 / 0

| # | 步骤 | 执行方 | 方式 | 状态 | 耗时 | 关键断言 |
|---|------|--------|------|------|------|----------|
| 1 | 官网提交申请 | 官网访客 | ui | 通过 | 0.84s | 官网提交成功，申请单状态=submitted，返回 UUID 单号 |
| 2 | 线索按规则分配 | 销售中台 | api | 通过 | 0.01s | 线索分配命中规则 region=east->ADV-101，状态 assigned |
| 3 | 顾问首次联系 | 招商顾问 | ui | 通过 | 0.72s | 工作台点击后线索状态=contacted，页面回显联系记录 ID |
| 4 | 推进到预约参观 | 招商顾问 | api | 通过 | 0.01s | 预约参观创建成功，生成 6 位访客码，状态=visit_booked |
| 5 | 前台核销访客码 | 前台 | ui | 通过 | 0.74s | 访客码在 A 座前台核销成功，状态=visited |
| 6 | 纪要确认 | 招商顾问 | api | 通过 | 0.01s | 参观纪要确认落库，状态=minutes_confirmed |
| 7 | 9.5 折以内报价 | 招商顾问 | api | 通过 | 0.01s | 成交价为挂牌价 95.0%（9.5 折以内），成交价 1767000 分，状态=quoted |
| 8 | 电子签 | 签约双方 | ui | 通过 | 0.73s | 签约台完成两方签署（出租方+承租方），信封状态=signed，主状态=signed |
| 9 | 房态变为已租 | 运营中台 | api | 通过 | 0.01s | 房源 12F-1801 房态=rented，主状态=rented |
| 10 | 会员经理领取交接 | 会员经理 | api | 通过 | 0.01s | 会员经理 MM-021 领取交接，会员档案创建，状态=handed_over |
| 11 | 签约企业联系人在小程序完成认证 | 企业联系人 | miniapp | 通过 | 0.98s | 小程序内提交验证码完成企业联系人认证：POST /api/miniapp/certify → 200（29ms），页面 pages/entry/index 上真实输入并点击提交，phase=idle→certified，触发 certified 事件，状态=certified |
| 12 | 小程序首页看到首月资源推荐 | 企业联系人 | miniapp | 通过 | 0.00s | 小程序首页渲染 2026-11 首月资源包 3 项（页面上数到 3 个节点，与数据一致），GET /api/miniapp/home → 200（13ms），链路状态=activated |

## 已创建数据 ID

```json
{
  "rooms": "a0947f66-1ed6-4827-be67-34d1a669980c,a8c6dc7a-5e62-4fb2-997d-dd2cad804101",
  "room_primary": "a0947f66-1ed6-4827-be67-34d1a669980c",
  "room_secondary": "a8c6dc7a-5e62-4fb2-997d-dd2cad804101",
  "application_id": "ae4a7090-5368-4d15-8c67-905ab2210793",
  "lead_id": "a31b171d-600f-4479-935e-f105ea335e1a",
  "advisor_id": "ADV-101",
  "contact_id": "67b8b89a-ec14-4662-897e-fc51ff148fc4",
  "visit_id": "690f87f4-86d5-47e7-b8cc-555ff9f2c405",
  "visit_code": "691436",
  "minutes_id": "3c8f86bc-9276-4897-bb3f-c40b39deef25",
  "quote_id": "f19543a7-ff1b-4e45-b3c9-7639a686a47f",
  "envelope_id": "0c7f04c0-9d10-4226-97b8-9ec40da0773c",
  "handover_id": "3297c7c5-d5ee-4030-b671-da7a7d34b3f7",
  "member_id": "8827bd86-7b4f-4b58-bb4c-48f6b4da87e4",
  "recommendation_id": "a1f403a7-4fbd-459f-b042-da23aa72ace4"
}
```

## run_id 清理校验

- 清理时间：2026-11-24T06:28:57.012+00:00
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

- artifacts_dir: `reports/artifacts/smk-5x-r5-20261124-142852-9edd`
- report_json: `reports/run_smk-5x-r5-20261124-142852-9edd.json`
- report_md: `reports/run_smk-5x-r5-20261124-142852-9edd.md`
