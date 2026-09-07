---
url: "https://x.com/UPing123zzz/status/2093371727611105362"
title: "我把 Eval 装进 Codex 后，AI Coding 的工作方式变了"
author: "Ethan | Builder @UPing123zzz"
source: "x_bookmark"
date: 2026-09-07
chars: 4429
images: 7
---

# 我把 Eval 装进 Codex 后，AI Coding 的工作方式变了

AI Coding 越强，Eval 越重要。

听起来有点反直觉，但这是我把 Eval 真正装进 Codex 之后最明显的感受。

因为 Build 正在变便宜，但“什么叫完成”这件事，并没有变简单。

以前我用 Codex，最常说的一句话是：

帮我把这个做好。

但现在我发现，真正难的不是让 Codex 写出代码，而是定义什么叫“做好”。

上一篇我写了 Eval，把它比喻成“给 AI 考试”。

很多人看完以后会自然地问：

如果现在代码都可以交给 Codex 写了，Eval 还重要吗？

我真正把这套流程跑起来之后，结论反而更强：

AI Coding 越强，Eval 越重要。

因为 Build 正在变便宜，但“什么叫完成”这件事，并没有变简单。

## 1. 以前我是怎么用 Codex 的？

以前我会这样给 Codex 下指令：

帮我把这个招聘 Agent 做好。优化一下这个 RAG。把这个功能全部修好。

然后 Codex 改代码、跑测试、修 Bug，最后告诉我：Done。

问题是：

Done 到底是什么意思？

代码通过了？API 返回 200 了？JSON 合法了？页面打开了？Tests Passed 了？

如果招聘 Agent 仍然把不合格候选人推荐给 HR，RAG 仍然引用了错误资料，客服 Agent 仍然会在查不到订单时编造订单状态，那它到底算不算完成？

我以前把“代码完成”误认为“任务完成”。

## 2. Tests Passed，不等于 AI 做对了

传统测试可以证明：

- 系统能跑

- API 正常

- JSON 正常

- 工具能调用

- 页面没有崩溃

但它不能单独证明：

- AI 的业务判断是对的

- RAG 答案真的有依据

- Agent 最终任务真的完成

- 客户不会被误导

Agent 可以每次都返回合法 JSON，却每次都把客户分错类。

可以成功调用搜索工具，却把搜索结果理解错。

可以流畅地回答问题，却在关键事实上产生幻觉。

Testing 解决“系统有没有坏”。Eval 解决“结果到底好不好”。

这不是二选一。

Testing 是底线。Eval 是交付线。

![Article image](/assets/2026-09-07-我把-eval-装进-codex-后，ai-coding-的工作方式变了-0fbef2579a/01.jpg)

## 3. 我怎么把 Codex 的完成标准改了

以前的流程是：

Build → Tests Passed → Done

现在我把它改成：

Baseline → Build → Test → Eval → Analyze → Fix → Re-Eval → Release

Baseline：先知道旧版本现在有多好。

Build：让 Codex 修改 Prompt、RAG、Workflow、工具或代码。

Test：确认确定性的工程部分没有坏。

Eval：在 Golden Set 上检查任务成功、正确性、完整性、依据和业务规则。

Analyze：给失败分类，找到最值得修的根因。

Fix：做最小必要修改。

Re-Eval：重新跑原来的题库，检查有没有回归。

Release：只有达到预先定义的 Release Gate，才算真正完成。

Eval 在这里不再是附加项，而是完成条件的一部分。

![Article image](/assets/2026-09-07-我把-eval-装进-codex-后，ai-coding-的工作方式变了-0fbef2579a/02.jpg)

## 4. 先跑 Baseline，而不是上来就改 Prompt

这是我改变最大的一步。

以前拿到一个 AI 项目，我通常会先看代码，然后凭经验判断应该改 Prompt 还是改 RAG。

现在我会先问：

这个系统在当前版本，到底考了多少分？

下面是一组示例基线数据，用来说明报告长什么样，并不代表某个公开项目的实测结果：

指标当前 BaselineOverall Pass Rate78%High Risk Pass Rate84%Hallucination Rate6%Regression Cases0

如果没有这些数字，后面所有“感觉更好了”都不算数。

Baseline 还应该记录当前代码或 Prompt 版本、模型与配置、Golden Set 版本、每个 Case 的原始输出、工具调用轨迹、评分器版本，以及延迟、Token 和成本（如果能测量）。

这样下一次改完以后，比较的不是印象，而是同一组输入、同一套标准下的版本差异。

![Article image](/assets/2026-09-07-我把-eval-装进-codex-后，ai-coding-的工作方式变了-0fbef2579a/03.jpg)

## 5. Eval 最值钱的地方：告诉你下一步该改哪里

假设这次有 22 个失败案例。

分类以后得到：

失败类型数量Retrieval9Tool Selection5Prompt3Hallucination2Knowledge Missing2Unknown1

如果只看总分，你可能会继续改 Prompt。

但这张 breakdown 告诉你，最大的瓶颈不是 Prompt，而是 Retrieval。

也许是文档没有被召回，也许是召回了错误文档，也许是正确文档排得太后，导致模型根本没有看到关键依据。

这时最值得做的事情，不是继续堆几句 Prompt，而是检查：

- 查询改写是否丢失了业务关键词？

- Top-k 是否覆盖了正确文档？

- 文档切片是否破坏了上下文？

- 资料是否已经过期？

- 生成答案是否真的使用了召回内容？

Eval 不只是告诉你错了多少，更重要的是告诉你下一步最值得修什么。

## 6. 修改以后，不能只测修好的那一道题

修好了一个 Case，不代表整个系统真的更好了。

