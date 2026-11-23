# 招商全链路冒烟报告 · smk-reject-20261124-033728-deb2

- 结论：**失败**
- 模式：skip-miniprogram（小程序步骤跳过）
- 平台地址：http://127.0.0.1:5601
- 开始：2026-11-23T19:37:28.292+00:00　结束：2026-11-23T19:37:32.052+00:00
- 总耗时：**3.76s**（阈值 600s）
- 通过 / 跳过 / 失败：7 / 0 / 1

> 失败步骤：**8. 电子签**　原因：`AssertionError: 电子签未完成两方签署：签约方拒签：签约方在签署页点击拒签（电子签桩模拟）`

| # | 步骤 | 执行方 | 方式 | 状态 | 耗时 | 关键断言 |
|---|------|--------|------|------|------|----------|
| 1 | 官网提交申请 | 官网访客 | ui | 通过 | 0.83s | 官网提交成功，申请单状态=submitted，返回 UUID 单号 |
| 2 | 线索按规则分配 | 销售中台 | api | 通过 | 0.01s | 线索分配命中规则 region=east->ADV-101，状态 assigned |
| 3 | 顾问首次联系 | 招商顾问 | ui | 通过 | 0.72s | 工作台点击后线索状态=contacted，页面回显联系记录 ID |
| 4 | 推进到预约参观 | 招商顾问 | api | 通过 | 0.01s | 预约参观创建成功，生成 6 位访客码，状态=visit_booked |
| 5 | 前台核销访客码 | 前台 | ui | 通过 | 0.74s | 访客码在 A 座前台核销成功，状态=visited |
| 6 | 纪要确认 | 招商顾问 | api | 通过 | 0.01s | 参观纪要确认落库，状态=minutes_confirmed |
| 7 | 9.5 折以内报价 | 招商顾问 | api | 通过 | 0.02s | 成交价为挂牌价 95.0%（9.5 折以内），成交价 1767000 分，状态=quoted |
| 8 | 电子签 | 签约双方 | ui | 失败 | 0.81s |  |

## 已创建数据 ID

```json
{
  "rooms": "3bb21890-5b2e-43be-8dd7-da7c7ca04d44,6e004a84-80f6-46a3-af78-1726280a1494",
  "room_primary": "3bb21890-5b2e-43be-8dd7-da7c7ca04d44",
  "room_secondary": "6e004a84-80f6-46a3-af78-1726280a1494",
  "application_id": "46a6ed0d-e2e6-4c9f-a9b2-ba1aa9575bb7",
  "lead_id": "5f80fb8e-9193-4337-968f-ec2dcc99b210",
  "advisor_id": "ADV-101",
  "contact_id": "f0e86764-e62c-4b0a-bac6-c1fe25cd7bac",
  "visit_id": "2bbf2272-a47a-468e-90aa-0637042ba3fa",
  "visit_code": "690568",
  "minutes_id": "97215061-1744-4176-9285-2823f8f7e26d",
  "quote_id": "79995f91-a6f4-45ba-a6d7-1c7d061be3a9",
  "envelope_id": "dc28cf17-e1b7-4132-bde5-f0bf73fb8a4c"
}
```

## run_id 清理校验

- 清理时间：2026-11-23T19:37:32.108+00:00
- 删除行数合计：17
- 剩余行数合计：**0**

| 表 | 删除 | 剩余 |
|----|------|------|
| resource_recommendations | 0 | 0 |
| members | 0 | 0 |
| handovers | 0 | 0 |
| rooms | 2 | 0 |
| esign_envelopes | 1 | 0 |
| quotes | 1 | 0 |
| visit_minutes | 1 | 0 |
| visits | 1 | 0 |
| contacts | 1 | 0 |
| leads | 1 | 0 |
| applications | 1 | 0 |
| audit_events | 8 | 0 |

## 证据文件

- artifacts_dir: `reports/artifacts/smk-reject-20261124-033728-deb2`
- report_json: `reports/run_smk-reject-20261124-033728-deb2.json`
- report_md: `reports/run_smk-reject-20261124-033728-deb2.md`
