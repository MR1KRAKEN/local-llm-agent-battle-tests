# Agentic coding test of 5 local models: WinForms exe + 5 console languages

I ran five local models as **autonomous coding agents** on two tasks and measured the results. Full logs,
per-model details and Russian versions are in the companion repository:
**https://github.com/MR1KRAKEN/local-llm-agent-battle-tests** (Russian docs live in the `ru/` folder there).

> Testing was carried out under the supervision of **DeepSeek-V4.1-Flash** (DSH orchestrator). It started
> the servers, assigned the tasks, ran the automated checks and collected the metrics. It did not write or
> fix model code.

## Task

1. Write a working **C#/WinForms calculator (.NET 8)** in a given folder, build it and publish a single-file
   exe (dark theme, 4×5 button grid, keyboard support, division-by-zero handling).
2. Write **console calculators in Python, C, JavaScript, Rust and Java**, each verified against eight fixed
   expressions (`2+3`, `7*8`, `100/4`, `2.5+1.5`, `-4+10`, `0.1+0.2`, `(2+3)*4`, `10/0`).

## Bench

Ryzen 7 9800X3D, 64 GB DDR5, **RTX 4070 Ti 12 GB**, Windows 11, .NET SDK 8. llama.cpp (ctx 65536,
`--jinja`, `--reasoning-budget 0`, KV q8_0) for GGUF models, Ollama for gpt-oss:20b.

## Results

| Model | WinForms exe | Python | C | JS | Rust | Java | Console total |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | ---: |
| Nemotron-3.5-Lightning-30B-A3B Q4_0 | ⚠️ exe built, mouse works, keyboard crashed | 8/8 | 7/8 | 8/8 | 8/8 | 6/8 | 37/40 |
| Qwen3.5-9B Q4_K_M | ⚠️ exe built, UI unusable | 4/8 | 0/8 | 8/8 | 7/8 | 0/8 | 19/40 |
| LFM2-24B-A2B Q4_K_M | ⏱ no tool call reached the harness | — | — | — | — | — | — |
| Bonsai-27B Q1_0 | ❌ degeneration, no build | — | — | — | — | — | — |
| gpt-oss:20b (Ollama) | ❌ no exe in the main run | 8/8 | 8/8 | 8/8 | 8/8 | 8/8* | 40/40* |

`n/8` — matched cases out of eight; `x/40` — sum across five languages. `*` — gpt-oss Java was compiled
only after a separate orchestrator instruction; without it the total would be `32/40`.

## Per-model reports

Links to the individual reports are in the comments below.

## Main findings

1. **Harness matters more than weights.** The same models scored zero exes in an earlier one-shot harness
   and three exes once compiler feedback and surgical `edit` calls were available.
2. **"Builds" is not "works".** All three produced exes had functional defects (crash on keypress, dead
   input, broken decimals). The formal check (process alive 8 s) missed them; manual mouse/keyboard tests
   found them.
3. **Local single-line fixes land, parser rewrites do not.** Removing `base.OnKeyDown` and changing
   `printf("%.10f")` to `%.10g` succeeded. Rewriting a parenthesis parser failed for every model.
4. **Self-verification is unreliable.** Every model claimed success while the checks failed — including one
   that attached a log showing its own failure.
5. **Profiles differ sharply.** Nemotron is the all-rounder; gpt-oss is the console champion with a weak GUI;
   Qwen is fastest but narrow (0/8 in C and Java); Bonsai at Q1_0 degenerates; LFM2 is blocked by the
   integration, not by its ability to emit tool calls.
