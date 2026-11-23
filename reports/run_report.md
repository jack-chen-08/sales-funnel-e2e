# 链式用例运行报告

- 生成时间：2026-11-23
- 被测对象：本仓 `app/` 参考桩（对外接口约定与真实平台一致，替换 base_url 即可对接）
- 用例：#1–#12 招商闭环，单一 run_id 串联
- 环境：Linux-6.6.87.2-microsoft-standard-WSL2-x86_64-with-glibc2.43 · Python 3.12.13 · Playwright chromium · FastAPI(uvicorn)

## AC1 连续 5 次运行

| 次序 | run_id | 结果 | 通过步数 | 链耗时 (s) | 实际耗时 (s) | 残留数据 |
|------|--------|------|----------|------------|--------------|----------|
| 1 | `run-20261124024522-a734a8` | ✅ 通过 | 12/12 | 0.97 | 1.00 | 0 |
| 2 | `run-20261124024523-d0d7d3` | ✅ 通过 | 12/12 | 0.96 | 1.00 | 0 |
| 3 | `run-20261124024524-f3b846` | ✅ 通过 | 12/12 | 0.99 | 1.00 | 0 |
| 4 | `run-20261124024525-0f1ef2` | ✅ 通过 | 12/12 | 0.96 | 1.00 | 0 |
| 5 | `run-20261124024526-2ff563` | ✅ 通过 | 12/12 | 0.96 | 1.00 | 0 |

- 5 次全部通过：**True**
- 平均链耗时：**0.97 s**（红线 600 s，余量 599 s）
- 最大单次：0.99 s
- 5 次合计残留数据：**0** 条

复现命令：

```bash
.venv/bin/python scripts/run_5x.py          # 输出上表并落盘 reports/_runtime/chain_5x_summary.json
```

## AC2 电子签拒签报告

| 项 | 实测值 |
|----|--------|
| failed_step | **电子签** |
| failed_step_index | 8 |
| 错误码 | 命中 `ESIGN_REJECTED`：True |
| trace 条数 | 2（含 422 响应与异常栈） |
| 失败即停 | 仅执行 8 步 |
| 明细 | 见 `reports/failure_report_esign.md` |

## AC3 run_id 数据清理

- 单次运行收尾会调用 `POST /api/_test/purge?run_id=…`，并用**独立于 runner 的第二个 HTTP 客户端**复查 `GET /api/_test/count`。
- 实测：5 次运行合计残留 **0** 条；单次校验见 `test_ac3_run_data_purged_after_run`。

## AC4 跳过小程序后其余 10 步

`SKIP_MINI=1`（或 `ChainRunner(skip_mini=True)`）实测：

| # | 步骤 | 结果 |
|---|------|------|
| 1 | 官网提交申请 | passed |
| 2 | 线索按规则分配 | passed |
| 3 | 顾问首次联系 | passed |
| 4 | 推进到预约参观 | passed |
| 5 | 前台核销访客码 | passed |
| 6 | 纪要确认 | passed |
| 7 | 9.5折以内报价 | passed |
| 8 | 电子签 | passed |
| 9 | 房态变为已租 | passed |
| 10 | 会员经理领取交接 | passed |
| 11 | 小程序认证 | skipped |
| 12 | 小程序首页资源推荐 | skipped |

- 跳过 2 步、执行 10 步，整链结果：**通过**

## 复现

```bash
.venv/bin/pytest -q                                       # 全部用例
.venv/bin/python scripts/run_5x.py                        # AC1 证据（5 连跑）
SKIP_MINI=1 .venv/bin/python scripts/run_5x.py --runs 1   # AC4 证据（可选）
.venv/bin/python scripts/make_reports.py                  # 从 _runtime 生成上述样例
```
