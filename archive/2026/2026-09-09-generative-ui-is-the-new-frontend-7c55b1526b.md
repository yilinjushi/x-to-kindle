---
url: "https://x.com/Saboo_Shubham_/status/2062220865643982875"
title: "Generative UI Is the New Frontend"
author: "Shubham Saboo @Saboo_Shubham_"
source: "x_bookmark"
date: 2026-09-09
chars: 14599
images: 6
---

# Generative UI Is the New Frontend

The frontend used to be a fixed thing. Designers drew it. Engineers built it. Users got what shipped.

That's over.

The interfaces shipping in 2026 are drawn partly by the agent itself, in real time, from what the user actually asked for. Ask for a table, get a table. Not a paragraph describing one.

Generative UI is the layer that lets agents stop describing and start showing. Three patterns have emerged for how to build it, and the differences between them matter more than most teams realize.

But there isn't one way to build this. There are three. And most teams pick one without knowing they chose.

## The protocol stack

Three protocols. Each does one job.

MCP connects agents to tools. A2A connects agents to each other. AG-UI connects agents to users.

AG-UI is the streaming layer that carries everything you'll see below: tool calls, A2UI schemas, MCP App events, state deltas. Runs over SSE. State flows both ways on the same stream. User edits, agent sees. Agent mutates, user sees.

A2UI is Google's spec for agents emitting UI as schema. It rides on AG-UI. CopilotKit ships it in production.

You don't write a parser for any of this. CopilotKit is an AG-UI client and decodes the stream for you.

## The three patterns most teams confuse

Ask ten developers what Generative UI is. You get ten answers. Most of them are describing whichever pattern their current framework ships.

There are just three. The spectrum runs from more control to more flexibility.

- Controlled: You pre-build the components. The agent picks which to render.

- Declarative: The agent emits a schema. Your app maps it to components.

- Open-ended: The agent writes raw HTML. Your app renders it in a sandbox.

![Article image](/assets/2026-09-09-generative-ui-is-the-new-frontend-7c55b1526b/01.jpg)

Every Gen UI framework in 2026 lives somewhere on this line. The differences are architectural, not cosmetic. Each pattern breaks your app in a different way at scale.

I tried different stacks. Most cover one pattern well. Landed on CopilotKit because it supports all three on the same runtime, riding AG-UI. That's the stack everything below runs on.

## Pattern 1: Controlled, frontend owns the UI

![Article image](/assets/2026-09-09-generative-ui-is-the-new-frontend-7c55b1526b/02.jpg)

This is where most teams start. It's also where most teams get stuck.

You pre-build a React component. You bind it to a tool name. The agent picks that tool and the component renders inline in chat with the agent's args as props.

One frontend hook. Zero agent code. That's it.

typescript
"use client";
import { z } from "zod";
import { useComponent } from "@copilotkit/react-core/v2";

const expenseChartSchema = z.object({
  title: z.string(),
  data: z.array(z.object({ label: z.string(), value: z.number() })),
});

function ExpenseChart({ title, data }: z.infer<typeof expenseChartSchema>) {
  return (
    <section className="rounded-xl border p-4">
      <h3 className="text-sm font-medium">{title}</h3>
      <ul className="mt-2 grid gap-1">
        {data.map((d) => (
          <li key={d.label} className="flex justify-between text-sm">
            <span>{d.label}</span>
            <span>${d.value}</span>
          </li>
        ))}
      </ul>
    </section>
  );
}

export function ExpensesCopilot() {
  useComponent({
    name: "showExpenseChart",
    description: "Render a breakdown of expenses by category.",
    parameters: expenseChartSchema,
    render: ExpenseChart,
  });

  return null;
}

The hook registers the tool with CopilotKit's runtime. The runtime advertises it to the agent over AG-UI. When the agent calls it, the args stream in and your component renders inline. No Python tool to write, no schema to wire, no API route to add.

Your design system stays in charge.

That expense chart isn't a mockup. The AI Financial Coach Agent renders cards just like it for real budgets, savings plans, and debt payoff.

The media could not be played.
Reload

Want the bare hook first? It's 'use-generative-ui-examples.tsx' in the Generative UI Starter Project.

The token tax

Every component you register sits in the agent's context window before the user has said anything. A typical tool description with its JSON schema runs around 400 tokens. 25 components are 10,000 tokens on every turn. You pay that tax per request.

The agent picks the wrong component too. Too many look similar. Pie chart and donut chart both "show proportions." It guesses.

When to add agent-side state

Shared state is the one case where writing a Python tool is worth it. The agent writes to session state. Other parts of the UI subscribe and re-render with no second LLM call. Pin a metric, the dashboard updates. Add a row, the table redraws.

python
from google.adk.agents import LlmAgent
from google.adk.tools import ToolContext

