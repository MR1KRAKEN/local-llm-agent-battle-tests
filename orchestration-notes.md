# Orchestration notes: concurrency, roles, and repeatability

**Languages:** English (this file) · [Русский](ru/orchestration-notes.md)

Measurements taken while running local models as DSH subagents on the battle rig. They are about the
**harness**, not about any single model, so they live apart from the per-model reports.

Bench: AMD Ryzen 7 9800X3D, 64 GB DDR5, **NVIDIA RTX 4070 Ti 12 GB**, Windows 11, llama.cpp CUDA `b12248`.

## 1. How many agents fit on one server

llama.cpp serves several requests at once with `-np N`. It batches them, so total throughput grows while
each individual request slows down. Measured with Bonsai-27B (Q1_0, 3.5 GiB — small enough to show the shape
clearly), 220 generated tokens per request:

| Concurrent agents | Per agent | Total | % of single | VRAM |
| ---: | ---: | ---: | ---: | ---: |
| 1 | 75.8 tok/s | 75.8 tok/s | 100% | 8.9 GiB |
| 2 | 63.4 tok/s | 126.6 tok/s | 164% | — |
| 4 | 42.5 tok/s | 177.1 tok/s | 220% | 8.9 GiB |
| 8 | 27.4 tok/s | 219.2 tok/s | 289% | 9.4 GiB |
| 16 | 18.2 tok/s | **289.9 tok/s** | **383%** | 10.7 GiB |

The same shape on a larger model — Qwen3.5-9B, `-np 4`, `-c 131072`:

| Concurrent agents | Per agent | Total |
| ---: | ---: | ---: |
| 1 | 67.5 tok/s | 67.5 tok/s |
| 4 | 58.4 tok/s | **233.3 tok/s** |

And with `-np 2`, two agents measured **61–64 tok/s each** while running simultaneously.

**Practical reading.** Four agents is the sweet spot: each one still runs at roughly the speed a single
large model gives you, but you get four at once. Eight agents at 27 tok/s each is already sluggish for
agent work; sixteen is only useful for batch jobs that tolerate slow per-task progress.

## 2. The pitfall: context is divided between slots

`-c` sets the **total** context of the server, and it is split across slots: per-slot context is
`-c / np`. The DSH system prompt alone is about **12 278 tokens**. So a configuration like
`-c 32768 -np 4` gives 8 192 tokens per slot, and every request fails immediately:

```
400: {"message":"request (12278 tokens) exceeds the available context size (8192 tokens),
      try increasing it"}
```

Working configuration for four agents: `-c 131072 -np 4` — 32K per slot, which leaves room for the prompt,
the tool schemas and a long working context.

## 3. Splitting roles between agents

A small pipeline was tested on Qwen3.5-9B (`-np 4`, 32K per slot): a researcher, three parallel
implementers, and a reviewer.

| Role | What it did | Outcome |
| :--- | :--- | :--- |
| Researcher | `web_fetch` of an article, wrote `research.md` (2.4 KB) | succeeded on the second attempt — the first time it fetched a page and wrote no file |
| Python implementer | `calc.py` | **8/8** |
| JS implementer | `calc.js` | **8/8** |
| C implementer | `calc.c` + `calc.exe` | **0/8** — `fgets` without a loop, reads a single line |
| Reviewer | ran all three, wrote `review.md` | **accurate**: 8/8, 0/8, 8/8 — matched an independent check by the orchestrator |

Parallelism was confirmed in the server log: slots 0, 1 and 2 were processing requests at the same time, each
around 30–35 tok/s against 67.5 alone.

**Observations:**

- Role separation works. The researcher did go online (one of only two web accesses in the whole project),
  and the reviewer correctly reported the single failure without inventing results.
- A dedicated researcher is of limited value for a simple task: the summary it produced was general
  knowledge the model already had. It matters when the task needs facts the model lacks.
- Parallel implementers write worse code than solo ones. The JS agent produced a file with a duplicate
  `const tokens` that did not even parse — the same model wrote 8/8 for JS when running alone.

## 4. Repeatability: same task, same prompt, four runs

Qwen3.5-9B, four independent runs of an **identical** prompt: a console calculator in Python verified against
the same eight expressions. Verified by the orchestrator, not by the model.

| Run | Score | What broke |
| :--- | :--- | :--- |
| run-1 | **8/8** | — |
| run-2 | **5/8** | `RecursionError: maximum recursion depth exceeded` on `(2+3)*4`; `0.1+0.2` printed `0.30000000000000004` |
| run-3 | **7/8** | `-4+10` → `-14`: the unary minus captured the whole expression |
| run-4 | **8/8** | — |

**Mean 7.0 / 8; fully correct in 2 of 4 runs (50%).**

Two things worth taking away:

1. **The failure mode varies, not just the outcome.** Three different defect classes appeared on one task:
   a recursion crash, float formatting, and unary-minus precedence. Knowing that a model "can do it" says
   nothing about *how* it will break next time.
2. **Self-reporting is unreliable.** In 2 of 4 runs the model claimed 8/8 while the actual score was lower
   (run-2 reported success with a crashing program). Agent output has to be verified by running it.

## 5. Cost: tokens per task is as important as tok/s

A fast model can afford to loop, and the bill is paid in tokens. Observed on the same rig:

| Run | Tokens spent | Wall time | Result |
| :--- | ---: | ---: | :--- |
| Bonsai-27B, Rust console | **1.4M** | 6 m 45 s | exe built but panics on first input — 0/8 |
| qwen3:30b, Java console | 389K | 12 m 10 s | 6/8, later fixed to 8/8 |
| qwen3:30b, Rust retry | 129K | 5 m 49 s | 8/8 |
| flint-24B, reasoning budget 32K | 44.6K | 10 m 17 s | zero tool calls |

A model at 70 tok/s that thinks in circles is more expensive than a slower model that acts. High `tok/s`
alone is a misleading headline number for agent work.

## Reproducing the harness settings

```powershell
# four agents, 32K context each
llama-server -m model.gguf --host 127.0.0.1 --port 8090 --alias model-alias `
  -c 131072 -fa on -ctk q8_0 -ctv q8_0 --jinja -np 4 --no-webui
```

Measured and written up by **DeepSeek-V4.1-Flash** (DSH orchestrator); it did not write or fix model code.
