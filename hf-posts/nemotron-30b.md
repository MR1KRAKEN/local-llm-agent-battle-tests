# Agentic coding test: Nemotron-3.5-Lightning-30B-A3B Q4_0 — the best all-rounder, with a GUI caveat

Up-front context: this is part of a **comparison of five local models** run as autonomous coding agents.
The overview post with the full matrix and methodology is here: {{OVERVIEW_URL}}

English only here; the Russian version of the full report lives on GitHub:
https://github.com/MR1KRAKEN/local-llm-agent-battle-tests (folder `ru/`).

> Testing was carried out under the supervision of **DeepSeek-V4.1-Flash** (DSH orchestrator).
> It started the server, assigned the task, ran the checks and collected the metrics; it did not write
> or fix model code.

## Setup

llama.cpp, ctx 65536, `--jinja --reasoning-budget 0`, KV cache q8_0, RTX 4070 Ti 12 GB.
File: `NVIDIA-Nemotron-3.5-Lightning-30B-A3B-Q4_0.gguf` (17.6 GiB, MoE 30B / ~3B active).

## WinForms result

| Metric | Value |
| :--- | ---: |
| Wall time | 231 s |
| Steps | 30 |
| Build attempts (successful / total) | 1 / 7 |
| prompt / completion tokens | 37,026 / 9,038 |
| TTFT / speed | 2.04 s / 60.65 tok/s |
| VRAM peak | 11,095 MiB |
| exe | `CalculatorBattle.exe`, 165,031 bytes |

**This model actually delivered an exe on its own**, and mouse arithmetic is correct: `2+2=4`, `7*8=56`,
`46+54=100`, `123*45=5535`.

**Critical defect:** pressing any digit killed the process. Cause was a closed recursion loop —
`OnKeyDown` called `base.OnKeyDown`, while `InitializeComponent` subscribed
`this.KeyDown += (s, e) => OnKeyDown(e)`; the crash stack showed
`Control.OnKeyDown -> CalculatorForm.OnKeyDown -> <InitializeComponent>b__18_0 -> ...` repeating.

After a refinement round (the model was given the crash stack trace) it removed `base.OnKeyDown` and the
crash disappeared. Keyboard operators on a Russian layout were never completed — the model exhausted its
context on the third round.

## Console languages — 37 / 40, best in the set

| Python | C | JavaScript | Rust | Java |
| :---: | :---: | :---: | :---: | :---: |
| 8/8 | 7/8 | 8/8 | 8/8 | 6/8 |

- C: `0.1+0.2` printed `0.3000000000` instead of `0.3`; a one-line refinement (`%.10f` → `%.10g`) fixed it
  to 8/8.
- Java: `-4+10` gave `2` and `(2+3)*4` gave `error`; unary minus was fixed (7/8), parentheses still fail
  because the parser scans the whole string and ignores nesting.

## Takeaway

- Holds project structure well: reached `publish` unaided, 311-line file is coherent.
- Does not design event recursion — a typical failure for this size class.
- Loses syntax when assembling a file in chunks: 6 of 7 builds died on unbalanced braces.
- Reports "done" even when input handling crashes — always verify.
