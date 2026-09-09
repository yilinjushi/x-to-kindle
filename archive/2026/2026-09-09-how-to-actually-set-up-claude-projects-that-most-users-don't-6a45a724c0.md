---
url: "https://x.com/eng_khairallah1/status/2063186252606865711"
title: "How to Actually Set Up Claude Projects That Most Users Don't Know"
author: "Khairallah AL-Awady @eng_khairallah1"
source: "x_bookmark"
date: 2026-09-09
chars: 12207
images: 0
---

# How to Actually Set Up Claude Projects That Most Users Don't Know

Most people treat Claude Projects like a folder with a label on it.

They create a project. They give it a name. Maybe they write a sentence or two in the system prompt. Maybe they upload a file. Then they start chatting and wonder why the output feels the same as regular Claude.

That is not a project. That is a labeled chatbox.

The people getting insane results from Claude Projects are building something completely different. They are building customized AI employees. Each project is tuned so precisely that Claude knows their voice, their standards, their audience, their workflow, and their exact definition of "good output" before they type a single word.

I spent three weeks testing every possible project configuration. Different system prompts. Different knowledge file combinations. Different organizational structures. I rebuilt the same project twelve times until the output was consistently excellent with minimal prompting.

Here is the exact blueprint that works.

## Why Most Claude Projects Fail

There are three reasons most people's projects produce mediocre output.

Reason 1: The system prompt is too vague.

"You are a helpful writing assistant" is not a system prompt. It is a wasted opportunity. Claude already knows how to be helpful. What it does not know is your specific voice, your audience, your formatting rules, your quality bar, and the fifteen things you hate seeing in an output.

Reason 2: There are no knowledge files uploaded.

A project without knowledge files is just a labeled conversation. The entire point of a project is that Claude has persistent access to reference documents that shape every single response. If you are not uploading files, you are not using the feature.

Reason 3: The project tries to do everything.

One project called "Work Stuff" that handles emails, content, strategy, research, coding, and analysis will produce mediocre results across all of them. Separate your workflows into separate projects. Each one should do one thing extremely well.

# The 6-Part Project Blueprint

Every high-performing project has six components. Skip any of them and the output quality drops noticeably. I tested this by removing each component one at a time and measuring the difference in output quality. The drop was immediate every single time.

## Part 1: The Identity Block

This is the first thing in your system prompt. It tells Claude exactly who it is in this project.

Not "you are a helpful assistant." Something like this:

You are my senior content strategist and writer. You have been working with me for two years. You know my voice, my audience, and my quality standards intimately.

Your job in this project is to research, plan, draft, and edit long-form articles for my audience of 250,000 followers who are learning AI tools for the first time.

You are direct. You are specific. You never use filler. Every sentence earns its place or gets cut.

Why this works: Claude performs dramatically better when it has a clear identity. "You have been working with me for two years" creates a framing where Claude defaults to confident, specific output rather than generic safe output. The specificity of "250,000 followers who are learning AI tools" gives it a concrete audience to write for.

## Part 2: The Rules Block

This is the non-negotiable list of things Claude must always do and must never do in this project. This is the most important part of your system prompt by far.

ALWAYS:
- Use short paragraphs. Maximum 3 sentences per paragraph.
- Include specific numbers rather than vague claims. Never say "many" or "some." Give a number.
- Bold the key insight in every section so a skimmer can read just the bold text and get the core message.
- Open with a hook that creates a gap between what the reader thinks they know and what is actually true.
- End with a CTA that creates urgency without being salesy.

NEVER:
- Use the word "leverage" or "utilize" or "streamline"
- Start any sentence with "In today's" or "It's important to note"
- Use em dashes
- Write generic advice that could apply to anyone. Every point must be specific and actionable.
- Include disclaimers or hedging language like "it depends" without immediately following with the specific thing it depends on

Why this works: Rules are constraints. Constraints force Claude into a specific lane where it cannot default to its generic patterns. Every time you find yourself correcting Claude's output, that correction should become a rule. After a month of this, your rules list is a precision instrument.

## Part 3: The Process Block

This tells Claude exactly how to approach work in this project. Not what to produce but how to think.

PROCESS:
1. Before writing anything, spend your first paragraph thinking about what the reader already believes about this topic. Your opening must challenge that belief.
2. Outline the complete structure before writing any section. Share the outline with me for approval before proceeding.
3. Write the first draft in one pass without self-editing.
4. Review the draft against my Rules. Fix any violations.
5. Check every claim for a specific supporting number or example. Replace anything vague.
6. Read the entire piece as if you are a busy person scrolling on their phone. Cut anything that would make them stop reading.

Why this works: Without a process block, Claude jumps straight to generating output. With one, it follows a structured workflow that produces consistently higher-quality results. The "read as a busy person scrolling on their phone" instruction alone improved my content quality more than any other single line.

## Part 4: The Output Format Block

This defines exactly what the finished product looks like. Eliminate all guessing.

OUTPUT FORMAT:
- Title: [Number] + [Claude-Specific Topic] + [Exclusion Hook]
- Length: 2000-3500 words
- Structure: Bold contrast opener (2 paragraphs) > Context section > Numbered main content > Strong closing CTA
- Subheadings: Bold, written as hooks that make the reader want to read the section
- Closing: Italic line + bold italic line using the "most people will X / the ones who Y" dichotomy

