# Agentic coding test: Qwen3.5-9B Q4_K_M — the fastest, the most uneven

Part of a **comparison of five local models** run as autonomous coding agents. Overview with the full
matrix: {{OVERVIEW_URL}}

Russian version of the full report: https://github.com/MR1KRAKEN/local-llm-agent-battle-tests (`ru/` folder).

> Testing was carried out under the supervision of **DeepSeek-V4.1-Flash** (DSH orchestrator).
> It started the server, assigned the task, ran the checks and collected the metrics; it did not write or
> fix model code.

## Setup

llama.cpp, ctx 65536, `--jinja --reasoning-budget 0`, RTX 4070 Ti 12 GB.
File: `Qwen3.5-9B-Q4_K_M.gguf` (5.24 GiB) + `mmproj-Qwen3.5-9B-BF16.gguf`.

## WinForms — two attempts, both unusable

| Metric | Attempt 1 | Attempt 2 |
| :--- | ---: | ---: |
| Wall time | 137.5 s | 378.8 s |
| Steps | 20 | 29 |
| Builds (successful / total) | 2 / 3 | 1 / 8 |
| prompt / completion tokens | 27,917 / 7,938 | 33,775 / 14,134 |
| TTFT / speed | **0.59 s / 69.73 tok/s** | 0.63 s / 64.95 tok/s |
| exe | 161 KB | 160 KB |

**Attempt 1 — clean build, instant crash.** The exe died with
`System.ArgumentException: Controls do not support transparent background colors` at `Program.cs:23`:
the model assigned `Color.Transparent` to `BackColor`. There were no compiler errors at all — the build
was perfectly clean.

**Attempt 2 — dead UI.** The window opens, but buttons have no captions, the last grid row is stretched to
268 px, the window title is empty, and input is ignored (`2+2⏎` leaves `0`).

After a refinement round (documentation hint) the grid and title were fixed and mouse digit entry started
working — but `+ - * /`, `=` and the whole keyboard stayed broken (`46+54⏎` produced `dfed`). The model ran
out of context before building.

## Console languages — 19 / 40, the narrowest profile

| Python | C | JavaScript | Rust | Java |
| :---: | :---: | :---: | :---: | :---: |
| 4/8 | 0/8 | 8/8 | 7/8 | 0/8 |

- **Python 4/8**: `2+3 → 2`, `2.5+1.5 → 2.5`, `-4+10 → error`, `0.1+0.2 → 0.1`. The model rewrote the file
  in circles for 11 minutes without changing its approach.
- **C 0/8**: parser meltdown — `5→3`, `56→8`, `25→400`, `20→0`. Its own "verification" called the **system**
  `calc.exe` instead of `.\calc.exe`, so it tested the Windows calculator, not its binary.
- **Java 0/8**: every case returned `error`; early runs never terminated (infinite loop, 100% CPU).
- **Rust 7/8**: `-4+10 → 14` — the unary minus is swallowed.

## Takeaway

- **Speed is the best in the set** (TTFT 0.59 s, 69.73 tok/s) — noticeable on short tasks.
- Strong only in dynamic languages; hand-written parsers in C/Java fail completely.
- Loops easily: rejected `edit` calls with identical old/new strings, 11-minute rewrite cycles.
- Self-verification does not work: it attached a log showing `2+3 → 2` and still wrote "all defects fixed".
