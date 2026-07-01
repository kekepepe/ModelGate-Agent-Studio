# Phase 2: 真实 Provider 接入 — 实施总结

> 完成日期：2026-07-01
> 对应文档：`docs/roadmap/modelgate-next-step-full-plan.md` 阶段 2

---

## 1. 完成内容

### 新增 Provider 包结构

```
backend/src/services/providers/
├── __init__.py                       # 公共导出
├── base.py                           # ModelProvider Protocol + ModelRequest/ModelResponse
├── mock_provider.py                  # Mock Provider（测试/开发专用）
├── openai_compatible_provider.py     # OpenAI-compatible Provider（真实 API）
└── provider_factory.py               # Provider 工厂（按类型创建，环境变量配置）
```

### 新增文件

| 文件 | 说明 |
|------|------|
| `backend/src/services/providers/__init__.py` | 包初始化，导出公共接口 |
| `backend/src/services/providers/base.py` | `ModelProvider` Protocol + `ModelRequest` + `ModelResponse` dataclass |
| `backend/src/services/providers/provider_factory.py` | `get_provider()` / `set_provider()` / `create_provider(type)` |
| `backend/src/services/providers/openai_compatible_provider.py` | 真实 HTTP API 调用，支持 OpenAI / Anthropic proxy / Ollama / vLLM |

### 修改文件

| 文件 | 变更 |
|------|------|
| `backend/src/services/providers/mock_provider.py` | 重写，实现 `ModelProvider` Protocol，async `generate()` |
| `backend/src/services/runtime_service.py` | 改用 `get_provider()` + `ModelRequest`，用 `asyncio.new_event_loop()` 调用 async provider |
| `backend/tests/test_mock_provider.py` | 适配新接口（async + ModelRequest） |

---

## 2. Provider 接口

### ModelRequest

```python
@dataclass
class ModelRequest:
    provider: str                 # e.g. "openai", "anthropic"
    model: str                    # e.g. "gpt-4-turbo"
    messages: List[Dict]          # [{"role":"system","content":...}, {"role":"user","content":...}]
    temperature: float = 0.7
    max_tokens: int = 4096
    tools: Optional[List] = None
    metadata: Dict = {}
```

### ModelResponse

```python
@dataclass
class ModelResponse:
    content: str                  # 模型输出文本
    input_tokens: int
    output_tokens: int
    total_tokens: int
    latency_ms: int
    raw_response: Optional[Dict]  # 原始 API 响应
    finish_reason: str = "stop"
```

### Provider 切换方式

```bash
# 使用 Mock Provider（默认）
export MODEL_PROVIDER=mock

# 使用真实 OpenAI Provider
export OPENAI_BASE_URL=https://api.openai.com/v1
export OPENAI_API_KEY=sk-xxx
export MODEL_PROVIDER=openai
```

或代码中：
```python
from src.services.providers import set_provider, create_provider
set_provider(create_provider("openai"))
```

---

## 3. 错误处理

OpenAICompatibleProvider 处理以下错误：

| 错误 | 处理 |
|------|------|
| API key 缺失 | 初始化时抛出 `OpenAICompatibleError` |
| 429 Rate Limit | 抛出异常，建议重试或切换模型 |
| 5xx Provider Error | 抛出异常，带状态码 |
| 请求超时 | 抛出 `OpenAICompatibleError`，可配置 timeout |
| 连接失败 | 抛出 `OpenAICompatibleError`（base_url 错误） |
| 非 200 响应 | 抛出异常，带状态码和响应内容 |

Runtime 在 `_execute_single_task()` 中捕获所有 Provider 异常，转为 task failure。

---

## 4. 测试结果

```text
Backend: 164 passed
Frontend: 145 passed
Total: 309 passed
Build: 通过
Status: 零回归
```

## 5. 当前限制

- Mock Provider 仍为默认（`MODEL_PROVIDER` 环境变量默认为 `mock`）
- OpenAI-compatible Provider 需要用户设置 `OPENAI_API_KEY` 才能使用
- 未测试真实 API 调用（需要网络和 API key）
- Async 调用使用 `asyncio.new_event_loop()` 在同步上下文中运行，未来可考虑全面异步化

## 6. 下一步

阶段 3: Supervisor 审查链路。Runtime 执行完成后进入 Supervisor Review，判断 passed/needs_revision/failed。