Why this works: When Claude knows the exact format before it starts writing, it distributes its effort correctly. Without this, it front-loads detail in the early sections and rushes the ending. With it, every section gets proportional attention.

## Part 5: The Knowledge Files

This is where your project gets its real intelligence. Upload these files and Claude references them in every single conversation:

File 1: Style guide (REQUIRED)

A document showing your writing style. Include at least three examples of your best work. Claude pattern-matches against these examples to capture your voice. Without this file, Claude writes in its default style. With it, Claude writes in yours.

File 2: Audience profile (REQUIRED)

Who reads your content? What do they already know? What frustrates them? What are they trying to achieve? What level of technical depth do they want? Write this as a one-page persona document. Claude uses it to calibrate every piece of content.

File 3: Competitor analysis (RECOMMENDED)

What does the competition look like in your space? What topics have been covered to death? What angles are overused? Upload examples of content you want to be different from. Claude uses this to avoid generic takes.

File 4: Performance data (RECOMMENDED)

Which of your past pieces performed best? What titles got the most engagement? What topics resonated? Upload your metrics. Claude uses this data to make better strategic decisions about what to write and how to position it.

File 5: Template library (RECOMMENDED)

Your best-performing formats as reusable templates. Article structures. Email frameworks. Report layouts. Claude uses these as starting frameworks instead of inventing structure from scratch every time.

## Part 6: The Onboarding Message

This is the first message you send in a new conversation within the project. Think of it as the daily briefing you would give an employee.

Today we are working on [TASK].

Here is the context: [WHAT I NEED AND WHY]

Reference my style guide for voice. Reference my audience profile for targeting. Reference my performance data for strategic decisions.

Before starting, tell me:
1. What angle would make this stand out from what already exists?
2. What does the reader already believe that we can challenge?
3. What is the one-sentence hook?

Once I approve the angle, proceed with a full outline.

Why this works: This message activates all five knowledge files, sets the task context, and forces Claude to think strategically before writing. Without it, Claude starts generating immediately. With it, Claude plans first and executes better.

## The Complete System Prompt Template (Copy This)

Here is the full system prompt, assembled from all six parts. Copy it. Modify the details for your specific use case. Paste it into your project.

IDENTITY:
You are my [ROLE]. You have worked with me for two years. You know my voice, my audience, and my standards.

Your job in this project is to [PRIMARY FUNCTION] for [AUDIENCE DESCRIPTION].

You are [COMMUNICATION STYLE]. You never [ANTI-PATTERNS].

RULES:
ALWAYS:
- [Rule 1]
- [Rule 2]
- [Rule 3]
- [Rule 4]
- [Rule 5]

NEVER:
- [Anti-rule 1]
- [Anti-rule 2]
- [Anti-rule 3]
- [Anti-rule 4]

PROCESS:
1. [Step 1 - Think/Plan]
2. [Step 2 - Outline/Structure]
3. [Step 3 - Execute]
4. [Step 4 - Review against rules]
5. [Step 5 - Quality check]

OUTPUT FORMAT:
- Format: [EXACT FORMAT SPECIFICATION]
- Length: [WORD COUNT RANGE]
- Structure: [SECTION ORDER]
- Style: [SPECIFIC STYLE MARKERS]

# The 5 Projects Everyone Needs

You do not need twenty projects. You need five. Each one handles one core workflow.

Project 1: Content Production

System prompt defines your writing voice, audience, and content standards. Knowledge files include your style guide, best-performing pieces, audience persona, and content calendar.

Project 2: Research and Analysis

System prompt defines how you want research structured, what sources you trust, and what depth of analysis you expect. Knowledge files include your research methodology, past analyses as examples, and your evaluation criteria.

Project 3: Communication

System prompt defines your email and messaging style, your professional tone, and your relationship with different audiences (clients, team, leadership). Knowledge files include examples of great emails you have written and templates for common message types.

Project 4: Strategy and Planning

System prompt defines your business context, your goals, your constraints, and how you think about decisions. Knowledge files include your business plan, competitor data, market research, and strategic frameworks you use.

Project 5: Code and Technical Work

System prompt defines your tech stack, coding conventions, architecture preferences, and quality standards. Knowledge files include your CLAUDE.md content, architecture decision records, and code examples that show your preferred patterns.

## What Happens After You Set This Up

Here is what changes.

Before this setup: You type a detailed prompt. Claude gives you a decent response. You spend twenty minutes editing it to match your voice and standards. You do this five to ten times a day.

After this setup: You type a two-sentence task description. Claude gives you an output that already matches your voice, follows your rules, targets your audience, and hits your quality bar. You spend two minutes reviewing it. You do this five to ten times a day.

That is a 90% reduction in editing time across every single task you delegate to Claude.

The math is simple. If you use Claude for two hours a day and this saves you 60% of your editing and correction time, that is over an hour saved daily. Five hours per week. Over 250 hours per year.

That is six full work weeks of your life back. From a one-time setup that takes about forty-five minutes.

Most people will keep using Claude Projects as labeled chat windows and wonder why their results are average.

The ones who build their blueprint today will never prompt the old way again. And they will never understand how they worked without it.

Follow me @eng_khairallah1 for more AI courses, tools, and workflows. New content every week.

hope this was useful for you, Khairallah ❤️
