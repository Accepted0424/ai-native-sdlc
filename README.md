# AI-Native SDLC Skill

一套面向 Codex 的对话式软件开发生命周期 Skill。

它把一次软件变更组织为可追踪的产物链，让 Codex 负责整理、实现、验证和准备发布，让人负责需求、方案、风险和生产发布决策。

## 快速安装

复制下面这条命令即可安装最新版 Skill：

```bash
npx --yes codex-ai-native-sdlc@latest install
```

安装完成后，在目标项目的 Codex 任务中输入：

```text
$ai-native-sdlc 管理这次软件变更
```

```text
intent → spec → plan → build → test → review → deploy → complete
   ↑                                                          │
   └──────────────── incident / monitoring feedback ──────────┘
```

日常使用不需要运行工作流 CLI。用户只需要在 Codex 中描述任务、检查阶段结果并回复是否批准。Skill 内部会自动维护状态、产物和审计记录。

## 适用场景

- 需要先澄清需求，再进入实现的功能开发；
- 涉及数据迁移、安全或较大回归风险的代码变更；
- 希望保存需求、设计、计划、代码和测试之间的证据链；
- 由生产事故、告警或复盘行动触发的修复；
- 需要明确区分“代码完成”“测试通过”“批准发布”和“已经部署”的团队。

普通的一次性代码解释、简单格式修改或无需阶段治理的小任务，不必使用这套 Skill。

## 安装

### 通过 npm 安装

npm 包只负责把 Skill 安装到 Codex，不会把日常开发流程变成 CLI：

```bash
npx --yes codex-ai-native-sdlc@latest install
```

安装完成后，仍然通过 Codex 对话使用：

```text
$ai-native-sdlc 管理这次软件变更
```

覆盖已有版本时，安装器会先生成可恢复备份：

```bash
npx --yes codex-ai-native-sdlc@latest install --force
```

### 手动安装

Skill 目录必须保留完整结构：

```text
ai-native-sdlc/
├── SKILL.md
├── agents/openai.yaml
├── assets/templates/
├── references/
└── scripts/workflow.py
```

将 `ai-native-sdlc` 文件夹放到个人 Codex Skills 目录：

```text
~/.codex/skills/ai-native-sdlc/
```

也可以解压发布包：

```bash
mkdir -p ~/.codex/skills
unzip ai-native-sdlc.skill.zip -d ~/.codex/skills
```

依赖：

- Codex；
- Python 3.9 或更高版本；
- 目标项目自身的构建、测试和代码检查工具。

Skill 本身不依赖第三方 Python 包。

## 开始使用

在目标项目的 Codex 任务中输入：

```text
$ai-native-sdlc 为订单服务增加幂等创建能力
```

也可以直接使用自然语言：

```text
按照 AI-Native SDLC 管理这次搜索缓存改造，从需求意图开始。
```

Skill 会为变更生成一个稳定 ID，并在项目内建立：

```text
.ai-sdlc/changes/<change-id>/
├── manifest.json
├── audit.jsonl
├── intent.md
├── spec.md
├── plan.md
├── evidence.md
├── review.md
└── deploy.md
```

只有流程已经到达的文件才会出现。

## 实际交互示例

用户发起需求：

```text
$ai-native-sdlc 修复支付回调重试导致重复创建订单的问题
```

Codex 首先调查问题并生成 `intent.md`，随后给出摘要：

```text
Intent 已整理：

- 问题：相同 payment_id 的并发回调可能生成多个订单；
- 目标：同一租户内相同 payment_id 最多产生一个订单；
- 约束：数据库保证正确性，不能只依赖 Redis 锁；
- 待确认：历史重复数据如何处理。

是否批准进入 spec 阶段？
```

用户可以批准：

```text
批准，历史重复数据先生成报告，不自动删除。
```

Codex 会记录这次决定，补充约束并进入 `spec`。如果用户回复：

```text
不批准，先补充跨租户 payment_id 相同的情况。
```

任务会停留在当前阶段，Codex 修改 `intent.md` 后重新请求审批。

## 阶段说明

### 1. Intent

记录为什么要改：

- 当前问题；
- 可观察的成功结果；
- 受影响的用户和系统；
- 安全、兼容性和交付约束；
- 明确不做什么；
- 尚未回答的问题。

此阶段不应提前确定具体文件和实现方案。

### 2. Spec

Codex 阅读已经批准的 `intent.md` 并检查真实项目代码，形成：

- 功能和非功能需求；
- 系统边界与数据流；
- 接口及状态变化；
- 可执行的验收标准；
- 安全、合规和设计问题。

### 3. Plan

将规格转换为文件级实施计划：

