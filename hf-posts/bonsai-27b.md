# Agentic coding test: Bonsai-27B Q1_0 — degeneration, unsuitable for code at this quant

Part of a **comparison of five local models** run as autonomous coding agents. Overview with the full
matrix: {{OVERVIEW_URL}}

Russian version of the full report: https://github.com/MR1KRAKEN/local-llm-agent-battle-tests (`ru/` folder).

> Testing was carried out under the supervision of **DeepSeek-V4.1-Flash** (DSH orchestrator).
> It started the server, assigned the task, ran the checks and collected the metrics.

## Verdict

**No successful build, then degeneration.** This is expected: the model is a vision model by design, and
Q1_0 is extreme quantization (about 1 bit per weight). It was excluded from the refinement stage by the
stand owner's decision.

## Runs

| Stage | Metric | Value |
| :--- | :--- | ---: |
| One-shot harness | steps / successful builds | 11 / 0 of 1 |
| One-shot harness | speed / time | 72.1 tok/s / 5 min |
| Agent run | time before stop | 610 s (interrupted by the orchestrator) |
| Agent run | steps | 7 |
| Agent run | builds (successful / total) | 0 / 2 |
| Agent run | prompt / completion tokens | 54,654 / 13,274 |
| Agent run | TTFT / speed | 7.74 s / 55.55 tok/s |
| Agent run | VRAM peak | 9,133 MiB |
| Agent run | exe | none |

## What exactly broke

**Compiler errors (both builds):** `CS0103` (name does not exist), `CS0117` (type has no such member),
`CS0123` (no overload matches the delegate), `CS0246` (type not found), `CS1061` (no such member),
`CS1503` (cannot convert argument), `CS1729` (no constructor with those arguments), plus warning `CS8632`
(nullability annotation outside a `#nullable` context).

**Degeneration.** After two failed builds the model started an answer that never ended: the llama.cpp log
showed the generated-token counter reaching **15,574** against `defaultMaxTokens: 8192`, running for about
ten minutes at ~53 tok/s. Files did not change during that time. The orchestrator interrupted the run
manually — the model did not leave the loop on its own.

## Takeaway

- Error style matches other small-class models: invented API members, lost `using` directives,
  non-existent constructors. The difference is that this model made no attempt to fix them.
- Q1_0 visibly degrades answer coherence: slow TTFT (7.74 s) and long answers without progress.
- Practical lesson for local setups: **a hard per-step token limit is necessary**, otherwise one response
  can consume the whole session.
- For vision tasks (the model ships with `mmproj`) these tests say nothing — they are about code generation.
