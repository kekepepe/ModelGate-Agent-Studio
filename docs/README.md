# ModelGate Agent Studio · 文档入口

> 🚧 **2026-09-06 重设计进行中**  
> 旧文档已全部归档到 [`_archive_2026/`](./_archive_2026/)。**所有架构 / 产品 / 开发决策以唯一文档为准**：

# 👉 [`design/2026-09-06-platform-redesign.md`](./design/2026-09-06-platform-redesign.md)

## 目录

| 路径 | 说明 |
|---|---|
| `design/2026-09-06-platform-redesign.md` | **唯一权威设计文档**（架构 / 前后端 / Agent / 数据 / 阶段） |
| `../V1.0.1-V1.1-plan.md` | 当前阶段执行计划（修复 + CI + Handoff 完整业务流），进度 checkbox 在此维护 |
| `_archive_2026/` | 重设计前的所有旧文档（V0 / MVP / P0-P7 时期），仅供考古 |

## 使用规则

- ✅ 任何架构 / 接口 / 状态机变更 → 先改 `design/2026-09-06-platform-redesign.md`
- ❌ 不要在别处另开新的规划文档（除非有充分理由并在本 README 留入口）
- ❌ 不要去翻 `_archive_2026/` 找"当前事实"（历史已定，新设计为准）

## 实施进度

按 V1.0 → V1.4 阶段推进，详见设计文档第 8 章。当前进行中：

- ✅ V1.0 核心闭环（29 个提交，`e3fc444` docker compose + `36094e0` release notes 收尾）
- ✅ V1.0 末位补活：P0-P3 shadcn 化 + SSE + tasks 列表接口
- ⏳ V1.0.1 补短板（CI / 文档修正 / 测试修复）→ 见 `../V1.0.1-V1.1-plan.md` Phase F/C
- ⏳ V1.1 Handoff + Quota → 见 `../V1.0.1-V1.1-plan.md` Phase B

> 最后更新：2026-09-15
