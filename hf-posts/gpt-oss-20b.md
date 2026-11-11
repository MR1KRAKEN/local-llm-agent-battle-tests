# Agentic coding test: gpt-oss:20b (Ollama) — console champion, GUI weak spot

Part of a **comparison of five local models** run as autonomous coding agents. Overview with the full
matrix: {{OVERVIEW_URL}}

Russian version of the full report: https://github.com/MR1KRAKEN/local-llm-agent-battle-tests (`ru/` folder).
Tested through the Ollama library tag `gpt-oss:20b` (MXFP4), not through a GGUF from this repo.

> Testing was carried out under the supervision of **DeepSeek-V4.1-Flash** (DSH orchestrator).
> It started the server, assigned the task, ran the checks and collected the metrics; it did not write or
> fix model code.

## Console languages — 40 / 40, the best in the set

| Python | C | JavaScript | Rust | Java |
| :---: | :---: | :---: | :---: | :---: |
| 8/8 | 8/8 | 8/8 | 8/8 | 8/8* |

All eight reference expressions correct on four languages in a row, `0.1+0.2 → 0.3` included.
`*` — Java counted only after a separate orchestrator instruction to run `javac`; the model wrote
`Calc.java` but never compiled it. Without that intervention the total would be `32/40`.

## WinForms — no exe in the main run

| Metric | Value |
| :--- | ---: |
| Wall time | 190 s |
| Steps | 31 |
| Builds | 0 / 3 real (+3 calls rejected by the harness) |
| prompt / completion tokens | 21,958 / 7,164 |
| TTFT / speed | 1.70 s / 57.12 tok/s |
| VRAM peak | 11,703 MiB |
| exe | none |

Three of 31 steps were burned on **invented tool parameters** (`sandbox_permissions: ""`, `timeoutMs: 0`,
empty `justification`); the harness answered `Error: invalid arguments`. Files went into an extra
`CalculatorBattle\` subfolder, so the first build died with `MSB1003`. `Program.cs` was only 8.5 KB —
the implementation was cut off, and the final message was empty.

Compiler errors: `CS1001`, `CS1002`, `CS1003`, `CS1022`, `CS1026`, `CS1519`, `CS1525`, `CS8124` on the first
real build, then `CS0117`, `CS0123`, `CS0200`, `CS0246`, `CS1739` ("no such named argument").

## Refinement — from "never built" to working integer arithmetic

It took five rounds, including two separate "build and publish only" tasks, because the model repeatedly
reported success while `dist` stayed stale.

| Round | What the model did | Independent check |
| :--- | :--- | :--- |
| 1 | wrote buttons, styles, `ProcessCmdKey` | exe built, but `dist` not refreshed — edits never reached the binary |
| 2 (build & publish only) | published | exe appeared but was older than `Program.cs` |
| 3 | replaced `DataTable.Compute(expr, "$")` with its own parser | mouse `123*45=` → **`5535`** |
| 4 | fixed the grid (`Controls.Add(b, c, r)`), removed `Region` in `OnPaint` | layout correct, clicks land on intended buttons |
| 5 (independent web research, no hints) | fixed parsing and `C` | decimals still broken, `C` does not reset, keyboard operators dead |

**Root cause found during refinement:** the evaluator called `dt.Compute(expr, "$")`. The second argument
of `DataTable.Compute(expression, filter)` is a row filter, and `"$"` is not a valid filter expression —
hence `Error` on every expression. A small hand-written parser fixed integer arithmetic.

**State after refinement (measured externally):**

| Check | Result |
| :--- | :--- |
| `123*45=` with mouse | `5535` ✅ |
| `46+54=` with mouse | `100` ✅ |
| `2.5+2.5=` with mouse | `27,5` ❌ (second `.` dropped, comma decimal separator) |
| `C` button | does not reset expression or result ❌ |
| keyboard `2+2⏎` | display `22`, result `Error` — `+` never reaches the handler ❌ |
| window title / grid | `Calculator` ✅ / 4×5 correct ✅ |

**Behaviour worth noting.** In the round where it was explicitly asked to research the web and given no
hints, the model never called `web_search` or `web_fetch`. Instead it called a non-existent tool named
`search` seven times (`Error: unknown tool "search"`), trying to grep its own source for `Compute(`,
`try {`, `OemComma` — seven steps of budget wasted.
