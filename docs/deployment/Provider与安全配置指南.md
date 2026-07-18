# Provider 与安全配置指南

## Provider

生产运行必须由后端进程或 Secret Manager 注入密钥，数据库和前端均不接受明文 API Key。

```env
MODEL_GATE_EXECUTION_MODE=live
PROVIDER_API_BASE=https://api.openai.com/v1
PROVIDER_API_KEY=
PLANNER_MODEL_NAME=
WORKER_MODEL_NAME=
VERIFIER_MODEL_NAME=
EMBEDDING_MODEL_NAME=
PROVIDER_TIMEOUT_SECONDS=60
```

`OPENAI_API_KEY` 与 `OPENAI_BASE_URL` 仅作为兼容别名。角色模型环境变量覆盖数据库中的展示模型标识；发往 Provider 的 `ModelRequest.model` 必须是远端真实模型名。

上线前依次验证健康检查、direct、single-agent、Coder→Verifier、Research→Coder→Verifier、parallel 和 Replan/Handoff。日志中应有 provider、model、request id、token 与延迟，但不能出现密钥。

### 六场景真实验收

后端必须已用上述 live 配置启动，且 `WORKSPACE_ROOT` 包含验收运行目录：

```bash
python backend/scripts/live_provider_acceptance.py \
  --base-url http://127.0.0.1:8000/api/v1 \
  --runs-dir /tmp/modelgate-live \
  --output docs/review/live-provider-acceptance.json
```

脚本执行六个隔离 Git Workspace，拒绝 Rule Fallback，并检查真实 request id、Planner mode、角色链、工具调用、Artifact、Verification、Worktree、Replan、Handoff 和最终 Goal 状态。任一场景失败时进程非零退出。脚本不读取或打印 Provider key。

### 真实 Embedding 与 Benchmark

```bash
python backend/scripts/rag_eval.py --embedding-backend real \
  --output docs/review/live-embedding-rag.json --enforce-thresholds

export MODEL_PRICING_JSON='{
  "实际远端模型名":{"input_per_million":2.0,"output_per_million":8.0}
}'
python backend/scripts/multi_agent_benchmark.py \
  --base-url http://127.0.0.1:8000/api/v1 \
  --runs-dir /tmp/modelgate-live \
  --output docs/review/live-multi-agent-benchmark.json \
  --runs-per-mode 5
```

定价对象必须覆盖 Planner、Worker、Verifier/Supervisor 实际使用的每个远端模型名。缺少定价、token usage 或任一次质量证据都会使 Benchmark 失败，不能以 `null` Cost 进入 RC。

GitHub 的 `Nightly CI` 会自动执行慢测、安全测试、完整浏览器矩阵、六场景 Provider 和真实 Embedding；付费的 15 次 Benchmark 只在手动触发并选择 `run_benchmark` 时执行。

## 安全基线

```env
DEBUG=false
MAX_REQUEST_BODY_BYTES=5242880
WORKSPACE_ROOT=/app/workspace
SANDBOX_BACKEND=local
```

- API 使用同域反向代理和 HTTPS；生产 CORS 只允许正式域名。
- Agent 文件访问必须位于 Goal Workspace 且通过 realpath/commonpath 与敏感路径拒绝规则。
- Shell 只启用审核后的命令类别；network、destructive、privileged、arbitrary-code 默认拒绝。
- 不把 `.env`、SSH/AWS/Kubernetes 凭据目录、Docker socket 或宿主根目录挂给 Runtime。
- Context、日志、Handoff、ToolCall 和异常统一递归脱敏；检索内容始终视为不可信数据。
- 依赖例外及其补偿控制见 `docs/security/dependency-vex.md`。

## 密钥轮换

1. 在 Secret Manager 创建新版本。
2. 滚动重启后端并运行 Provider health check。
3. 撤销旧密钥。
4. 搜索发布日志确认没有明文密钥。
5. 若怀疑泄漏，立即撤销密钥并按事件响应流程处理，不能只做日志脱敏。
