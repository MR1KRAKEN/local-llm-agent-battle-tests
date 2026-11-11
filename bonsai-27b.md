# Bonsai-27B (Q1_0) — Test as a DSH Agent

**Languages:** English (this file) · [Русская версия](ru/bonsai-27b.md)

**Weights:** [lmstudio-community/Bonsai-27B-GGUF](https://huggingface.co/lmstudio-community/Bonsai-27B-GGUF)
— `Bonsai-27B-Q1_0.gguf`, 3,803,452,576 bytes (3.54 GiB), plus the multimodal projector
`mmproj-Bonsai-27B-BF16.gguf` (931,145,888 bytes)
**Runtime:** llama.cpp (`local-llama`), ctx 65,536, `--jinja --reasoning-budget 0`
**Date:** 11 November 2026

> Testing was carried out under the supervision of **DeepSeek-V4.1-Flash** (DSH orchestrator,
> provider `deepseek-account`, model id `deepseek-flash`).

## Summary

**Verdict: ❌ unsuitable for coding at the Q1_0 quant.** No successful build, then degeneration.
This is expected: the model is a vision model by design, and Q1_0 is extreme quantization (about 1 bit
per weight). By the stand owner's decision it was excluded from the refinement stage.

## Runs

| Stage | Metric | Value |
| :--- | :--- | ---: |
| One-shot harness | steps / successful builds | 11 / 0 of 1 |
| One-shot harness | speed / time | 72.1 tok/s / 5 min |
| Agent run | time before stop | 610 s (interrupted by the orchestrator) |
| Agent run | steps | 7 |
| Agent run | builds: successful / total | 0 / 2 |
| Agent run | prompt / completion tokens | 54,654 / 13,274 |
| Agent run | TTFT | 7.74 s |
| Agent run | speed | 55.55 tok/s |
| Agent run | VRAM peak | 9,133 MiB |
| Agent run | exe | none |

## What exactly broke

**Compiler errors (both builds):** `CS0103` (name does not exist in the context), `CS0117` (type has no such
member), `CS0123` (no overload matches the delegate), `CS0246` (type not found), `CS1061` (no such member),
`CS1503` (cannot convert argument), `CS1729` (type has no constructor with those arguments), plus warning
`CS8632` (nullability annotation outside a `#nullable` context).

**Degeneration.** After two failed builds the model started an answer that never ended: the llama.cpp log
showed generated-token count reaching **15,574** against `defaultMaxTokens: 8192`, running for about ten
minutes at ~53 tok/s. Files did not change during that time. The orchestrator interrupted the run manually —
the model did not leave the loop on its own.

This is the practical takeaway for local setups: **a hard per-step token limit is necessary**, otherwise a
single response can consume the whole session.

## What to expect when choosing this model

- The error style matches other small-class models: invented API members, lost `using` directives,
  non-existent constructors. The difference is that this model made no attempt to fix them.
- Q1_0 visibly degrades even answer coherence: slow TTFT (7.74 s) and long answers without progress.
- For vision tasks (the model ships with `mmproj`) these tests say nothing — they are about code generation.


## Third-party reports on these exact weights

- **The intended runtime is a patched llama.cpp.** The official repository
  ([prism-ml/Bonsai-27B-gguf](https://huggingface.co/prism-ml/Bonsai-27B-gguf)) states that Q1_0_g128 needs the
  **PrismML fork of llama.cpp** with dedicated 1-bit hybrid-attention kernels, and claims 76.11 average over
  15 thinking benchmarks (89.5% of FP16, coding 81.88). **This run used the stock build**, so the degeneration
  result describes that configuration, not the model in its intended runtime.
- **Base model is Qwen3.6-27B.** That explains
  [Discussion #2](https://huggingface.co/lmstudio-community/Bonsai-27B-GGUF/discussions/2), where the model
  insists it is "Qwen hosted on Alibaba Cloud" and refuses local tools — identity confusion inherited from
  the base model, amplified by 1-bit quantization.

---

Post your own results in the model discussions:
[lmstudio-community/Bonsai-27B-GGUF/discussions](https://huggingface.co/lmstudio-community/Bonsai-27B-GGUF/discussions)