def pin_metric(tool_context: ToolContext, label: str, value: float) -> dict:
    """Pin a metric to the user's dashboard."""
    pinned = tool_context.state.get("pinnedMetrics", [])
    tool_context.state["pinnedMetrics"] = pinned + [{"label": label, "value": value}]
    return {"status": "pinned"}

agent = LlmAgent(name="dashboard_agent", model="gemini-3.5-flash", tools=[pin_metric])

The frontend reads pinned metrics through CopilotKit's shared-state hook. The chat component still renders inline because the same tool name is wired with the frontend hook.

Pin a metric in chat. The panel redraws with no second model call. That's the AI Dashboard Canvas Agent.

The media could not be played.
Reload

The AI Deep Research Agent takes it further. The plan, every search, each file write, all of it streams in as live cards. For everything else, the frontend hook is the whole story.

The media could not be played.
Reload

When to ship Controlled: Ten or fewer high-value flows. Design precision matters. You know the exact UIs you need.

When not to: Your codebase grows linearly with use cases. 25 components means 25 tool definitions sitting in every agent turn.

What breaks: Agent picks the wrong component. Two tool descriptions overlap semantically. Past 15 tools, two of them probably read like "displays data." Fix: rewrite descriptions to name the user intent, not the visual. "Use when the user asks to compare proportions of a whole" beats "renders a pie chart."

## Pattern 2: Declarative (A2UI), agent emits schema

![Article image](/assets/2026-09-09-generative-ui-is-the-new-frontend-7c55b1526b/03.jpg)

This is the pattern most production agent apps end up needing.

The agent emits a JSON schema describing the UI. Your app has a catalog of components that maps schema nodes to React (or Svelte, Flutter, anything). One tool. Many UIs.

A2UI is the standard spec. CopilotKit ships the runtime. ADK runs the agent. AG-UI is the wire.

The agent tool returns three operations in order: create a surface, push the component tree, push the data.

python
def search_flights(flights: list[Flight]) -> dict[str, Any]:
    """Search flights and display them as rich cards."""
    return {
        "a2ui_operations": [
            {"type": "create_surface", "surfaceId": SURFACE_ID, "catalogId": CATALOG_ID},
            {"type": "update_components", "surfaceId": SURFACE_ID, "components": FLIGHT_SCHEMA},
            {"type": "update_data_model", "surfaceId": SURFACE_ID, "data": {"flights": flights}},
        ]
    }

This is the actual function, not pseudocode. The runtime middleware sees the a2ui_operations container in the tool result and forwards surfaces to the frontend. Adding hotels? New schema file. One more function with a different surface ID. Zero extra frontend work.

Fixed schema vs dynamic schema

The component tree above lives in flights.json. You wrote it. The agent only fills in the data. That's a fixed schema.

Dynamic schema flips it: a secondary LLM writes the component tree per turn from conversation context. Same a2ui_operations container at the end. The Google ADK showcase ships both.

The catalog is the contract

Definitions list the components the agent is allowed to emit, with Zod schemas for the props. Renderers fill in React. Typos become build errors instead of blank screens.

typescript
const renderers: CatalogRenderers<TravelDefinitions> = {
  FlightCard: ({ props }) => (
    <article className="rounded-xl border p-4">
      <header className="flex justify-between">
        <span>{(props as any).airline}</span>
        <span>{(props as any).price}</span>
      </header>
      <div className="text-sm text-muted-foreground">
        {(props as any).origin} → {(props as any).destination} · {(props as any).departureTime}
      </div>
    </article>
  ),
};

export const travelCatalog = createCatalog(travelDefinitions, renderers, {
  catalogId: "copilotkit://travel-catalog",
  includeBasicCatalog: true,
});

Both halves live in the Generative UI Starter Project, wired and matched. search_flights in 'a2ui_fixed_schema.py', the FlightCard catalog in 'renderers.tsx'. Ask for flights. Watch the cards stream into chat.

The media could not be played.
Reload

Buttons and other interactive components carry an action in the schema. The basic catalog wires it to onClick. Click fires an event back to the agent over AG-UI. The agent decides what to render next. Zero click handlers.

The token math

50 card types or 500, the agent sees one function. Tokens per turn stay flat as your component library grows.

Extensible to any rendering framework because it's just JSON. Any agent that already speaks AG-UI can drive A2UI on day zero. You don't touch agent code to wire this up.

Trade-off: The LLM owns the layout. Output varies run to run within your catalog. If you're shipping legal disclosures, marketing surfaces, or anything where exact pixel placement matters, this is not your bucket.

Declarative is the pattern built for the long tail. Dashboards, results, forms, cards, widgets.

When to ship Declarative: You have more use cases than time to pre-build. You care about token economics past the prototype stage.

What breaks: Built a custom FlightCard. Every flight renders as the basic catalog's generic card. No error in the console. The CATALOG_ID on the agent and catalogId in createCatalog on the frontend don't match. Frontend doesn't recognize the catalog the agent is targeting, falls back to basic. Match the strings exactly on both sides.

