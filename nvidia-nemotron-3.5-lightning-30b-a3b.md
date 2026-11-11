# NVIDIA Nemotron-3.5-Lightning-30B-A3B (Q4_0) — Agent Coding Test

**Languages:** English (this file) · [Русская версия](ru/nvidia-nemotron-3.5-lightning-30b-a3b.md)

**Weights:** [ggml-org/NVIDIA-Nemotron-3.5-Lightning-30B-A3B-GGUF](https://huggingface.co/ggml-org/NVIDIA-Nemotron-3.5-Lightning-30B-A3B-GGUF)
— `NVIDIA-Nemotron-3.5-Lightning-30B-A3B-Q4_0.gguf`, 18,898,091,584 bytes (17.6 GiB), MoE 30B total / ~3B active
**Runtime:** llama.cpp (`local-llama`), ctx 65,536, `--jinja --reasoning-budget 0`, KV cache q8_0
**Date:** 11–12 November 2026

> Testing was carried out under the supervision of **DeepSeek-V4.1-Flash** (DSH orchestrator,
> provider `deepseek-account`, model id `deepseek-flash`).

## Summary

| Area | Result |
| :--- | :--- |
| WinForms → exe | ✅ **exe built by the model itself** (161 KB), mouse arithmetic correct |
| Keyboard | ❌ original build died on the first digit (stack overflow); partially fixed later |
| Console languages | `37 / 40` — best all-round profile in the set |
| Refinement | C fixed to `8/8`, WinForms crash fixed |

**Verdict: ⚠️ the best all-rounder of the set.** The only model that delivered both a mouse-operable GUI
and a nearly complete console result.

## WinForms

| Metric | Value |
| :--- | ---: |
| Wall time | 231 s |
| Steps | 30 (over the 25 limit) |
| Build attempts: successful / total | 1 / 7 |
| Publish calls | 1, succeeded |
| prompt / completion tokens | 37,026 / 9,038 |
| TTFT | 2.04 s |
| Speed | 60.65 tok/s |
| VRAM peak | 11,095 MiB |
| exe | `dist\CalculatorBattle.exe`, 165,031 bytes |

Compiler errors along the way: `CS1002`, `CS1003`, `CS1026`, `CS1513`, `CS1514`, `CS1525`, `CS8641`
(syntax — the file broke while being assembled in chunks), `CS0123` (delegate signature mismatch),
`CS0246` (type not found).

**Critical defect:** `OnKeyDown` called `base.OnKeyDown`, while `InitializeComponent` subscribed
`this.KeyDown += (s, e) => OnKeyDown(e)`. That closed a recursion loop; the crash stack trace showed it
verbatim. Mouse input worked correctly at the same time: `2+2=4`, `7*8=56`.

**After refinement:** the model removed `base.OnKeyDown` — the crash disappeared and mouse arithmetic gave
`46+54=100` and `123*45=5535`. Keyboard operators on a Russian layout were never completed (the model ran
out of context on the third round).

## Console languages

| Language | Score | What failed |
| :--- | :---: | :--- |
| Python | **8 / 8** | — |
| C | 7 / 8 | `0.1+0.2` printed `0.3000000000`; after refinement — **8 / 8** |
| JavaScript | **8 / 8** | — |
| Rust | **8 / 8** | — |
| Java | 6 / 8 | `-4+10` gave `2`, `(2+3)*4` gave `error`; after refinement 7/8 |

## Caveat for readers

- The Java parenthesis failure needs a rewritten parser, not a local patch: `parseExpr`/`parseTerm` scan the
  whole string looking for operators and ignore nesting.

## What to expect when choosing this model

- Holds project structure well: reached `publish` unaided, 311-line file is logically coherent.
- Does not build event recursion — a typical mistake for models of this size class.
- Loses syntax when assembling a file in chunks: 6 of 7 builds failed on unbalanced braces.
- Reports "done" even when input handling crashes — verify yourself.


## Third-party reports on these exact weights

- **Artifact metadata bug (fixed).** The official `NVIDIA-Nemotron-3.5-Lightning-30B-A3B-Q4_0.gguf` had
  per-layer `attention.head_count_kv` written as zeros, so block 5 was treated as an SSM block and the loader
  looked for a non-existent `blk.5.ssm_in.weight`
  ([llama.cpp issue #27718](https://github.com/ggml-org/llama.cpp/issues/27718), fixed by
  [PR #27729](https://github.com/ggml-org/llama.cpp/pull/27729), merged 2026-08-26).
  Our local file has SHA256 `61f87e75…0e3c`, which does **not** match the buggy artifact (`b1cc80f0…486f`),
  so this run used the re-uploaded fixed file and the numbers above are unaffected.
- **User report with the same pattern.**
  [Discussion #1](https://huggingface.co/ggml-org/NVIDIA-Nemotron-3.5-Lightning-30B-A3B-GGUF/discussions/1):
  400 tok/s and a simple agentic configuration task failed, while Qwen solved it immediately — matching our
  "fast but structurally weak agent" finding.
- **Throughput context.** [Discussion #3](https://huggingface.co/ggml-org/NVIDIA-Nemotron-3.5-Lightning-30B-A3B-GGUF/discussions/3)
  reports 25–111 tok/s on pure CPU. For scale we measured 60.65 tok/s on a 4070 Ti, so the model is not
  compute-starved in this setup.

---

Post your own results in the model discussions:
[ggml-org/NVIDIA-Nemotron-3.5-Lightning-30B-A3B-GGUF/discussions](https://huggingface.co/ggml-org/NVIDIA-Nemotron-3.5-Lightning-30B-A3B-GGUF/discussions)