你修复了“找不到订单时不要编造状态”，可能顺手让 Agent 在正常订单查询里变得过度谨慎；你提高了召回数量，可能让上下文更长、延迟更高、模型更容易被无关内容干扰。

所以每次修改之后，我会把结果拆成四组：

Improved Cases

Regressed Cases

Unchanged Cases

New Failures

这四组比一个总分更接近工程现实。

版本变化说明Improved新版本修好的案例Regressed旧版本正确、新版本变错的案例Unchanged两个版本表现相同的案例New Failures新增的失败，可能来自新路径或新数据

真正的 Regression，不是“测试没报错”，而是确认旧能力没有被新改动悄悄拿走。

![Article image](/assets/2026-09-07-我把-eval-装进-codex-后，ai-coding-的工作方式变了-0fbef2579a/04.jpg)

## 7. 我开始给 Codex 设置 Release Gate

![Article image](/assets/2026-09-07-我把-eval-装进-codex-后，ai-coding-的工作方式变了-0fbef2579a/05.jpg)

当我开始用数字描述“什么叫好”，给 Codex 的任务指令也变了。

我不再说：

帮我把这个 Agent 做好。

我会说：

先跑 Baseline。修复 Retrieval 失败。完成后跑完整 Golden Set、Regression 和高风险集合。只有满足 Release Gate，才算完成。

比如一组示例 Gate 可以是：

Gate要求Overall Pass Rate≥ 92%High Risk Pass Rate≥ 98%Hallucination Rate≤ 2%Regression Cases≤ 3

这些阈值应该根据真实业务风险校准。刚开始没有足够历史数据时，它们只能叫 provisional，而不是宇宙真理。

只要高风险通过率没有达标，或出现零容忍的业务错误，就不应该把任务标成 Done。

我不再定义“帮我做好”，而是定义“什么叫做好”。

## 8. 我甚至把 Eval 直接装进了 Codex

这件事我分成两层。

第一层：Global AGENTS.md

让 Codex 在全局知道：只要修改会影响 AI 行为，就不能只看 Tests Passed。

例如 Prompt、RAG、知识检索、Agent Workflow、Tool Calling、模型配置，以及任何会改变生成结果的逻辑，都要进入 Eval Workflow。

第二层：eval-engineering Skill

把完整流程封装成可复用的工作方法：

- Golden Set

- Rubric

- Rule Evaluator

- LLM-as-a-Judge

- Human Review

- Regression

- RAG Eval

- Agent Trace Eval

- Release Gate

Codex 可以读懂项目规则、执行 Runner、保存结果、分析失败，并在修改后重新跑回归。

但这里有一个边界：Skill 是流程约束，不是业务真理。

它可以提醒 Codex“必须评估”，却不能替业务方决定“候选人是否应该被录用”。

![Article image](/assets/2026-09-07-我把-eval-装进-codex-后，ai-coding-的工作方式变了-0fbef2579a/06.jpg)

## 9. 有一件事我不会完全交给 AI：Ground Truth

我不会接受这样的闭环：

AI 自己出题

→ AI 自己写标准答案

→ AI 自己评分

→ AI 宣布自己 98 分

Codex 可以帮忙生成候选 Cases，可以写 Eval Runner，可以写 Judge，可以分析 Failure。

但高风险业务的正确性，必须保留人工确认。

特别是招聘、医疗、法律、金融、客户准入这类任务，标准答案不能从模型直觉里推出来。

我会把案例分成几种状态：

- human_verified：已经由业务专家确认

- source_verified：由明确资料或政策确认

- synthetic_unverified：模型或程序生成，尚未确认

- needs_human_review：存在争议，需要人工决定

只有经过必要审核的案例，才适合进入长期 Golden Set 或 Regression Set。

AI 可以帮我造题、写阅卷器、找错题，但不能替我定义业务真相。

## 10. AI Coding 越强，Eval 为什么反而越重要？

Build 正在变便宜。

以前一个人要花几天写出来的功能，现在可能只需要几轮对话。

这会带来一个变化：人越来越不应该只盯着“怎么写代码”。

人更应该掌握两个问题：

What should be built？What does good look like？

Codex 解决“怎么做”。

Eval 解决“做得怎么样”。

人最终负责定义：什么才叫好。

如果没有这层定义，AI Coding 只是更快地产生代码；有了它，才可能更快地产生可交付的系统。

![Article image](/assets/2026-09-07-我把-eval-装进-codex-后，ai-coding-的工作方式变了-0fbef2579a/07.jpg)

## 11. 我现在用 Codex 的方式已经变了

以前我会说：

帮我把这个做好。

现在我会这样开始一个 AI Coding 任务：

这是我的业务目标。

先检查现有 Eval、Golden Set、Rubric 和历史失败。

先跑 Baseline，不要先改代码。

找出影响最大、风险可控的失败来源。

做最小必要修改。

然后完整跑 Tests + Eval + Regression。

输出 Improved、Regressed、Unchanged、New Failures。

没过 Release Gate 就继续修，不要宣布 Done。

这不是把更多工作推给 Codex，而是把“完成”定义清楚以后，让 Codex 获得更大的自主空间。

它不需要猜我想要什么，而是沿着明确的质量系统自己 Build、自己 Eval、自己修、自己重新验证。

## 结尾：从让 AI 写代码，到给 AI 定义验收标准

以前我让 AI 帮我写代码。

现在我开始给 AI 定义验收标准。

这可能是 AI Coding 真正成熟的分水岭。

不是谁能让 Codex 一次写出最多代码，而是谁能把目标、证据、失败和上线标准组织成一个闭环。

Codex 解决“怎么做”。

Eval 解决“做得怎么样”。

人最终负责定义：什么才叫好。

AI Coding 的价值，不只是让 AI 写更多代码。

而是让 AI 在一个明确的质量系统里，自主完成工程。
