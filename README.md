# Local LLM Agent Tests — WinForms Calculator + Five Languages

**Languages:** English (this file) · [Русский](ru/README.md)

A reproducible evaluation of local models acting as **autonomous coding agents**: each model had to
write a working **C#/WinForms calculator (.NET 8), build it and publish a single-file exe**, and then write
**console calculators in Python, C, JavaScript, Rust and Java** verified against eight fixed expressions.

> **Testing was carried out under the supervision of DeepSeek-V4.1-Flash** (DSH orchestrator; provider
> `deepseek-account`, model id `deepseek-flash`). It started the servers, assigned the tasks, ran the
> automated checks, collected the metrics and wrote the reports. It did not write or fix model code.

## Participants

| Model | Weights | Quant | Size | Discuss |
| :--- | :--- | :--- | ---: | :--- |
| NVIDIA Nemotron-3.5-Lightning-30B-A3B | [ggml-org/NVIDIA-Nemotron-3.5-Lightning-30B-A3B-GGUF](https://huggingface.co/ggml-org/NVIDIA-Nemotron-3.5-Lightning-30B-A3B-GGUF) | Q4_0 | 17.6 GiB | [discussions](https://huggingface.co/ggml-org/NVIDIA-Nemotron-3.5-Lightning-30B-A3B-GGUF/discussions) |
| Qwen3.5-9B | [lmstudio-community/Qwen3.5-9B-GGUF](https://huggingface.co/lmstudio-community/Qwen3.5-9B-GGUF) | Q4_K_M | 5.24 GiB | [discussions](https://huggingface.co/lmstudio-community/Qwen3.5-9B-GGUF/discussions) |
| LFM2-24B-A2B | [lmstudio-community/LFM2-24B-A2B-GGUF](https://huggingface.co/lmstudio-community/LFM2-24B-A2B-GGUF) | Q4_K_M | 13.43 GiB | [discussions](https://huggingface.co/lmstudio-community/LFM2-24B-A2B-GGUF/discussions) |
| Bonsai-27B | [lmstudio-community/Bonsai-27B-GGUF](https://huggingface.co/lmstudio-community/Bonsai-27B-GGUF) | Q1_0 | 3.54 GiB | [discussions](https://huggingface.co/lmstudio-community/Bonsai-27B-GGUF/discussions) |
| gpt-oss:20b | [openai/gpt-oss-20b](https://huggingface.co/openai/gpt-oss-20b) (run via Ollama library `gpt-oss:20b`) | MXFP4 | 12.8 GiB | [discussions](https://huggingface.co/openai/gpt-oss-20b/discussions) |
| flint-24B (MoE) | [lmstudio-community/flint-GGUF](https://huggingface.co/lmstudio-community/flint-GGUF) (weights: [RecursiveSI/flint](https://huggingface.co/RecursiveSI/flint)) | Q4_K_M | 22.5 GiB | [discussions](https://huggingface.co/lmstudio-community/flint-GGUF/discussions) |
| qwen3:30b | [Qwen/Qwen3-30B-A3B](https://huggingface.co/Qwen/Qwen3-30B-A3B) (run via Ollama library `qwen3:30b`) | Q4_K_M | 17.3 GiB | [discussions](https://huggingface.co/Qwen/Qwen3-30B-A3B/discussions) |

The GGUF repositories were verified to contain exactly the files used (checked against the Hugging Face
API, including `mmproj` files for the vision-capable models).

Three further models were probed during the extended runs. They are **not part of the main tables** because
they turned out to be unsuitable for agent work on this hardware, but the findings are worth recording:

| Model | What blocked it |
| :--- | :--- |
| Devstral-Small-2-24B (IQ3_XXS) | its chat template rejects the harness message order (`conversation roles must alternate user and assistant`), and with a lenient template the tool calls disappear |
| Llama-3.1-8B-Instruct | zero tool calls under Ollama; under llama.cpp the tool calls appear, but the agent loop collapses on compiler feedback |
| Ministral-3-14B-Instruct (Q8) | 5.45 tok/s — 14.2 GiB does not fit in 12 GB of VRAM, and no tool call in seven minutes |

## Test bench

AMD Ryzen 7 9800X3D (8C/16T), 64 GB DDR5, **NVIDIA RTX 4070 Ti 12 GB**, Windows 11 Pro, .NET SDK 8.0.428,
Python 3.14, gcc (WinLibs UCRT), Node 24.17, rustc, Oracle JDK, llama.cpp CUDA `b12248`, Ollama.

Providers: `local-llama` → `http://127.0.0.1:8090/v1` (llama.cpp, `-np 1`, ctx 65536, `--jinja`,
`--reasoning-budget 0`, KV cache q8_0), `local-ollama` → `http://127.0.0.1:11434`.

## How to read the numbers

**Console tests.** Each language receives eight lines on stdin and its output is compared line by line,
character by character:

| Input | Expected output |
| :--- | :--- |
| `2+3` | `5` |
| `7*8` | `56` |
| `100/4` | `25` |
| `2.5+1.5` | `4` |
| `-4+10` | `6` |
| `0.1+0.2` | `0.3` |
| `(2+3)*4` | `20` |
| `10/0` | `error` |

`n / 8` is the number of matching cases. Any extra output line shifts the comparison and counts as a failure.
The `x / 40` total is the sum across five languages (maximum `5 × 8 = 40`).

**WinForms.** Verification was twofold: a formal automated check (exe exists in `dist`, the process is
alive after 8 s, the process has a window title, pressing `1+2=` does not kill it) **and** a manual
functional check: mouse clicks on buttons, keyboard input, non-trivial arithmetic (`46+54=100`,
`123*45=5535`) and division by zero.

**"Builds"** is the number of compiler invocations in a run and how many returned `exit 0`.
`1 / 7` means seven attempts, one successful.

## Three stages

1. **BATTLE2** — one-shot prompt with a custom harness, no edit loop: **no model produced an exe**.
2. **BATTLE3** — DSH subagents with `write`/`edit`/`read`/`pwsh` and compiler feedback: Nemotron and Qwen
   produced exes, gpt-oss and Bonsai did not, LFM2 was blocked by the runtime.
3. **Refinement** — models had to fix their own code in a separate `improved\` folder. Only local,
   single-line fixes succeeded.

## Model reports

- [NVIDIA Nemotron-3.5-Lightning-30B-A3B](nvidia-nemotron-3.5-lightning-30b-a3b.md)
- [Qwen3.5-9B](qwen3.5-9b.md)
- [LFM2-24B-A2B](lfm2-24b-a2b.md)
- [Bonsai-27B](bonsai-27b.md)
- [gpt-oss:20b](gpt-oss-20b.md)
- [flint-24B (MoE) — fast, but thinks more than it does](flint-24b.md)

## Orchestration notes

- [Concurrency, roles and repeatability](orchestration-notes.md) — how many agents fit on one server, the
  context-per-slot pitfall, a researcher/implementer/reviewer pipeline, and four identical runs of the same
  task (mean 7.0/8, fully correct in 50% of runs).

## Caveats

- Models had no internet access, except Qwen during one refinement round (three Microsoft Learn pages);
  this is noted in its report.
- The orchestrator passed diagnostics to the models: compiler error text, crash stack traces and lists of
  observed symptoms. The models made the edits themselves.
- Time and step limits were not technically enforced, so some runs exceeded them; the reported values are
  measured, not assigned.
