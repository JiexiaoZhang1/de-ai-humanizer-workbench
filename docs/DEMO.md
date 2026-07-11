# Demo Guide / 演示指南

[中文演示](#中文演示) | [English Demo](#english-demo) | [Screenshot Index](#screenshot-index--截图索引)

## 中文演示

### 演示目标

这次演示要让观众在几分钟内明白四件事：

1. De-AI 是可排序的英文改写流水线，不是一个只有“提交”按钮的黑盒。
2. 88 个节点是不同来源和类别的改写配置，不是 88 个本地模型。
3. 后端不只调用模型，还会检查段落、数字、引用和技术内容。
4. 项目可以只用内置规则运行，第三方仓库只是可选的本地参考资料。

### 演示前准备

在演示开始前完成下面的检查：

```bash
python3 tools/qa_50_tests.py
export NVIDIA_API_KEY="your-key-here"
python3 server.py --host 127.0.0.1 --port 8765
```

然后打开 `http://127.0.0.1:8765`，确认右上角显示 `88 nodes ready`。

如果要展示来源增强模式，可以提前运行：

```bash
python3 tools/fetch_sources.py
```

不要在投屏时打开 `config.local.json`、环境变量列表、终端历史或网络请求中的授权头。

### 推荐演示文本

下面这段文本同时包含模板化表达、三个段落和需要保护的技术内容，适合展示核心能力：

```text
As AI tools become woven into everyday research and product work, teams are experiencing a significant transformation in how they draft, revise, and publish written material. This paper aims to explore the important value of AI-assisted writing and analyze its role in productivity, knowledge synthesis, and editorial decision-making.

The operations team processed 18,420 messages in July 2026, and p95 latency rose by 12.8% after API v2.3.1. The incident is tracked as INC-4421, while the recovery plan remains in docs/q3-plan.md. These details must remain unchanged even when the surrounding prose is revised.

In conclusion, AI-assisted writing has important significance and broad prospects across academic and professional contexts. Organizations should establish a balanced process across tool use, editorial review, and ethical standards in order to improve writing quality in a sustainable way.
```

这段文字有意放入：

- `18,420` 和 `12.8%`。
- `July 2026`。
- `p95` 和 `API v2.3.1`。
- `INC-4421`。
- `docs/q3-plan.md`。
- 三段明确的段落结构。

### 五分钟现场演示流程

#### 0:00-0:40：说明问题

建议讲法：

> 很多英文 AI 初稿的问题不是语法错误，而是句式和过渡太固定。直接让模型“写自然一点”又容易把数字、术语和段落改坏。这个 Demo 把改写方法和质量检查拆开：节点处理表达，后端守住事实和结构。

屏幕操作：

- 停留在工作台顶部。
- 指出左边输入、中间流水线、右边输出。
- 不需要先滚动到节点库。

#### 0:40-1:30：展示流水线

建议讲法：

> 默认流水线有两个节点，系统会从上到下执行。节点可以拖拽，也可以用上下按钮调整。这里的节点不是单独的模型，而是不同的改写规则和来源配置，最后都通过同一个受控模型接口执行。

屏幕操作：

- 将第二个节点上移，再移回原位。
- 点击 `Default` 恢复默认顺序。
- 指出每个节点显示的上游项目名称。

#### 1:30-2:15：展示节点库

建议讲法：

> 节点库一共有 88 个节点，分成学术、anti-slop、Python、Node/Web 等 8 类。公开仓库不携带那些第三方项目的完整代码，默认只用本项目自己的 8 类基础规则；如果本机单独下载了某个来源，界面会显示 Source cached。

屏幕操作：

- 滚动到 `Node Library`。
- 点击 `Academic` 类别。
- 搜索 `academic` 或一个仓库名称。
- 添加一个节点，再移除，避免正式执行时增加不必要的 API 调用。

#### 2:15-3:20：执行改写

建议讲法：

> 现在运行默认两节点流水线。每个节点返回后，后端会先清理模型多加的标题、分数或解释，再检查三段结构和受保护内容。如果首次结果不合格，会自动重试或修复；仍然破坏结构时，就保留进入这个节点之前的文本。

屏幕操作：

- 粘贴推荐演示文本。
- 在 `Run note` 中保留默认要求。
- 点击 `Run pipeline`。
- 等待进度浮层完成，不要连续点击。

#### 3:20-4:20：检查结果

建议讲法：

> 输出不应该出现分析报告或检测分数。我们先看它是不是仍然有三段，再检查几个不允许改动的锚点：18,420、12.8%、July 2026、API v2.3.1、INC-4421 和文件路径。措辞可以变化，但这些内容和责任关系不能丢。

屏幕操作：

- 指出顶部 Input/Output 段落统计。
- 在右侧输出中逐个指出关键内容。
- 指出底部 `2/2 nodes completed` 摘要。

#### 4:20-5:00：收尾

建议讲法：

> 所以这个项目真正展示的是一个可控的改写工程流程：人决定节点和顺序，模型负责候选文本，程序负责清理、检查和回退。它不能证明作者身份，也不保证检测器结果，但它比一次没有约束的重写更容易检查和复现。

### 演示成功标准

现场演示完成后，应当能确认：

- 右上角显示服务与密钥正常。
- 节点可以搜索、添加、删除和排序。
- 输入与输出都是三段。
- 所有预设技术锚点仍然存在。
- 输出没有额外标题、评分、解释、列表或表格。
- 完成摘要显示节点执行数量。
- 页面在桌面和窄屏下没有明显遮挡或横向溢出。

### 没有 API 密钥时怎么演示

没有真实密钥时，不要伪装成在线运行成功。可以采用下面的备用方式：

1. 展示工作台、节点排序、搜索和分类筛选。
2. 展示 README 中已经保存的真实界面截图。
3. 使用 `python3 server.py --demo` 启动明确标注的本地演示模式，并展示一次确定性示例改写。
4. 运行 `python3 tools/qa_50_tests.py`，说明 110 项测试使用模拟模型调用，不消耗真实额度。
5. 打开 [架构说明](ARCHITECTURE.md)，讲解质量检查和回退流程。
6. 明确告诉观众，真实模型改写需要用户自己的 NVIDIA 凭据。

### 现场常见问题

| 情况 | 处理方式 |
| --- | --- |
| 右上角显示 `API key required` | 检查当前终端是否设置 `NVIDIA_API_KEY`，然后重启服务 |
| 端口被占用 | 改用 `--port 8766` 并打开对应地址 |
| React 页面空白 | 检查浏览器是否能访问 `https://esm.sh` |
| 模型调用时间较长 | 保持默认两节点，不要临时添加多个节点 |
| 某节点失败但 HTTP 仍为 200 | 查看步骤摘要；后端会把该节点输入作为输出继续执行 |
| 输出保留原文 | 可能是结果持续未通过结构检查，属于保守回退 |
| 来源显示 `Built-in` | 正常；代表没有下载可选上游仓库，节点仍可使用 |

## English Demo

### Demo objective

The audience should leave with four clear points:

1. De-AI is an ordered, inspectable rewrite pipeline rather than a one-button black box.
2. The 88 nodes are rewrite configurations and source references, not 88 local models.
3. The backend validates structure and protected details after every model call.
4. A clean clone works from built-in profiles; upstream repositories are optional local references.

### Preparation

```bash
python3 tools/qa_50_tests.py
export NVIDIA_API_KEY="your-key-here"
python3 server.py --host 127.0.0.1 --port 8765
```

Open `http://127.0.0.1:8765` and confirm the status pill says `88 nodes ready`. Do not open local credential files or authorization headers while sharing the screen.

### Five-minute walkthrough

#### 0:00-0:40 — Frame the problem

Suggested narration:

> Many model-generated drafts are grammatically correct but structurally repetitive. A broad request to make them sound natural can also damage numbers, citations, and technical terms. De-AI separates those jobs: nodes guide the edit, while one shared backend protects structure and factual anchors.

Show the input, pipeline, and output columns.

#### 0:40-1:30 — Explain the pipeline

Suggested narration:

> The default pipeline has two nodes and executes from top to bottom. I can drag nodes or use explicit move controls. A node is not a separate model; it is an editorial profile and source configuration executed through the same constrained model client.

Move the second node up, move it back, and use `Default` to reset the sequence.

#### 1:30-2:15 — Explore the library

Suggested narration:

> The library contains 88 nodes in eight categories. The public repository does not redistribute the upstream projects. Every node starts with a project-owned built-in profile, and a reviewed upstream source can be cached locally when deeper reference material is useful.

Filter to `Academic`, search for a node, add it, and remove it before the live run.

#### 2:15-3:20 — Run the rewrite

Suggested narration:

> After each model response, the server removes unwanted reports or labels, checks the three-paragraph structure, and verifies protected values. A failed candidate is retried or repaired. If the structure remains unsafe, the node keeps its previous input instead of passing damage downstream.

Paste the sample from the Chinese section above and run the default pipeline.

#### 3:20-4:20 — Inspect the result

Verify the output still contains:

- `18,420`
- `July 2026`
- `p95`
- `12.8%`
- `API v2.3.1`
- `INC-4421`
- `docs/q3-plan.md`
- Exactly three paragraphs

Point out that the wording can change while these anchors and their relationships remain intact.

#### 4:20-5:00 — Close

Suggested narration:

> The project demonstrates a controlled editing workflow: the user chooses the sequence, the model proposes revisions, and the program cleans, checks, and falls back. It does not prove authorship or guarantee detector outcomes. Its value is that the rewrite process is visible, testable, and easier to review than a single unconstrained prompt.

### Demo checklist

- The status pill confirms 88 nodes and an API key.
- Search, filter, add, remove, drag, and move controls work.
- Input and output paragraph counters both show three.
- Every protected value remains present.
- No report, score, heading, table, or list leaks into the result.
- The completion summary reports the expected node count.
- Desktop and mobile layouts remain readable without incoherent overlap.

## Screenshot Index / 截图索引

### Desktop workbench / 桌面端工作台

![Desktop workbench](assets/workbench-desktop.png)

Shows the initial three-column editor, default two-node pipeline, status, and the beginning of the node library.

### Completed run / 完成一次运行

![Completed run](assets/workbench-result.png)

Shows a finished output and the node completion summary. No credential is visible in the capture.

### Mobile layout / 移动端布局

![Mobile layout](assets/workbench-mobile.png)

Shows the stacked mobile flow and confirms that controls and text remain inside the viewport.
