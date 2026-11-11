# Agentic coding test: LFM2-24B-A2B Q4_K_M — blocked by the integration, not by the model

Part of a **comparison of five local models** run as autonomous coding agents. Overview with the full
matrix: {{OVERVIEW_URL}}

Russian version of the full report: https://github.com/MR1KRAKEN/local-llm-agent-battle-tests (`ru/` folder).

> Testing was carried out under the supervision of **DeepSeek-V4.1-Flash** (DSH orchestrator).
> It started the server, assigned the task, ran the checks and collected the metrics.

## Verdict: not evaluated — and this is important to be precise about

The model performed **zero actions**: no files created, no build attempted, no console tasks. The task
stayed unsolved because the tool call never reached the harness. This is **not** evidence about the model's
coding ability.

## What happened

| Run | Behaviour |
| :--- | :--- |
| One-shot harness | 2 steps, 26 s, nothing done |
| Agent (DSH + llama.cpp) | emitted the tool call **as plain text**: `<function=execute_powershell>` with parameters inside — the harness cannot execute that |
| Retry with explicit format instruction | followed it and printed `{"name": "create_goal", "arguments": {...}}` — again as text, and with the wrong tool (`create_goal` instead of `write`) |

It also tried to write outside its working folder — it addressed a path on the user's Desktop instead of
its own session directory.

## What was established about the cause

Direct requests to llama.cpp (`POST /v1/chat/completions` with the `tools` field):

| Number of tools | Server response |
| ---: | :--- |
| 1 | `finish_reason: tool_calls`, valid JSON |
| 4 | `tool_calls` |
| 8 | `tool_calls` |
| 20 | `tool_calls` |
| 32 (real DSH tool names: `read`, `write`, `pwsh`, …) | `tool_calls` |

**So the model does emit native tool calls and llama.cpp parses them.** "Cannot do tool calling" is not the
correct explanation.

The prompt was **not truncated**: the agent runs sent 13,680 and 12,724 input tokens against a 65,536
window (~20%), measured from session `usage`. Enlarging the context or memory budget changes nothing.

The remaining hypothesis, not yet confirmed, is that the LFM2 chat template renders tools into the system
prompt as a JSON list and in the real agent run the model prefers a textual format. Confirming it needs
request-body logging on the harness side.

## Takeaway

- For tool-calling agents in this llama.cpp stack, the model is unusable in this configuration.
- For ordinary chat and single-response code generation these results say **nothing**.
- Indirect signal: it picked a non-existent tool name out of a 32-item list, so orientation in a large tool
  set is weak.
