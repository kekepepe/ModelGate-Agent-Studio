# Multi-Agent Benchmark 协议与待执行记录

日期：2026-07-18  
状态：协议、指标、成本计算与可执行 runner 已实现；真实 Provider 15 次运行待执行。

## 固定变量

准备 15 份来自同一 Git SHA 的独立 Workspace，分别供三种模式各 5 次使用。每次运行固定：Provider、模型名、知识库快照、初始文件 checksum、最大 Token、超时、重试策略和验证命令。关闭跨运行缓存，保留 Provider request id。

模式：

1. `single_agent`
2. `sequential_multi_agent`
3. `parallel_multi_agent`

Planner 必须生成目标模式；模式不符的运行作废并重跑，不能事后把估算指标当成 A/B 数据。产品的 `multi_agent_metrics` 只提供单次运行的协调成本说明，不替代本协议。

## 每次记录

| 字段 | 口径 |
|---|---|
| Success | Goal 通过 Completion Gate |
| Verification Pass | 所有必需 VerificationResult 通过 |
| Duration | Goal start 到终态的墙钟时间 |
| Token / Cost | Provider 实际 usage 汇总 |
| Replan / Handoff | 持久化事件计数 |
| Conflict | Worktree merge conflict 计数 |
| Human Intervention | Approval、ask_user、手工冲突处理次数 |
| Final Diff Quality | 统一测试结果 + 盲审缺陷数 |

输出每种模式的 Success Rate、Verification Pass Rate、Duration P50/P95、Token、Cost 与所有计数分布。原始 Goal ID、ExecutionLog、ToolCallRecord、Artifact checksum 和最终 Git SHA 必须随报告保存。

## 可执行门禁

后端已在 live 模式启动后执行：

```bash
export MODEL_PRICING_JSON='{
  "provider-planner-model":{"input_per_million":2.0,"output_per_million":8.0},
  "provider-worker-model":{"input_per_million":2.0,"output_per_million":8.0},
  "provider-verifier-model":{"input_per_million":2.0,"output_per_million":8.0}
}'
python backend/scripts/multi_agent_benchmark.py \
  --base-url http://127.0.0.1:8000/api/v1 \
  --runs-dir /tmp/modelgate-live \
  --output docs/review/live-multi-agent-benchmark.json \
  --runs-per-mode 5
```

runner 为每次运行创建独立 Git fixture，检查 Planner 模式、真实 request id、Completion Gate、`pytest`、`git diff --check`、目标文件内容、Worktree 冲突及事件证据。任何模式少于 5 次、任一次失败、未验证、质量门禁失败、缺少模型定价或缺少 token usage，报告均为失败。Cost 只使用持久化的逐模型 input/output token 与显式 USD/M token 费率计算，不猜测价格。

## 推荐门槛

仅当 Multi-Agent 成功率不下降、净时间收益大于零、协调 Token 在预算内且冲突风险可控时推荐。否则产品应选择 single 或 sequential，不为展示强制并行。

## 当前阻塞

本环境没有 `PROVIDER_API_KEY`、角色模型名和逐模型定价，因此没有执行真实 15 次 A/B。该项在 RC 报告中保持未通过，不使用 Mock、空 Cost 或单次时长估算填充结果。