- 修改或新增哪些文件；
- 具体实施顺序；
- 风险和影响范围；
- 没有采用的替代方案；
- 测试命令及预期结果；
- 回滚方式。

计划未被批准前，Codex 不修改实现代码。

### 4. Build

Codex 按批准后的计划实现代码并补充测试。如果实现必须偏离计划，需要同步更新 `plan.md` 并说明原因。

### 5. Test

Codex 执行真实的构建、测试、Lint、接口检查或视觉验证，并把以下内容写入 `evidence.md`：

- 实际执行的命令或操作；
- 退出状态；
- 关键输出；
- 对验收标准的覆盖；
- 失败项和未验证部分。

测试失败时流程停留在 `test`。生成了测试文件、预计命令会通过或只检查 HTTP 状态，都不能冒充已经完成的运行验证。

### 6. Review

Codex 将实际变更与 `intent.md`、`spec.md`、`plan.md` 和 `evidence.md` 对照，记录：

- 是否满足原始意图；
- 是否存在越界修改；
- 正确性、安全和回归问题；
- 测试证据是否充分；
- 剩余风险和处理建议。

最终接受或拒绝仍由人决定。

### 7. Deploy

Codex只准备发布方案：

- 目标环境；
- 不可变的 Commit、镜像或制品标识；
- 灰度步骤；
- 监控基线和回滚阈值；
- 已演练的回滚命令或 Runbook；
- 需要谁授权。

发布方案被批准不等于已经上线。只有实际部署或回滚结果被观察并记录后，生命周期才会进入 `complete`。

## 五个人工审批门

以下阶段必须获得明确的人类决定：

| 审批门 | 主要判断 |
|---|---|
| Intent | 问题和目标是否正确 |
| Spec | 需求、设计和验收标准是否合理 |
| Plan | 文件级方案和风险是否可接受 |
| Review | 代码及剩余风险是否允许进入发布 |
| Deploy | 是否授权按发布方案执行 |

Codex 不会根据沉默、“继续做”或之前的宽泛授权推断审批。每次审批只对应当时可见的产物版本；批准后发生实质变化，需要重新审批。

## 事故闭环

生产告警可以直接启动 Skill：

```text
$ai-native-sdlc 处理订单服务 5xx 超过过去 30 天基线 3σ 的事故
```

Codex 会以 `incident` 作为来源创建新的 `intent.md`，记录指标、基线、时间窗口和已知影响，然后走正常的规格、计划、实现、测试、评审和发布流程。

紧急回滚可以使用已经批准的 Runbook，但不会替代永久修复的证据链。

## 项目产物

### `manifest.json`

保存当前阶段、状态、审批和事件索引，供 Skill 判断应该继续哪一步。

### `audit.jsonl`

追加记录创建、批准、拒绝、构建完成、验证结果和发布结果。它与 Git 历史共同组成审计线索。

### Markdown 产物

Markdown 同时服务于人和 Codex：人可以直接评审，Codex 可以在后续任务或上下文压缩后重新读取，不依赖早期聊天记录。

## 内部实现

`scripts/workflow.py` 是 Skill 内部使用的确定性状态控制器，负责：

- 创建变更目录和初始模板；
- 校验阶段顺序；
- 拦截残留占位符和未完成产物；
- 记录批准、拒绝和验证事件；
- 区分发布批准与真实部署结果；
- 输出机器可读状态。

用户不需要直接调用这个脚本。它的存在是为了避免仅靠提示词维护状态。

## 安全与治理边界

- Skill 不自动获得 merge、push、部署或访问生产环境的权限；
- 对话中的审批声明不能代替组织级身份认证；
- 正式环境仍应使用 CODEOWNERS、受保护分支、必需 CI 检查、沙箱、短期凭据和部署平台授权；
- 写入仓库前需要清理 Token、个人数据和生产请求原文；
- Skill 不会为了通过测试而擅自弱化已经批准的验收标准；
- 没有可验证回滚路径时，发布阶段应明确报告风险。

## 验证情况

当前版本已经验证：

- Skill 和 UI 元数据可以被 YAML 解析；
- `workflow.py` 不依赖第三方包；
- 未完成模板不能通过阶段校验；
- 阶段不能越级推进；
- 测试失败不会进入 Review；
- Review 和 Deploy 必须记录人工审批；
- 发布批准不会被记录为已经部署；
- 从 Intent 到真实发布结果的完整生命周期可以闭环。

## 参考

- [Anthropic：The AI-Native SDLC playbook](https://claude.com/blog/the-ai-native-sdlc-playbook)
- [OpenAI model guidance](https://developers.openai.com/api/docs/guides/latest-model)
