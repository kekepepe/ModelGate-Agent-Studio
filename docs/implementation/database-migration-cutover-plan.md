# 数据库 Migration 切换计划

> 对应：[下一阶段产品与开发总方案](../roadmap/2026-07-14-下一阶段产品与开发总方案.md) Phase D。  
> 状态：设计完成，尚未切换生产启动行为。

## 结论

当前不应直接按文件顺序执行 `migrations/001` 至 `010`：其中存在历史 `ALTER TABLE`，在已由 SQLAlchemy `create_all` 建立的数据库上会重复加列而失败。正确路径是引入**版本追踪 + 基线迁移**，从当前可运行 schema 安全过渡。

## 目标与非目标

目标：

1. 每个数据库可查询已应用版本与时间。
2. 新环境可从零构建完整 schema。
3. 既有 `modelgate.db` 可不丢数据地进入 migration 管理。
4. 后续 schema 改动必须有 upgrade，且注明 downgrade 可行性。

本轮不做：

- 自动回滚业务数据迁移；破坏性变更一律采用 expand/contract 两阶段。
- 在未备份的真实数据上自动执行历史 SQL。

## 设计

### 1. 版本表

新增 `schema_migrations`：`version`（主键）、`applied_at`、`checksum`、`description`。执行器按版本升序运行未记录的 migration，并在同一事务内写入记录。

### 2. 基线策略

建立新的 `011_baseline_current_schema`（或 Alembic baseline revision），表示截至当前 ORM 的完整兼容 schema。

- **新库**：只执行基线及之后的 migration；不回放 001–010。
- **已有开发库**：检查关键表/列均存在后，写入 `011` 基线记录，不执行旧 `ALTER TABLE`。
- **不满足基线的库**：中止并输出缺失对象清单；由维护者选择导出、修复或从备份恢复。

### 3. 启动行为

开发环境允许显式 `MODEL_GATE_SCHEMA_MODE=bootstrap` 创建空库；常规启动和生产环境只运行 migration 检查/执行器，不调用 `Base.metadata.create_all()`。

### 4. 迁移规范

- 文件名：`NNN_verb_noun.sql`；每个文件带目的、前置版本、upgrade 与 downgrade 说明。
- SQLite 与目标生产数据库有差异时，迁移使用 Python/Alembic operation，而不是依赖不可移植 SQL。
- 新列先可空或有默认值，应用双读/双写后才收紧约束。
- 每次 migration 需有：空库升级、已有库升级、重复执行、失败中断四项测试。

## 实施顺序

1. 建立版本表与 migration runner，只支持 dry-run 和基线标记。
2. 编写 schema inspector，验证当前 ORM 所需表/列。
3. 添加基线 revision；在临时 SQLite 文件验证“空库”和“已 create_all 的库”。
4. 将本地开发默认启动改为 runner；保留短期 bootstrap 开关。
5. 为下一次真实 schema 修改添加第一条 post-baseline migration，验证升级与 downgrade。
6. 在备份和 staging 验证通过后，移除生产 `create_all`。

## 验收证据

| 验收项 | 证据 |
|---|---|
| 空库可启动 | 临时 SQLite 从零升级后 API health 成功 |
| 现有库无损接管 | 基线前后关键表行数和 schema inspector 一致 |
| 重复安全 | 第二次 runner 显示 0 条待执行 migration |
| 失败可诊断 | 人为破坏 schema 后输出缺失对象，不写入版本记录 |
| 回滚边界明确 | 每条新 migration 有 downgrade 或明确标注 forward-only 原因 |
