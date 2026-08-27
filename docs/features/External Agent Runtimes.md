# External Agent Runtimes

> 状态：Draft
>
> 职责：外部 Agent Runtime 作为 Workflow 节点执行单元的设计草案
>
> 最后更新：2026-07-12

## Feature 目标

OpenCAI 可以把 Codex CLI、Claude Code CLI、AGY CLI 或其他完整 Agent harness 作为 Workflow 中的节点 Agent 调用，而不是把这些 Agent 当成普通 LLM Provider。

外部 Agent Runtime 负责完成单个节点内部的代码理解、工具调用、文件修改和验证闭环；OpenCAI 继续持有 Workflow 的计划、顺序、状态、失败恢复和最终 handoff。

```text
OpenCAI Workflow
  -> 决定何时执行哪个节点、节点之间传递什么、失败后走向哪里

External Agent Runtime
  -> 完成当前节点内部的 agent loop 和真实工具执行
```

该能力的价值不是简单转发用户输入，而是让 OpenCAI 在复用成熟 Agent 执行能力的同时，提供稳定流程、结构化状态、独立 review、验证门槛和 retry。

## 核心边界

外部 Agent Runtime 不属于 `LLMAdapter`。

```text
LLMAdapter
  -> 单次模型决策边界
  -> 输入 messages + tools
  -> 输出 tool_call 或 final_answer

External Agent Runtime
  -> 完整 Agent 执行边界
  -> 内部拥有自己的 model loop、tools、context 和 session
  -> 输出事件流、文件变更、验证证据和最终结果
```

如果把 Codex、Claude Code 等完整 Agent 塞进 `LLMAdapter.call()`，OpenCAI 会出现双重 Agent Loop、双重 Tool Model 和双重权限判断。因此，外部 Agent 必须通过独立的 runtime / executor 抽象接入。

## 接入形态

不同 Agent 可以暴露不同接口，OpenCAI 不应把实现限定为某一条 CLI 命令。

### One-shot CLI

OpenCAI 启动一次性子进程，传入任务，并读取 stdout 中的文本或 JSONL 事件。

```text
spawn command
  -> write prompt / arguments
  -> read stdout events
  -> read stderr diagnostics
  -> wait for exit code
  -> normalize result
```

适合短任务、smoke test 和第一阶段验证。限制是进程通常在单次任务后退出，中途审批、steer 和长期 session 能力较弱。

### Long-lived Protocol Server

OpenCAI 启动长期运行的 Agent 服务，通过 stdio、WebSocket 或其他 transport 交换结构化请求、响应和事件。

候选协议包括 Codex app-server JSON-RPC、Agent Client Protocol，以及其他 Agent 提供的等价协议。

```text
start server process
  -> initialize connection
  -> create / resume session
  -> start task turn
  -> stream events
  -> handle approval / steer / cancel
  -> persist external session id
```

适合需要持续会话、人工审批、暂停恢复、实时过程展示和后台任务的成熟接入。

### SDK

如果 Agent 提供稳定 SDK，Runtime Adapter 可以通过 SDK 启动或连接 Agent。SDK 只是 transport 和协议封装，不改变“外部 Agent 是完整执行单元”的架构定位。

### Native TUI / PTY

OpenCAI 可以在 PTY 中启动 Agent 原生 TUI，并镜像终端输入输出。该形态适合保留原生交互体验，但结构化事件、状态恢复和自动化控制通常弱于正式协议，因此不作为 Workflow 自动编排的首选接口。

## 核心架构

建议增加独立于 Model Runtime 的 Agent Runtime 层：

```text
WorkflowRunner
  -> AgentDispatcher
      -> AgentRuntimeRegistry
          -> OpenCAIRuntimeAdapter
          -> CodexRuntimeAdapter
          -> ClaudeRuntimeAdapter
          -> AgyRuntimeAdapter
          -> CustomRuntimeAdapter

AgentRuntimeAdapter
  -> start / resume / execute / steer / cancel
  -> normalize native events
  -> return NodeExecutionResult
```

主要职责：

- `WorkflowRunner`：解释执行 `WorkflowSpec + WorkflowScript`，不感知具体 CLI 命令。
- `AgentDispatcher`：根据节点配置、role、能力和 policy 选择 runtime。
- `AgentRuntimeRegistry`：注册可用 runtime、能力声明和 adapter factory。
- `AgentRuntimeAdapter`：处理外部进程、协议、认证、session 和事件转换。
- `NodeExecutionResult`：向 Workflow 返回 provider-independent 结构化结果。

## Node Agent 合同

Workflow 节点不能只向外部 Agent 传递一段无约束 prompt。节点需要明确的输入、输出和权限合同。

### NodeExecutionRequest

```text
workflow_run_id
node_id
phase_id
role
original_task
instruction
dependency_results
cwd
permission_profile
timeout
expected_output_schema
external_session_id (optional)
```

### NodeExecutionResult

```text
node_id
runtime_id
status
final_answer
events
changed_files
artifacts
verification_evidence
usage
external_session_id
error
```

`dependency_results` 应只包含当前节点声明依赖的结构化摘要和 artifact reference，不复制其他节点的完整原始消息流。

## 数据流

```text
User Task
  -> Workflow Clarify / Planner
  -> WorkflowSpec + WorkflowScript
  -> WorkflowRunner selects next node
  -> AgentDispatcher selects runtime
  -> build NodeExecutionRequest
  -> AgentRuntimeAdapter executes external Agent
  -> native events
  -> RuntimeEventNormalizer
  -> OpenCAI node events
  -> NodeExecutionResult
  -> WorkflowRun ledger
  -> branch / retry / review / verify / handoff
```

