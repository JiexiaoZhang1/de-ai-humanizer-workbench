# Pitch and Speaker Script / 双语演讲稿

[中文](#中文演讲稿) | [English](#english-speaker-script) | [Q&A](#qa--常见问答)

## 中文演讲稿

### 30 秒版本

> De-AI 是一个本地英文改写工作台。用户把英文文本放进来，选择并排列不同的改写节点，后端按顺序调用模型，同时检查数字、引用、术语、路径和段落有没有被改坏。它不是简单地再发一次提示词，而是把改写、清理、验证、重试和回退做成一条能看见、能调整的流水线。项目有 88 个节点，但公开仓库不打包第三方代码，默认使用 8 类自有规则，外部来源只在本地按需下载。

### 90 秒版本

> 很多 AI 生成的英文没有明显语法错误，但读起来会有固定的开场、过渡和总结。直接让另一个模型“写得像人一点”虽然简单，却容易带来第二个问题：数字、引用、文件路径、版本号或段落结构可能被改错。
>
> De-AI 把这两件事分开处理。前端是一张三栏工作台，左边是原文，中间是可以排序的节点流水线，右边是结果。用户从 88 个节点中选择需要的规则，后端逐个调用 NVIDIA 对话模型。每一步返回后，程序都会清理模型多加的标题、分数和解释，再检查段落数量、数字、日期、URL、代码片段、配置键和其他技术锚点。
>
> 如果第一次结果不合格，系统会自动重试和修复；段落结构仍然不稳定时，会改成逐段处理；最后仍然有明显问题，就保留上一步文本。这个项目不保证任何检测器结果，也不能代替人工审稿，它展示的是怎样把一次随意的模型改写，变成一个更容易检查、测试和扩展的工程流程。

### 三分钟版本

> 我做这个 Demo，起点不是“再做一个文本框加提交按钮”，而是一个比较具体的问题：英文 AI 初稿常常语法没错，但表达方式高度重复。开头先说某件事很重要，中间按 First、Second、Finally 排列，结尾再把前面的话总结一次。读者能看懂，但会觉得空泛。
>
> 常见做法是再给模型一句“humanize this text”。这能改掉一部分表面措辞，却不容易控制副作用。比如原文里的 18,420、12.8%、API v2.3.1、INC-4421 或 docs/q3-plan.md，任何一个被模型随手改掉，文本可能更顺了，内容却不可靠了。
>
> De-AI 的界面把这个过程拆成三栏。左边输入原文，中间安排节点，右边看最终结果。节点库有 88 个配置，来自学术改写、anti-slop、通用写作规则、Python、Node/Web、MCP 和参考应用等方向。这里需要特别说明：88 个节点不是 88 个模型，也不是 88 个第三方程序在本机运行。每个节点是一份元数据、一类内置编辑规则，以及可选的上游文本参考，最后都通过同一个模型接口执行。
>
> 真正关键的部分在后端。模型每返回一次，系统先清理它擅自添加的分析、评分、标题、列表和 Markdown，然后从原文中提取需要保护的内容，检查输出有没有保留段落数量、数字、日期、引用、URL、文件路径、工单号、金额、标准和代码片段。如果有问题，先严格重试，再用修复提示处理；严重的段落压缩还会逐段重写。如果仍然不安全，就把当前节点的输入原样保留下来，避免错误继续传到后面的节点。
>
> 公开仓库还有一个边界处理。最初调研下载了 93 个仓库，大约 397 MB，其中不少仓库没有明确许可证，所以这些镜像不会被上传。公开版只保留 88 个已接入来源的链接和文件选择规则，并提供下载脚本。没有任何外部仓库时，节点依然使用本项目自己的 8 类规则运行。
>
> 因此，这个项目的价值不是宣称文字一定能骗过某种检测，而是把改写从一次不可见的模型请求，变成一个有顺序、有检查、有警告、有回退的流程。它仍然需要人工判断事实和文风，但已经能把很多常见风险放到程序里反复测试。

### 五分钟演讲结构

#### 第一部分：问题，约 45 秒

> AI 初稿常见的困难不是完全不能读，而是太像一套固定格式。另一方面，二次改写又可能损坏数字、引用和技术信息。自然度与内容保真需要同时处理。

屏幕建议：显示包含技术锚点的三段示例文本。

#### 第二部分：产品界面，约 60 秒

> 工作台左边输入、中间编排、右边输出。节点可以搜索、筛选、添加、删除和排序。顺序直接决定处理顺序，因此用户可以复现实验，也能比较不同组合。

屏幕建议：移动节点，筛选 Academic 类别，最后恢复默认两节点。

#### 第三部分：后端流程，约 90 秒

> 每个节点将内置规则、节点描述和可选来源资料拼成提示词。模型输出先经过清理，再进入质量检查。检查项包括段落数量、受保护内容、长度变化、说明泄漏、列表和表格。失败后按重试、修复、逐段处理和保留上一步文本的顺序恢复。

屏幕建议：展示架构图或执行进度，然后指出结果中的受保护值。

#### 第四部分：来源与安全，约 60 秒

> 第三方仓库不进入公开 Git 历史，也不会被执行。它们只在用户明确下载后作为不可信文本参考。真实密钥保存在环境变量或被忽略的本地配置中，浏览器只能看到是否已配置，不能读取密钥。

屏幕建议：展示 README 的 Built-in / Source cached 说明和 `config.example.json` 的空密钥。

#### 第五部分：边界和结论，约 45 秒

> 这个 Demo 不验证事实，不证明作者身份，也不保证检测结果。它解决的是工程上的可控性：谁决定流程、每步检查什么、失败怎么处理、第三方内容怎么隔离。最后的判断仍然由编辑者负责。

屏幕建议：停留在完成后的三栏结果页。

## English Speaker Script

### 30-second version

> De-AI is a local workbench for revising English prose through an ordered set of rewrite nodes. The user chooses the sequence, while the backend calls a configured model and checks whether numbers, citations, technical terms, paths, and paragraph structure survive each step. It turns rewriting, cleanup, validation, retry, and fallback into one visible pipeline. The project defines 88 nodes, but the public repository does not redistribute upstream code: every node works from one of eight built-in profiles, and outside sources are downloaded only when the user chooses to cache them locally.

### 90-second version

> Many model-generated English drafts are grammatically correct but rely on predictable openings, transitions, and conclusions. Asking another model to make the text sound natural can improve the surface while quietly damaging facts, version numbers, citations, or paragraph structure.
>
> De-AI separates editorial guidance from quality control. The browser shows the source on the left, an ordered node pipeline in the middle, and the result on the right. A user can search 88 node configurations and decide exactly which sequence to run. The Python backend sends each step to a configured NVIDIA chat-completions model, removes unwanted headings and explanations, and then checks paragraph count, numbers, dates, URLs, code spans, configuration keys, and other protected anchors.
>
> If a response fails, the server retries, repairs, and can fall back to paragraph-level rewriting. If the result is still structurally unsafe, it keeps the previous text. The project does not promise detector outcomes or replace editorial review. It demonstrates how to turn an unconstrained rewrite prompt into a process that is visible, testable, and easier to extend.

### Three-minute version

> This demo started with a narrower problem than “build another AI writing tool.” Model-generated English is often readable, but its structure is repetitive: broad opening, mechanical sequence, broad conclusion. A simple “humanize this” prompt may change the wording, but it also gives the model freedom to alter details that should not move.
>
> Consider a paragraph containing 18,420 messages, July 2026, p95 latency, a 12.8% change, API v2.3.1, incident INC-4421, and docs/q3-plan.md. If any one of those anchors changes, smoother prose is not a successful result.
>
> De-AI presents the workflow in three columns. The source is on the left, the node sequence is in the middle, and the final result is on the right. The library contains 88 configurations across academic editing, anti-slop rules, general writing skills, Python, Node/Web, MCP, detector-oriented patterns, and reference applications. Those are not 88 models and they are not 88 programs being executed. A node is metadata, one project-owned editorial profile, and an optional upstream text reference, all routed through one controlled model client.
>
> The backend is where the project becomes more than a prompt collection. After each response, it removes model-added analysis, scores, headings, lists, tables, and Markdown wrappers. It extracts protected values from the source and checks paragraph count, length change, numbers, dates, citations, URLs, paths, issue keys, amounts, standards, and code spans. A failed candidate is retried with the exact issues. Persistent failures go through a repair prompt and then a paragraph-local fallback. If severe structure problems remain, the node returns its own input so a damaged result cannot propagate through the pipeline.
>
> The public repository also makes a deliberate licensing decision. The original research cache contained 93 repositories and occupied roughly 397 MB. Many did not expose a clear license in the local checkout, so none of those mirrors are published as part of this project. The repository keeps links and adapter metadata for 88 integrated sources and provides an optional shallow downloader. A clean clone still works from eight built-in profiles maintained here.
>
> The point is not to claim that a detector can be defeated. The point is control: the user owns the order, the model proposes text, and the program enforces explicit checks and fallback behavior. Human review is still necessary, but the risky parts of repeated model rewriting are now visible and testable.

## Q&A / 常见问答

### Is this 88 different models? / 这是 88 个不同模型吗？

No. There is one configured chat-completions model. The 88 nodes are different metadata, category profiles, and optional source references.

不是。真实运行使用一个配置好的对话模型；88 个节点是不同的元数据、规则类别和可选来源参考。

### Does it run third-party repository code? / 会运行第三方仓库代码吗？

No. The downloader only shallow-clones repositories. Current public adapters read allow-listed text as reference material and use `llm_prompt` execution.

不会。下载器只做浅克隆；当前公开节点只读取明确列出的文本文件作为参考，并通过 `llm_prompt` 执行。

### Why keep upstream repositories optional? / 为什么不直接上传那些上游仓库？

They are large, belong to other authors, change independently, and have different or sometimes unclear licenses. Links and an explicit downloader preserve research reproducibility without mixing their code into this project's ownership.

因为它们体积大、作者不同、会独立变化，而且许可证各不相同，有些还不明确。保留链接和按需下载工具，既能复现实验，也不会把别人的代码混进本项目的所有权范围。

### Does it guarantee that facts are preserved? / 能保证事实完全不变吗？

No. It checks many high-value textual anchors, but a model can keep a token and still change the surrounding meaning. Human review remains required.

不能。程序能检查很多重要文本锚点，但模型可能保留某个数字，同时改变它周围的含义，因此仍然需要人工审阅。

### Does it bypass AI detectors? / 能绕过 AI 检测器吗？

There is no guarantee. Detector outputs are unstable and do not establish authorship. The project is presented as an editing and quality-control workbench, not a detector-bypass claim.

没有保证。检测结果本身并不稳定，也不能证明作者身份。本项目定位是编辑和质量控制工作台，不以“绕过检测”为承诺。

### Why use multiple nodes? / 为什么需要多个节点？

Different profiles emphasize different editing concerns, and order can change the result. Multiple nodes also increase latency, cost, and semantic drift, so short pipelines are usually easier to inspect.

不同规则关注的编辑问题不同，顺序也可能影响结果。但节点越多，延迟、成本和语义漂移风险越高，所以短流水线通常更容易检查。

### Is the text processed fully offline? / 文本是否完全离线处理？

No. The interface and orchestration server run locally, but real rewrites send assembled requests to the configured NVIDIA endpoint. The frontend also loads React from `esm.sh` unless dependencies are vendored separately.

不是。界面和编排服务在本机运行，但真实改写会把拼装后的请求发送到 NVIDIA 接口；如果没有自行打包依赖，前端还会从 `esm.sh` 加载 React。

### What is the strongest technical part? / 最值得讲的技术点是什么？

The recovery ladder and protected-content checks. They make intermediate model failures observable and prevent a visibly damaged response from automatically becoming the next node's input.

质量检查和分层回退。它们让中间模型失败变得可观察，并阻止明显损坏的结果直接进入后续节点。
