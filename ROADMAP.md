# ROADMAP — V1.0 → V2.0

> 2026-09-15 重新规划（用户拍板）。取代 `docs/design/2026-09-06-platform-redesign.md` §8 的旧编号体系。
> 规划原则：**不为"架构看起来高级"提前引入依赖**（Redis/arq 只在 V1.4 引入）；**README 里每一个
> "已完成"都必须有自动证据**（e2e 脚本 / CI）；**先收口 SSOT 再动工**。每阶段立项时产出独立
> 计划文档（惯例见 docs/README.md）。

## 版本路线

| 版本 | 主题 | 状态 | 计划文档 |
|---|---|---|---|
| V1.0 | Core Agent Runtime（Goal → 拆解 → 执行 → Final Summary） | ✅ 完成 | CHANGELOG |
| V1.1 | Handoff 完整业务流 + Quota 可视化 | ✅ 完成 | `_archive_2026/V1.0.1-V1.1-plan.md` |
| V1.2 | Memory + RAG + Skill 沉淀 | ✅ 完成 | `_archive_2026/V1.2-Memory-RAG-Skill-plan.md` |
| **V1.2.1** | **Architecture Alignment + CI + Product Acceptance** | ✅ 完成 | [V1.2.1-plan.md](./V1.2.1-plan.md) |
| V1.3 | Real Multi-Provider + MCP | 📋 计划就绪（OpenAI-compatible + Anthropic native；MCP 首批 filesystem+GitHub） | [V1.3-plan.md](./V1.3-plan.md) |
| V1.4 | Parallel Multi-Agent Runtime（单机强化） | ✅ 完成 | [V1.4-plan.md](./V1.4-plan.md) |
| V1.5 | Evolution Quality Loop（知识主线重心） | ✅ 完成 | [V1.5-plan.md](./V1.5-plan.md) |
| V2.0 | Developer Agent Operating System | ⏳ 下一阶段（含 arq/Redis 按需、Router 学习、Station Test Run 等收口项） | — |

## 阶段总览（P0–P6 → 版本映射）

| Phase | 内容 | 版本 | 目标 |
|---|---|---|---|
| P0 | 架构与文档收口 | V1.2.1 | 重新建立真正 SSOT：设计文档对齐真实技术栈；三大悬而未决的栈决策落锤；HANDOVER 恢复为真正的交接文档 |
| P1 | CI + Product Acceptance | V1.2.1 | 给 V1.2 建质量基线：最小 GitHub Actions + e2e-product-acceptance.sh，让 README 的每项"已完成"有自动证据 |
| P2 | Real Multi-Provider | V1.3 | 真模型多 Provider 全链路：≥2 家真实 Provider 跨模型执行、故障→备份/交接、真实 token/latency/cost 记录 |
| P3 | MCP Runtime | V1.3 | 从本地 Tool Registry 升级为外部 Tool Platform（server 发现 / tools/list 同步 / 权限 / 审批 / 健康检查） |
| P4 | Parallel Runtime | V1.4 | 单机 ThreadPool 强化：恢复常态化（心跳+续租）、checkpoint 增量 resume、确定性 merge、WAL；**修订 2026-09-16：探索证明并行雏形已可用，arq/Redis 移至 V2.0 按需** |
| P5 | Evolution 2.0 | V1.5 | 从"能记忆"升级成"记忆真的改善下一次任务"：usefulness 闭环、retrieval hit→accepted→used、Skill versioning、失败技能降级 |
| P6 | Product Polish | V2.0 | 面向作品集/真实用户收口：Station Test Run、Model 诊断、Context Inspector、Run Export、Goal Template、Demo Dataset |

## 各版本边界（明确不做）

- **V1.2.1 不做任何新功能**——只收口文档与质量门禁。
- **V1.3 不做并行**——多 Provider 与 MCP 是"接得更宽"，不是"跑得更并发"。
- **V1.4 之前不引入 Redis/arq**——当前串行 + SQLite 够用。
- **Pixel Office 不再投入复杂动画**；多人协作 / Marketplace / 知识图谱 / Memory 自进化
  Agent Runtime 均不做（仅 Evolution 质量闭环）。
- 产品壳已存在的页面（Agents / Models / Tools 管理页）不作为独立阶段——随所在版本顺带收口。

## 与旧路线的差异

旧设计文档 §8 的 V1.3 = Agents 页面、V1.4 = 并行，被本次规划**取代**：Agents / Models / Tools
的管理壳已存在，单独成阶段价值低；真正稀缺的是「真实多模型证据」「外部工具生态」「并发执行」
「Evolution 的效果证明」。设计文档 §8 的编号改写是 V1.2.1 P0 的任务。