外部 Agent 的原生事件不能直接成为 Workflow 的事实模型。Runtime Adapter 必须先转换为 OpenCAI 可以稳定消费的事件，例如：

```text
session_started
node_started
assistant_output
command_started
command_completed
file_change
tool_started
tool_completed
approval_requested
verification
usage_updated
node_completed
node_failed
```

OpenCAI 可以保存必要的原生 payload 用于诊断，但 Workflow 状态判断只依赖规范化字段。

## Session 映射

OpenCAI session、WorkflowRun 和外部 Agent session 是不同对象。

```text
OpenCAI RuntimeSession
  -> 可以包含多个 WorkflowRun

WorkflowRun
  -> 可以调度多个 node Agent

Node Agent
  -> 可以创建或恢复一个外部 Agent session / thread
```

OpenCAI 需要持久化最小映射：

```text
workflow_run_id + node_id + runtime_id
  -> external_session_id
```

外部 Agent 进程退出不等于 session 消失。若目标 runtime 支持持久化，新的 adapter 进程可以通过 `external_session_id` 恢复后续 turn。

## Context 所有权

OpenCAI 负责提供 workflow-scoped context：

- 原始任务。
- 当前 phase、role 和节点 instruction。
- 明确声明的 dependency results。
- 节点权限、修改范围和验收要求。
- 期望的结构化输出合同。

外部 Agent Runtime 负责加载自己的 startup context：

- Agent 自身 system instructions。
- repo 中由该 Agent 原生支持的 instruction files。
- Agent 自己的 skills、plugins、MCP 和工具配置。
- Agent session 内部的历史消息。

OpenCAI 不应默认把完整 system prompt、全部 AGENTS 内容或所有历史节点结果再次拼进外部 Agent prompt。重复注入会造成指令冲突、token 浪费和事实来源不清。

## Tool 与权限所有权

节点必须明确选择唯一的实际工具执行方。

```text
OpenCAI-native node
  -> OpenCAI Agent Loop
  -> OpenCAI Tool Registry
  -> OpenCAI SafetyPolicy

External-Agent node
  -> External Agent Loop
  -> External Agent tools
  -> External Agent sandbox / approval protocol
```

OpenCAI 对外部节点仍负责设置权限上限、cwd、可写 workspace roots、timeout、并发限制和 cancel；但不能把外部 Agent 内部未暴露的工具调用描述为已经经过 OpenCAI `SafetyPolicy` 的逐次裁决。

如果 OpenCAI permission profile 无法等价映射到目标 Agent，adapter 必须明确拒绝、降级或要求 human approval，不能静默扩大权限。

## Runtime 能力声明

不同 Agent Runtime 的能力不一致。Registry 需要通过 capability metadata 做显式选择，而不是假设所有 CLI 都支持相同功能。

```text
structured_events
persistent_session
resume
streaming
steer
cancel
interactive_approval
structured_output
file_change_events
usage_events
native_tools
```

Workflow Planner 或 Dispatcher 只能选择满足节点必要能力的 runtime。例如，需要中途 human approval 的节点不能分配给只支持 one-shot 非交互执行的 backend。

## Workflow 中的使用方式

外部 Agent 是节点执行策略，不是新的顶层 phase。

```text
diagnose
  -> runtime: codex

execute
  -> runtime: claude

review
  -> runtime: agy

verify
  -> runtime: opencai
```

`clarify / plan / execute / review / verify / handoff` phase vocabulary 保持不变。具体使用哪个 Agent，应落在 task/node 的 runtime selection 上。

## Failure Model

Runtime Adapter 至少需要区分：

- Agent executable 不存在。
- 启动失败。
- 认证不可用。
- 协议初始化失败。
- session 无法恢复。
- timeout 或取消。
- 事件格式不兼容。
- Agent task failed。
- 进程异常退出。
- 任务完成但缺少结构化结果。

这些错误必须进入 `NodeExecutionResult.error` 和 WorkflowRun ledger，由 Workflow policy 决定 retry、切换 runtime、humancheck 或 stop。

## 当前状态

- OpenCAI 当前没有 `AgentRuntimeAdapter`、`AgentDispatcher` 或外部 Agent session 映射。
- 当前 `SerialWorkflowRunner` 仍直接调用 OpenCAI `run_agent_loop()`。
- Codex、Claude、AGY 和其他 Agent 均未在 OpenCAI 中实现或验证。
- 本文只定义候选架构和边界，不代表已选择首个 runtime，也不代表任何外部 Agent 已受支持。

## 非目标

- 不把外部 Agent 当作普通 `LLMAdapter`。
- 不让外部 Agent 接管 OpenCAI 的 Workflow control plane。
- 不要求所有 Agent 使用同一种 transport。
- 不在第一步统一所有外部 Agent 的完整原生功能。
- 不默认允许多个写入型 Agent 并行操作同一个 workspace。
- 不复制外部 Agent 的内部实现。

## 待确认决策

1. 首个验证 backend 选择 one-shot CLI 还是 long-lived protocol server。
2. 首个支持对象选择 Codex、Claude Code、AGY 或其他 Agent。
3. 一个 WorkflowRun 复用单个外部 session，还是每个 node 创建隔离 session。
4. RuntimeEvent 是扩展现有 `Event`，还是增加独立 provider-independent event envelope。
5. 外部 Agent 写入 workspace 时采用串行独占、worktree 隔离还是其他策略。
6. `AGY CLI` 的正式产品名、命令名和可用协议需要单独核实。
