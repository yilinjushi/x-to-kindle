---
url: "https://x.com/freeman1266/status/2066677040238227843"
title: "最小 Loop：让 Claude 自己跑测试、修 Bug"
author: "老金 @freeman1266"
source: "x_bookmark"
date: 2026-09-08
chars: 1830
images: 3
---

# 最小 Loop：让 Claude 自己跑测试、修 Bug

我之前有一段时间，每天晚上的工作流程大概是这样的：

让 Claude 写代码 → 跑测试 → 3 个失败 → 把报错粘贴给 Claude → 它修了一个、又破了另一个 → 再粘贴 → 再修 → 再破……

一个晚上就这么过去了。

我当时以为这是正常的，是 AI 编码的"代价"。后来我才意识到，这个流程里我做的事情是纯机械的——Claude 写代码，我跑测试，我读错误，我再粘给 Claude。我就是个 USB 线。这完全可以被自动化掉，只需要 3 个文件。

## 先说清楚问题在哪

默认的 Claude Code 工作方式是一条直线：你发任务 → Claude 写代码 → Claude 停下来 → 等你

它不会主动跑测试。"完成"在它的默认定义里就是"写完了"。

要解决这个问题，把直线弯成循环：写代码 → 跑检查 → 有失败？修它 → 再跑检查 → 直到通过

![Article image](/assets/2026-09-08-最小-loop：让-claude-自己跑测试、修-bug-a54dab4092/01.jpg)

## CLAUDE.md——重新定义"完成"

在项目根目录的 CLAUDE.md 里加入循环协议：

循环协议
每个任务作为循环运行，不是直线：
1. 写变更。
2. 运行检查：测试 + linter + 类型检查。
3. 有失败？读错误，找原因，修它，回到第 2 步。
4. 最多循环 5 次。

停止条件：
· 所有检查通过 → 报告"完成"，附上通过输出作为证明。
· 5 次用完 → 停下来，报告还剩什么没过。
· 同一个错误连续出现两次 → 立刻停。你在猜，不是在修。

禁止：在没有检查输出的情况下报告"完成"。
禁止：通过删断言、弱化测试来让测试通过。修代码，不修记分牌。

最后两条"禁止"是整个配置里最关键的部分。我第一次没加，结果 Claude 在第 3 次迭代里把一个断言直接删掉了——测试绿了，bug 还在。它在作弊，而且作弊得很自然。

## .claude/settings.json——光靠协议不够

Claude 会"忘记"CLAUDE.md 里写的协议。settings.json 的钩子是硬约束：每次它想停下来，系统强制先跑一遍测试，把结果塞回给它。

![Article image](/assets/2026-09-08-最小-loop：让-claude-自己跑测试、修-bug-a54dab4092/02.jpg)

{
  "hooks": {
    "Stop": [{ "hooks": [{ "type": "command", "command": "npm test --silent 2>&1 | tail -20" }] }],
    "PostToolUse": [{ "matcher": "Write|Edit", "hooks": [{ "type": "command", "command": "npx tsc --noEmit --pretty false 2>&1 | head -10" }] }]
  }
}

- PostToolUse：每次改完文件立刻跑类型检查，边写边纠。

- Stop：Claude 想说"完成了"的时候，先跑完整测试套件。失败了？输出直接进会话，强制再来一次。

Python 换 pytest -q + pyright，Rust 换 cargo test --quiet + cargo check。

## .claude/agents/fixer.md——处理死局

有些问题在同一个上下文窗口里修不好。它已经试了 4 次，上下文里全是失败记录，思路被锁死了。这时候需要一个干净的上下文：

![Article image](/assets/2026-09-08-最小-loop：让-claude-自己跑测试、修-bug-a54dab4092/03.jpg)

name: fixer
description: 当同一个测试在 2 次修复尝试后仍然失败时调用。
tools: Read, Edit, Grep, Glob, Bash
model: opus

你修复失败的检查。你不允许猜测。

1. 自己运行失败的检查，读完整错误。
2. 从头到尾读失败路径里的每个文件。
3. 写一句话：实际原因是什么。
4. 只修那个原因，不要顺手重构。
5. 再次运行检查，报告修复前后的输出。

禁止：删测试、放宽断言、用 try/catch 压错误、把测试标记为 skip。

主会话里用 @fixer 调用。它没有之前 4 次失败的记忆，重新从零诊断，经常一次就过。

## 配起来

把循环协议贴进 CLAUDE.md，创建 .claude/settings.json 放钩子配置，再建一个 .claude/agents/fixer.md。给 Claude 一个真实任务，看循环跑起来。

配置完之后你会发现，你不再需要盯着终端复制粘贴报错了。Claude 自己跑、自己看、自己修，修不动了叫 fixer。你只需要最后看一眼 diff。
