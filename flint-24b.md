# flint-24B (MoE) — fast, but thinks more than it does

**Model:** flint, [RecursiveSI/flint](https://huggingface.co/RecursiveSI/flint) weights,
[lmstudio-community/flint-GGUF](https://huggingface.co/lmstudio-community/flint-GGUF) Q4_K_M, 22.5 GiB
**Architecture:** MoE, 256 experts, 6 active per token, 49 blocks, native context 262 144
**Runtime:** llama.cpp CUDA `b12248`, `--jinja`, KV cache q8_0, draft-free
**Verdict:** excellent raw generation speed, **not usable as an agent** in this harness at any reasoning budget

## Summary

| Metric | Value |
| :--- | ---: |
| Generation speed (plain text) | **49.9 tok/s** |
| Generation speed (long runs, 128K ctx) | **55.3 tok/s** |
| Max speed observed | **62.7 tok/s** (short bursts) |
| Tool calls through the API | work correctly (1.8 s per call) |
| Tool calls as a DSH subagent | **0 in the decisive run** |
| WinForms calculator produced | **no** |
| Console calculators | not reached |

For comparison, the fastest model in the main battle was Qwen3.5-9B at 69.7 tok/s and Nemotron-30B at
60.6 tok/s — flint sits between them, while being by far the largest file (22.5 GiB versus 5.24 and 17.6).
The MoE sparsity really does pay off: only 6 of 256 experts are active per token.

## What actually happened

The task was the same as for every other model: write a WinForms calculator, build it, publish an exe.
Four configurations were tested, all with the same minimal prompt.

| Reasoning budget | Language | Outcome |
| :--- | :--- | :--- |
| `--reasoning-budget 0` (off) | EN | wrote both files, then **28 edits in a row** failing with `old_string was not found`; no build |
| `--reasoning-budget 6000` + "Stop analysing. Call the tool now." | EN | **12 rewrites of `Program.cs`** — full 6 283-character writes alternating with 116- and 12-character stubs; no build |
| `--reasoning-budget 16384` | EN | **16 263 tokens spent reasoning**, 279 s, file never completed |
| `--reasoning-budget 32768` | EN | **32 771 tokens spent reasoning**, 593 s, **zero tool calls** |
| unrestricted (`-1`) | RU | degenerated into repeated `<think></think>` |

The last row is the decisive one. With a 128K context window, a 40K output limit and a 32K reasoning
budget, the model spent every token it was allowed on deliberation and never made a single tool call.

## Code quality — the parts it did write

The code flint produced was checked with the compiler and with reflection, not by eye:

| Finding | Detail |
| :--- | :--- |
| `CS1513` | the file ends at line 217 with the class and namespace left unclosed |
| Latent `CS1729` | `new Font("Segoe UI", 10, FontStyle.Regular, GraphicsUnit.Point, 10, false, false, false, false)` — **9 arguments**; `System.Drawing.Font` only has constructors taking 2, 3, 4, 5 and 6 arguments (verified by reflection), so this would fail as soon as the braces were fixed |
| Locale bug | `result.ToString()` without invariant culture — same decimal-comma problem as the other models |

What it got **right** is worth noting, because these are exactly the traps other models fell into:

- `Keys.Oemplus` with the correct lower-case `p` (Nemotron used `OemPlus` and broke its build with `CS0117`);
- **no `base.OnKeyDown` call** from its own `KeyDown` handler — the recursion that crashed Nemotron's calculator;
- a sane structure: fields, `UpdateDisplay`, `Calculate`, `AppendDigit`, `Backspace`, `ClearAll`.

So the API knowledge is there. The discipline is not: tens of thousands of reasoning tokens, then two
missing braces.

## Why the reasoning budget does not save it

`--reasoning-budget N` is enforced server-side: when the counter is exhausted, llama.cpp injects the
end-of-thinking token and the model must start answering. The model does not know this is happening.

There is a side effect that makes the low budgets worse, not better: the cut can land **inside a tool call**,
truncating its arguments. That is exactly what the 6 000-token run shows — full 6 283-character writes
alternating with 12-character stubs, the model re-writing the file over and over because each truncated
write left it empty.

`--reasoning-budget-message` helps steer the model ("Stop analysing. Call the tool now."), but does not
prevent the truncation.

## What the community writes

The Hugging Face thread
[“Flint can now run in llama.cpp and Unsloth Desktop!”](https://huggingface.co/unsloth/flint-GGUF/discussions/3)
says the same thing, less politely:

> “It just thinks and thinks and thinks lol. Not really usefull”

and a reply that matches our measurements closely:

> “This is how not very smart models work nowadays. If you take a mediocre model → make it loop in thinking →
> it can produce something useful at the end. Caveat here is that it can use more time than a big slow model
> will use for the same task.”

Other reports in the same thread: *"20K+ reasoning tokens before it wrote any code"*, *"it's fast but not too
smart"*, and one case where the agent *"deleted everything including report"*.

One person found `reasoning-budget = 20000` workable. At 32 768 it still produced nothing in our harness, so
the difference is likely the task shape rather than the budget.

**Speed references:** a user reports 49 tok/s on an RX 7800 XT (Vulkan, Q4_K_XL, 23.3 GiB) — consistent with
our 55–62 tok/s on an RTX 4070 Ti.

## Template notes

The original chat template from RecursiveSI contains `| replace("\x00", "")`. Older llama.cpp builds and
LM Studio failed on it with `Failed to parse Jinja template: Unexpected escaped character: x`. Fixed upstream:

- [PR #30929](https://github.com/ggml-org/llama.cpp/pull/30929) — *jinja: support hexadecimal string escapes*
- [PR #30928](https://github.com/ggml-org/llama.cpp/pull/30928) — *models: Add Flint model*

Both merged 2026-10-21. Our build (`b12248`) includes them, so no template error occurred here.

## Verdict

flint is a **fast text generator** with a real MoE advantage: 22.5 GiB of weights running at 55–62 tok/s on a
12 GB card. Tool calling works at the API level.

As an agent in a harness with a fixed per-step token budget it does not work at any setting we tested —
0, 6 000, 16 384 or 32 768 tokens. It either cannot complete an edit loop (budget 0), gets its tool calls
truncated (low budgets) or spends everything on deliberation and never acts (16K and above).

Good uses: one-shot code snippets, explanations, drafting text. Bad uses: autonomous multi-step work with a
token ceiling.

## Reproducing

```powershell
llama-server -m flint-Q4_K_M.gguf --host 127.0.0.1 --port 8090 --alias flint-24b-64k `
  -c 131072 -fa on -ctk q8_0 -ctv q8_0 --jinja -np 1 `
  --reasoning-format deepseek --reasoning-budget 32768 --no-webui
```

Measured on: AMD Ryzen 7 9800X3D, 64 GB DDR5, NVIDIA RTX 4070 Ti 12 GB, Windows 11, llama.cpp CUDA `b12248`.
Supervision and measurement by **DeepSeek-V4.1-Flash**; the orchestrator did not write or fix model code.
