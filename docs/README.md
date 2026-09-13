# CodeCAI 文档

本目录保存 CodeCAI 的当前状态、长期路线、功能设计、架构决策、实施计划和历史记录。每类信息只维护一个事实源；其他文档只保留摘要和链接。

## 推荐阅读顺序

1. 项目介绍与使用：[`../README.md`](../README.md)
2. 产品定义：[`PRD.md`](PRD.md)
3. 当前开发状态：[`status.md`](status.md)
4. 长期路线：[`roadmap.md`](roadmap.md)
5. 当前功能设计：[`features/`](features/)
6. 架构决策：[`adr/`](adr/)

## 文档职责

| 位置 | 职责 |
| --- | --- |
| `PRD.md` | 产品目标、目标用户、核心场景、产品范围和成功标准 |
| `status.md` | 当前主线、当前能力、已知问题、下一步和最近验证摘要 |
| `roadmap.md` | 长期目标、Feature 优先级、执行顺序和非目标 |
| `goals/` | 产品或实验的成功标准和验收口径 |
| `features/` | 当前有效的功能设计、模块边界、实现状态和限制 |
| `adr/` | 已确认且长期影响架构的决策及其原因 |
| `plans/` | 尚未完成、需要跨任务或跨会话执行的计划 |
| `logs/` | 开发流水、详细验证证据和历史状态 |
| `maps/` | 可视化和生成产物，不作为文字事实源 |
| `archive/` | 已失效但仍有历史或学习价值的材料 |
| `../references/` | 本地 reference-only 外部源码或资料，默认不提交 |

## 当前功能事实源

| Feature | 事实源 |
| --- | --- |
| Workflow | [`features/Workflow.md`](features/Workflow.md) |
| Context Engineering | [`features/Context Engineering.md`](features/Context%20Engineering.md) |
| Tools | [`features/Tools.md`](features/Tools.md) |
| LLM Providers | [`features/LLM Providers.md`](features/LLM%20Providers.md) |
| Skills | [`features/Skills.md`](features/Skills.md) |
| External Agent Runtimes | [`features/External Agent Runtimes.md`](features/External%20Agent%20Runtimes.md) |

`features/<topic>/README.md` 只作为专题索引；专题文件只保留能够独立维护的细节，不再创建第二份 Feature 总览。

## 新建文档规则

只有满足以下至少一项时才新建文档：

- 需要成为新的唯一事实源。
- 有独立目标读者或独立生命周期。
- 内容需要长期维护，加入现有文档会破坏其主题边界。
- 记录一项长期且难以逆转的架构决策。

否则优先更新现有文档：小型需求和临时 TODO 放 Issue，实施说明和验证结果放 PR / CI，稳定功能规则回写 Feature 文档，详细历史进入 `logs/`。

不要用 `V2`、`Final`、`New` 等文件名复制现有事实源；功能演进直接更新原文档，Git 负责保存版本历史。

## 文档生命周期

- `Draft`：尚未确认的设计或计划。
- `Active`：当前有效且持续维护。
- `Superseded`：已被另一份文档替代，需指向新的事实源。
- `Archived`：仅保留历史，不再作为当前入口。

活跃的 Feature、Goal 和 Plan 可以在标题后标明状态、职责和最后更新日期。README、每日日志和已归档历史不要求机械添加元数据。

计划完成后，将稳定结论合并到对应 Feature 文档，详细验证写入 `logs/`，再删除或归档计划。移动或删除文档前必须检查活跃引用；历史日志中的旧路径叙述可以保留。

## 维护检查

纯文档修改至少执行：

```powershell
git diff --check
git diff --name-status
rg -n "旧路径或旧文件名" README.md AGENTS.md docs
```

如果文档修改了命令、模块名、功能状态或验证结论，还需要运行对应命令核对事实。只有 `python -m unittest discover tests` 通过后，才能写“全量测试通过”。
