### 一、 产品设计思路 (Product Design)

这个项目的核心价值在于 **“信息聚合与自动化决策辅助”**。它解决的痛点是：投资者在分析股票时，需要在交易软件（看数据）和新闻网站（看消息）之间反复切换，且难以快速整合信息。

#### 1. 核心工作流 (Workflow)

我们可以将其抽象为经典的 **Input-Process-Output** 模型：

* **输入 (Input):** 用户提供一个简简单的指令（如“300750”）。
* **处理 (Process - The "Black Box"):**
* **定量分析:** 像爬虫一样去抓取实时的资金流向数据（硬数据）。
* **定性分析:** 像记者一样去搜索全网的最新新闻舆情（软数据）。
* **认知综合:** 像分析师一样，将“硬数据”和“软数据”结合，进行逻辑推理（如：资金流出+利好新闻=诱多出货？）。


* **输出 (Output):** 一份结构化、可读性强、带有行动建议的研报（Markdown/Web界面）。

#### 2. 迭代路径 (Roadmap)

回顾我们的开发过程，这是一个标准的 MVP 迭代路径：

* **v1.0 (MVP):** 单点功能跑通。只查资金数据，黑框框运行。（验证核心API可行性）
* **v2.0 (Productization):** 产品化封装。加上 Streamlit 界面，变成 Web App。（提升交互体验）
* **v3.0 (Enhancement):** 能力增强。加入联网搜索 (Search Tool)，实现多模态信息融合。（提升业务价值）

---

### 二、 多 Agent 技术架构 (Technical Architecture)

这是你最关心的部分。所谓的 **Multi-Agent (多智能体)** 系统，本质上是 **“大模型 (Brain) + 工具 (Tools) + 流程编排 (Orchestration)”** 的组合。

下面我画了一张架构图来解释我们在 `CrewAI` 里到底做了什么：

#### 1. 核心组件拆解

* **大脑 (The Brain - DeepSeek LLM):**
* 这是系统的动力源。所有的 Agent (数据侦探、记者、分析师) 其实共用同一个大脑。
* **作用:** 理解自然语言指令、进行逻辑推理、决定是否调用工具。


* **智能体 (The Agents):**
* 在技术上，Agent 其实就是 **"Prompt + Tools"** 的封装。
* **Persona (人设):** 通过 Prompt 定义（如“你是一个只相信数字的侦探”）。这限制了 LLM 的生成范围，让它更专注。
* **Capability (能力):** 绑定特定的 Python 函数（如 `stock_fund_flow`）。只有绑定了工具，Agent 才有“手”。


* **工具与函数调用 (Tools & Function Calling):**
* 这是 Agent 最硬核的技术点。
* **原理:** 当 Agent 觉得需要查数据时，它不会直接去运行 Python 代码（因为 LLM 是生成文本的）。它会输出一个特殊的 JSON 格式文本，告诉框架：“我要调用 `stock_fund_flow`，参数是 `300750`”。
* **执行:** `CrewAI` 框架截获这个 JSON，帮它运行 Python 代码，拿到结果（如“净流出5亿”），再喂回给 LLM。


* **编排与上下文 (Orchestration & Context):**
* **流程 (Process):** 我们使用的是 `Sequential` (顺序执行)。
* **记忆传递 (Context Passing):** 这是多 Agent 协作的关键。
* 任务 1 (侦探) 跑完的结果，会被自动塞进任务 3 (分析师) 的 Prompt 里。
* **技术实现:** 分析师在写报告时，它的输入 Prompt 其实变成了：
> "根据以下数据（来自侦探的输出：...）和以下新闻（来自记者的输出：...），写一份报告。"


* 这就是为什么分析师明明没有工具，却能知道资金数据的原因。


#### 2. 我们的技术栈总结

| 层级 | 技术选型 | 作用 |
| --- | --- | --- |
| **应用层 (Frontend)** | **Streamlit** | 极速构建 Web 交互界面，无需写 HTML/CSS。 |
| **编排层 (Framework)** | **CrewAI** | 管理 Agent 的生命周期、任务分配、上下文传递。 |
| **模型层 (Model)** | **DeepSeek (via API)** | 提供推理能力 (Reasoning) 和文本生成能力。 |
| **工具层 (Tools)** | **AkShare / BeautifulSoup** | 连接真实世界的桥梁，获取实时数据和网页信息。 |
| **基础层 (Infra)** | **Python** | 胶水语言，粘合以上所有组件。 |




### 1. 有哪 3 个 Agent？

代码中定义了以下三个角色，分别负责不同的职责：

1. **数据侦探 (`scout` / `Data Scout`)**
* **职责**：负责干“苦力活”，调用 `stock_fund_flow` 工具去 AkShare 查硬核的资金数据。
* **工具**：`Stock Fund Flow Tool`。


2. **财经记者 (`reporter` / `Financial Reporter`)**
* **职责**：负责搜集信息，调用 `search_news` 工具去互联网（Bing 或模拟数据）搜最新的新闻。
* **工具**：`News Search Tool`。


3. **首席投资顾问 (`analyst` / `Chief Investment Advisor`)**
* **职责**：负责“大脑”思考。它**没有工具**，它的工作是阅读前两个人的报告，进行逻辑推理，最后写出 Markdown 格式的研报。



### 2. 它们之间是如何调用的？

严格来说，Agent 之间并没有直接互相“打电话”或“调用函数”。它们是通过 **“接力棒” (Context Passing)** 的方式进行协作的。

整个流程由 `Crew` 对象进行编排，具体机制如下：

* **机制一：顺序执行 (Sequential Process)**
* 代码中配置了 `process=Process.sequential`。
* 这意味着任务是按顺序一个接一个跑的：先跑`task_data`（查钱），再跑`task_news`（查新闻），最后跑`task_report`（写报告）。


* **机制二：上下文投喂 (Context Context)**
* 这是最核心的技术点。请看你代码中 `task_report` 的定义：
```python
task_report = Task(
    description='...',
    agent=analyst,
    # ↓↓↓ 关键在这里 ↓↓↓
    context=[task_data, task_news], 
    expected_output='Markdown研报'
)

```


* `context=[task_data, task_news]` 这行代码告诉 CrewAI 框架：
> "在让**分析师**开始工作之前，请把**侦探**查到的数据结果和**记者**搜到的新闻结果，全部拼接到分析师的 Prompt（提示词）里发给它。"

