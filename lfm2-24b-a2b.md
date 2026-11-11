# LFM2-24B-A2B (Q4_K_M) — Test as a DSH Agent

**Languages:** English (this file) · [Русская версия](ru/lfm2-24b-a2b.md)

**Weights:** [lmstudio-community/LFM2-24B-A2B-GGUF](https://huggingface.co/lmstudio-community/LFM2-24B-A2B-GGUF)
— `LFM2-24B-A2B-Q4_K_M.gguf`, 14,415,473,952 bytes (13.43 GiB), MoE ~24B total / ~2B active
**Runtime:** llama.cpp (`local-llama`), ctx 65,536, `--jinja`
**Date:** 11 November 2026

> Testing was carried out under the supervision of **DeepSeek-V4.1-Flash** (DSH orchestrator,
> provider `deepseek-account`, model id `deepseek-flash`).

## Summary

**Verdict: ⏱ not evaluated — the failure belongs to the integration, not to the model.**
The model performed zero actions: it created no files, ran no build, and never reached the console tasks.
The task stayed unsolved because the tool call never reached the harness.

## What happened

| Run | Behaviour | Outcome |
| :--- | :--- | :--- |
| One-shot harness (earlier stage) | 2 steps, 26 s, nothing done | no result |
| DSH agent | emitted a tool call **as plain text**: `<function=execute_powershell>` with parameters inside | the harness could not execute it |
| Retry with an explicit instruction ("output exactly a JSON object `{"name": ..., "arguments": ...}`") | the instruction was **followed**: it printed `{"name": "create_goal", "arguments": {...}}` — but as text again, and with the wrong tool (`create_goal` instead of `write`) | call still not recognised |

Additionally, the model tried to write outside the working folder — it addressed a path under the user's
Desktop instead of its own session directory, so it did not stay inside its `cwd`.

## What was established about the cause

Direct requests to llama.cpp (`POST /v1/chat/completions` with the `tools` field) were used to test the model
in isolation:

| Number of tools | Server response |
| ---: | :--- |
| 1 | `finish_reason: tool_calls`, valid JSON arguments |
| 4 | `tool_calls` |
| 8 | `tool_calls` |
| 20 | `tool_calls` |
| 32 (real DSH tool names: `read`, `write`, `pwsh`, …) | `tool_calls` |

So **the model does emit native tool calls**, and llama.cpp parses them. "The model cannot do tool calling"
is not the correct explanation.

The prompt was **not truncated**: the two agent runs sent 13,680 and 12,724 input tokens against a
65,536 window — about 20%. Enlarging the context or the memory budget therefore changes nothing;
this was measured from `usage` in the session logs.

The remaining hypothesis (not yet confirmed, it needs request-body logging on the DSH side) is that the
LFM2 chat template renders tools into the system prompt as a JSON list, and in the real agent run the model
prefers a textual format over the native one.

## What this means for users

- For agentic tasks that require tool calling in the **DSH + llama.cpp** combination, the model is unusable
  in this configuration.
- For ordinary chat and single-response code generation these results say **nothing** — it did not fail
  the task, it never started it.
- An indirect signal: the model picked a non-existent tool (`create_goal`) out of a 32-item list, so its
  orientation in a large tool set is weak.

---

Post your own results in the model discussions:
[lmstudio-community/LFM2-24B-A2B-GGUF/discussions](https://huggingface.co/lmstudio-community/LFM2-24B-A2B-GGUF/discussions)