## Pattern 3: Open-ended, no catalog, no rules

![Article image](/assets/2026-09-09-generative-ui-is-the-new-frontend-7c55b1526b/04.jpg)

The third pattern is the opposite extreme. No catalog. No schema. Just a blank canvas.

Two sub-patterns live in this bucket.

MCP Apps

An MCP server exposes UI surfaces that the agent drives. Excalidraw is the example that stuck with me. The agent gets full control of the canvas. Draws diagrams from your context. Owns every pixel on the board.

![Article image](/assets/2026-09-09-generative-ui-is-the-new-frontend-7c55b1526b/05.jpg)

Implementing the client protocol from scratch is painful, so CopilotKit ships an MCPAppsMiddleware. Attach it to your agent and point it at any MCP Apps server.

typescript
const agent = new BuiltInAgent({
  model: "openai/gpt-5.5",
  prompt: "You are a helpful assistant.",
}).use(
  new MCPAppsMiddleware({
    mcpServers: [{ type: "http", url: "https://mcp.excalidraw.com/mcp", serverId: "my-server" }],
  }),
);

Spin up the MCP Apps Showcase and you're booking flights and reserving hotels inside the chat window. Same middleware, real MCP servers. Or go further.

The AI MCP App Builder lets the agent write a brand-new app into an E2B sandbox, then renders it live.

The media could not be played.
Reload

Sandboxed HTML

The agent writes raw HTML. Your app renders it inside a sandboxed iframe so it can't hijack the session.

The runtime registers an HTML rendering tool and ships it to the agent over AG-UI. The agent calls it with whatever markup it wants. There is no HTML tool to define on the agent side. The runtime injects it.

Agent-side instruction is doing real work:

python
canvas_agent = LlmAgent(
    name="canvas_agent",
    model="gemini-3.5-flash",
    instruction=(
        "You are a visualization assistant. When the user asks to see, "
        "draw, or visualize anything, generate an interactive HTML UI. "
        "Use Tailwind classes only. No external fonts. Stick to neutral "
        "colors unless the user names one."
    ),
)

Without those style rules, the model defaults to whatever aesthetic was loudest in its training data that week. With them, you get something close to your brand most of the time. Not always.

The brand inconsistency problem

I tried shipping Open-ended as the primary UI for an agent. Pulled it in a week.

"Neo-brutalist" on Tuesday. "iOS 4 clone" on Wednesday. Style rules in the prompt nudge the agent toward your brand. They don't guarantee it. The brand kept changing. The product felt unserious.

![Article image](/assets/2026-09-09-generative-ui-is-the-new-frontend-7c55b1526b/06.jpg)

Open-ended isn't useless. It's misapplied.

Right call for one thing: throwaway interactions where the user doesn't care what the interface looks like and will never see it again. "Show me how electrons work." "Give me a weird bar chart of my last 10 queries." "Visualize this API response." The kind of thing you see in Google AI overviews.

When to ship Open-ended: One-shot queries. Disposable visualizations. Sandboxed experiments. Never as the primary surface.

What breaks: The iframe renders. Buttons don't click. Forms don't submit. Sandbox flags are too tight, or too loose in a way the browser refuses. Set the iframe sandbox to allow scripts and allow forms. Nothing else. Never allow-same-origin.

## How to pick

Run the decision tree before you write code.

Designer has pixel-perfect mockups for this flow? Controlled.

Dozens of card types or widgets to ship? Declarative.

One-shot, throwaway visualization the user will never see twice? Open-ended.

Can't decide? Default to Declarative. Upgrade to Controlled for the top 3 flows. Never Open-ended as the default.

If you're already shipping and not sure where you landed, count the render tools. Past 15, you're in Controlled and the wall is close. Start wiring A2UI this week.

## Three patterns. Three bets.

Controlled bets on you. Pre-built components, pixel-perfect. Expensive past 25 of them.

Declarative bets on the schema. The schema is the contract. The agent fills it in. Scales flat.

Open-ended bets on the model. No catalog, no schema, raw HTML. Good for throwaway. Brittle for anything that ships twice.

The mistake isn't picking the wrong pattern. It's not knowing you picked one.

Most teams default to Controlled because the framework defaults to Controlled. They hit the wall at 25 components and reach for Open-ended because it looks compelling in demos. Neither was a decision. Both were drift.

Pick on purpose. Match the pattern to the problem. Controlled for the flows that need to be exact. Declarative for the long tail. Open-ended for the disposable.

Open Source Generative UI Agent Templates

The reference for all three lives in the new Generative UI Agents section of awesome-llm-apps. Clone what you need. Rip out what you don't.

I'll be publishing more about shipping agents in production, AG-UI, and the patterns that scale. Follow me @Saboo_Shubham_ to stay tuned.
