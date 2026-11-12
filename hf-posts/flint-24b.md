# Agentic coding test: flint-24B Q4_K_M — fast, but thinks more than it does

Part of a comparison of local models run as autonomous coding agents. Overview with the full matrix:
{{OVERVIEW_URL}}

Full reports (English + Russian): https://github.com/MR1KRAKEN/local-llm-agent-battle-tests

> Testing was carried out under the supervision of **DeepSeek-V4.1-Flash** (DSH orchestrator). It started the
> server, assigned the task, ran the checks and collected the metrics. It did not write or fix model code.

## Setup

- Weights: this repository's `flint-Q4_K_M.gguf`, 22.5 GiB, MoE 256 experts / 6 active per token
- Runtime: llama.cpp CUDA `b12248`, `--jinja`, KV cache q8_0, `-np 1`
- Hardware: Ryzen 7 9800X3D, 64 GB DDR5, **RTX 4070 Ti 12 GB**
- Task: write a C#/WinForms calculator (.NET 8), build it, publish a single-file exe. Identical prompt for
  every model in the comparison.

## Speed: genuinely good

| Measurement | Value |
| :--- | ---: |
| Plain generation | **49.9 tok/s** |
| Long runs, 128K context | **55.3 tok/s** |
| Short bursts | **62.7 tok/s** |

For comparison, the fastest model in the main battle was Qwen3.5-9B at 69.7 tok/s, and Nemotron-30B at
60.6 tok/s — flint sits right between them while carrying a 22.5 GiB file instead of 5.2 and 17.6. The MoE
sparsity absolutely pays off. Tool calls through the API also work correctly (1.8 s per call).

## As an agent: no build at any reasoning budget

Four configurations, all with the same minimal prompt:

| `--reasoning-budget` | Outcome |
| :--- | :--- |
| `0` (off) | wrote both files, then **28 edits in a row** failing with `old_string was not found`; no build |
| `6000` + "Stop analysing. Call the tool now." | **12 rewrites of `Program.cs`**: full 6 283-character writes alternating with 116- and 12-character stubs; no build |
| `16384` | **16 263 tokens spent reasoning** (279 s), file never completed |
| `32768` | **32 771 tokens spent reasoning** (593 s), **zero tool calls** |

The last row is the decisive one: 128K context, 40K output limit, 32K reasoning budget, and the model spent
every token it was allowed on deliberation without making a single tool call.

## Why the budget does not save it

`--reasoning-budget N` is enforced server-side: when the counter is exhausted, llama.cpp injects the
end-of-thinking token and the model must start answering. The model does not know this is happening.

There is a side effect that makes low budgets worse rather than better: the cut can land **inside a tool
call** and truncate its arguments. That is exactly the 6 000-token run above — full writes alternating with
12-character stubs, the model rewriting the file again and again because each truncated write left it empty.

`--reasoning-budget-message` steers the model well ("Stop analysing. Call the tool now."), but does not
prevent the truncation.

## Code quality, checked with the compiler

| Finding | Detail |
| :--- | :--- |
| `CS1513` | the file ends at line 217 with the class and namespace unclosed |
| Latent `CS1729` | `new Font("Segoe UI", 10, FontStyle.Regular, GraphicsUnit.Point, 10, false, false, false, false)` — **9 arguments**, while `System.Drawing.Font` only has constructors taking 2 to 6 (verified by reflection) |
| Locale bug | `result.ToString()` without invariant culture — decimal comma instead of point |

What it got **right** is worth noting, because these are the traps other models fell into:

- `Keys.Oemplus` with the correct lower-case `p` (Nemotron used `OemPlus` and failed to compile);
- **no `base.OnKeyDown` call** from its own `KeyDown` handler — the recursion that crashed Nemotron's
  calculator.

So the API knowledge is there. The discipline is not: tens of thousands of reasoning tokens, then two
missing braces.

## Matches what others report

In the thread [“Flint can now run in llama.cpp and Unsloth Desktop!”](https://huggingface.co/unsloth/flint-GGUF/discussions/3)
people describe the same behaviour: *"It just thinks and thinks and thinks lol. Not really usefull"*,
*"20K+ reasoning tokens before it wrote any code"*, *"it's fast but not too smart"*. One person found
`reasoning-budget = 20000` workable; at 32 768 in this harness it still produced nothing, so the difference
is probably task shape rather than the budget alone.

A speed reference from that thread: 49 tok/s on an RX 7800 XT (Vulkan, Q4_K_XL) — consistent with our
55–62 tok/s on an RTX 4070 Ti.

## Template note

The original template contains `| replace("\x00", "")`. Older llama.cpp builds and LM Studio failed on it
with `Failed to parse Jinja template: Unexpected escaped character: x`. Fixed by
[PR #30929](https://github.com/ggml-org/llama.cpp/pull/30929) and
[PR #30928](https://github.com/ggml-org/llama.cpp/pull/30928), both merged 2026-10-21. Our build includes
them, so no template error occurred here.

## Verdict

**Excellent raw generation speed, not usable as an agent under a per-step token ceiling.**

Good uses: one-shot code snippets, explanations, drafting. Bad uses: autonomous multi-step work where the
clock and the token budget matter. With a real MoE advantage on a 12 GB card it is a genuinely interesting
model — just wire it for generation, not for agent loops.

Reproduce:

```powershell
llama-server -m flint-Q4_K_M.gguf --host 127.0.0.1 --port 8090 --alias flint-24b-64k `
  -c 131072 -fa on -ctk q8_0 -ctv q8_0 --jinja -np 1 `
  --reasoning-format deepseek --reasoning-budget 32768 --no-webui
```
