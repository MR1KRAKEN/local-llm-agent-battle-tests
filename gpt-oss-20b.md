# gpt-oss:20b (Ollama, MXFP4) — Agent Coding Test

**Weights:** [openai/gpt-oss-20b](https://huggingface.co/openai/gpt-oss-20b), run through the Ollama library
tag `gpt-oss:20b` (`registry.ollama.ai/library/gpt-oss/20b`, model layer 13,793,422,144 bytes).
**Runtime:** Ollama (`local-ollama`) at `http://127.0.0.1:11434`; the main run used the `gpt-oss:20b-32k-stable`
tier, later refinement rounds used `gpt-oss:20b-64k`
**Date:** 11–12 November 2026

> Testing was carried out under the supervision of **DeepSeek-V4.1-Flash** (DSH orchestrator,
> provider `deepseek-account`, model id `deepseek-flash`).

## Summary

| Area | Result |
| :--- | :--- |
| WinForms → exe | ❌ no exe in the main run; in refinement an exe was built and it computes integers with the mouse |
| Console languages | `40 / 40*` — best console result in the set |
| Refinement | exe appeared, grid fixed, integer arithmetic works; decimals, `C` and keyboard do not |

**Verdict: ❌/⚠️ the widest spread in the set.** Console work is excellent (`8/8` on four languages in a row),
GUI is its weakest area. `*` — Java counts only because the orchestrator demanded compilation separately;
without that intervention it would be `32/40`.

## WinForms — main run

| Metric | Value |
| :--- | ---: |
| Wall time | 190 s |
| Steps | 31 (over the 25 limit) |
| Build attempts | 0 / 3 real builds (+3 calls rejected by the harness before execution) |
| prompt / completion tokens | 21,958 / 7,164 |
| TTFT | 1.70 s |
| Speed | 57.12 tok/s |
| VRAM peak | 11,703 MiB |
| exe | none |

Of 31 steps, three were burned on invented tool parameters (`sandbox_permissions: ""`, `timeoutMs: 0`,
empty `justification` — the harness answered `Error: invalid arguments`). Files were placed in an extra
`CalculatorBattle\` subfolder, so the first build died with `MSB1003` ("no project specified").
`Program.cs` was only 8.5 KB — the implementation was cut off, and the final message was empty.

Compiler errors: `CS1001`, `CS1002`, `CS1003`, `CS1022`, `CS1026`, `CS1519`, `CS1525`, `CS8124`
(a syntax meltdown on the first real build) and `CS0117`, `CS0123`, `CS0200`, `CS0246`, `CS1739`
("no such named argument") on the second.

## WinForms — refinement (detail)

The refinement stage started from "project was never built". It took five rounds, including two separate
"build and publish only" tasks, because the model repeatedly reported success while `dist` stayed stale.

| Round | What the model did | Independent check |
| :--- | :--- | :--- |
| 1 | wrote buttons, styles, `ProcessCmdKey` | exe built, but `dist` was not refreshed — edits never reached the binary |
| 2 (separate "build & publish" task) | published the project | exe appeared, but was older than `Program.cs` |
| 3 | replaced `DataTable.Compute(expr, "$")` with its own parser | mouse: `123*45=` → **`5535`**, integers now compute |
| 4 | fixed the grid (`Controls.Add(b, c, r)`) and removed `Region` in `OnPaint` | layout became correct, clicks land on the intended buttons: `4`,`6`,`+`,`5`,`4` builds `46+54` |
| 5 (independent web research, no orchestrator hints) | fixed parsing and `C` | decimals still broken: `2.5+2.5=` → `27,5`; `C` does not reset; keyboard operators dead |

**Root cause found during refinement.** The original evaluator called
`dt.Compute(expr, "$")`. The second argument of `DataTable.Compute(expression, filter)` is a row filter, and
`"$"` is not a valid filter expression — that is why every expression produced `Error`. Replacing it with a
small hand-written parser fixed integer arithmetic. Note that an earlier model message claimed it had changed
`"$"` to `""`; the file still contained `"$"` at that point.

**State after refinement (measured, not claimed):**

| Check | Result |
| :--- | :--- |
| `123*45=` with mouse | `5535` ✅ |
| `46+54=` with mouse | `100` ✅ |
| `2.5+2.5=` with mouse | `27,5` ❌ (the second `.` is dropped, and output uses a comma) |
| `10/0=` | `Error` — but the expression was corrupted by the dead `/` click |
| `C` button | does not reset the expression or the result ❌ |
| Keyboard `2+2⏎` | display `22`, result `Error` — `+` never reaches the handler ❌ |
| Window title | `Calculator` ✅ |
| Button grid | 4 × 5, correct order, captions visible ✅ |

**Behaviour worth noting.** In the round where the orchestrator explicitly asked it to research the web and
gave no hints, the model never called `web_search` or `web_fetch`. Instead it called a non-existent tool
named `search` seven times (`Error: unknown tool "search"`), trying to grep its own source for `Compute(`,
`try {`, `OemComma`. Seven steps of its budget were wasted that way.

## Console languages

| Language | Score | Notes |
| :--- | :---: | :--- |
| Python | **8 / 8** | 800 bytes, 7 steps, 66 s |
| C | **8 / 8** | 2,529 bytes, 12 steps, 105 s |
| JavaScript | **8 / 8** | 0.8 KB |
| Rust | **8 / 8** | 3.5 KB |
| Java | **8 / 8*** | `Calc.java` written, but `javac` was called only after a separate orchestrator instruction |

## What to expect when choosing this model

- **Console tasks are its strength:** all eight cases on four languages, including `0.1+0.2 → 0.3`.
- **GUI is its weakness:** it did not reach an exe in the agent run, and it also failed in the simpler
  one-shot harness of the previous stage.
- **Invents tool parameters** (`sandbox_permissions`, `timeoutMs`) and wastes steps on rejected calls.
- **Does not research** even when explicitly asked; it invents tool names instead.
- Reports success before verifying: one answer contained nothing but "Build exit code 0" while the binary
  was still stale.

---

Post your own results in the model discussions:
[openai/gpt-oss-20b/discussions](https://huggingface.co/openai/gpt-oss-20b/discussions)
