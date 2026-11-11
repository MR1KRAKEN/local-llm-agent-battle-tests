# Qwen3.5-9B (Q4_K_M) — Agent Coding Test

**Languages:** English (this file) · [Русская версия](ru/qwen3.5-9b.md)

**Weights:** [lmstudio-community/Qwen3.5-9B-GGUF](https://huggingface.co/lmstudio-community/Qwen3.5-9B-GGUF)
— `Qwen3.5-9B-Q4_K_M.gguf`, 5,627,044,256 bytes (5.24 GiB), plus `mmproj-Qwen3.5-9B-BF16.gguf` (921 MB)
**Runtime:** llama.cpp (`local-llama`), ctx 65,536, `--jinja --reasoning-budget 0`
**Date:** 11–12 November 2026

> Testing was carried out under the supervision of **DeepSeek-V4.1-Flash** (DSH orchestrator,
> provider `deepseek-account`, model id `deepseek-flash`).

## Summary

| Area | Result |
| :--- | :--- |
| WinForms → exe | ⚠️ exe built twice (161 and 160 KB), but the application does not work |
| Console languages | `19 / 40` — the narrowest profile in the set |
| Refinement | UI cleaned up, arithmetic never worked |

**Verdict: ⚠️ the fastest and the most uneven.** Best speed in the set (69.7 tok/s, TTFT 0.59 s), but strong
only in dynamic languages: JavaScript `8/8`, while C and Java are `0/8`.

## WinForms — two attempts

| Metric | Attempt 1 | Attempt 2 (`retry`) |
| :--- | ---: | ---: |
| Wall time | **137.5 s** | 378.8 s |
| Steps | **20** | 29 |
| Build attempts: successful / total | 2 / 3 | 1 / 8 |
| prompt / completion tokens | 27,917 / 7,938 | 33,775 / 14,134 |
| TTFT | **0.59 s** | 0.63 s |
| Speed | **69.73 tok/s** | 64.95 tok/s |
| VRAM peak | 7,595 MiB | 7,595 MiB |
| exe | 161 KB | 160 KB |

**Attempt 1 — crash at startup:** `System.ArgumentException: Controls do not support transparent background
colors` at `Program.cs:23` — the model assigned `Color.Transparent` to `BackColor`. The build itself was
clean, with no compiler errors at all.

**Attempt 2 — dead UI:** the window opens, but buttons have no captions, the last `TableLayoutPanel` row is
stretched to 268 px, the window title is empty and input is ignored (`2+2⏎` leaves `0`).

**Refinement:** after being pointed at Microsoft Learn documentation, the model fixed the grid (buttons
90×50) and the window title, and mouse digit entry started working. The operators `+ - * /` and `=` stayed
dead, and the keyboard produced garbage (`46+54⏎` → `dfed`). The model edited `Program.cs` up to 14.7 KB and
then exhausted its context window before building.

## Console languages

| Language | Score | What failed |
| :--- | :---: | :--- |
| Python | 4 / 8 | `2+3→2`, `2.5+1.5→2.5`, `-4+10→error`, `0.1+0.2→0.1`; 11 minutes of rewriting in circles |
| C | 0 / 8 | parser meltdown: `5→3`, `56→8`, `25→400`, `4→1.5`, `6→105`, `0.3→0.2`, `20→0`, `error→2` |
| JavaScript | **8 / 8** | — (1,416 bytes) |
| Rust | 7 / 8 | `-4+10` → `14` (unary minus swallowed) |
| Java | 0 / 8 | every case → `error`; early runs never terminated (infinite loop, 100% CPU) |

## Caveat for readers

- The C run's self-test was invalid: the model called the **system** `calc.exe` instead of `.\calc.exe`,
  so it "verified" the Windows calculator, not its own binary. Its claim that the test passed refers to
  another program.

## What to expect when choosing this model

- **Speed** is best in the set: TTFT 0.59 s, 69.7 tok/s. Noticeable on short tasks.
- **Dynamic-language tasks** go well; hand-written parsers in C/Java do not.
- **Loops easily:** spent 11 minutes rewriting the Python calculator without changing the approach; in Rust
  it issued five consecutive rejected `edit` calls with identical old/new strings
  (`old_string and new_string must differ`).
- **Self-verification does not work:** it attached output showing `2+3 → 2` and still wrote
  "all defects fixed".
- During one refinement round it **used the internet** (three Microsoft Learn pages: `Button.Click`,
  `Form.KeyPreview`, `KeyEventArgs.KeyCode`) — no other model had that access.


## Third-party reports on these exact weights

- **Reasoning/content split.** [Discussion #2](https://huggingface.co/lmstudio-community/Qwen3.5-9B-GGUF/discussions/2)
  reports that `response_format` output is routed into `reasoning_content` while `content` comes back empty —
  the same family of problem as the empty and overlong answers we saw with reasoning-heavy prompts.
- **Common thread with our results:** the model is fast and capable in dynamic languages, but its chat
  template and reasoning channel behave differently from what an agent harness expects by default.

---

Post your own results in the model discussions:
[lmstudio-community/Qwen3.5-9B-GGUF/discussions](https://huggingface.co/lmstudio-community/Qwen3.5-9B-GGUF/discussions)
