r"""
Posts follow-up comments with third-party findings into the already published HF discussions.

Usage:
    python comment.py              # dry run
    python comment.py --confirm    # post

Token is read from HF_TOKEN or %USERPROFILE%\.cache\huggingface\token (deleted after use).
"""
import io
import os
import sys

from huggingface_hub import HfApi

UB = "https://github.com/MR1KRAKEN/local-llm-agent-battle-tests"

COMMON_EN = (
    "\n\n---\n\n_Russian version of the full report: %s (folder `ru/`)._\n" % UB
)

COMMENTS = [
    # overview thread
    ("openai/gpt-oss-20b", 278, """**Follow-up: what other people report on these exact weights**

Since publishing, I read the existing threads and upstream issues. Four findings are worth adding, two of them
correct our own wording:

- **Nemotron Q4_0 file had a metadata bug, now fixed.** The official artifact wrote
  `attention.head_count_kv` as zeros, so block 5 was treated as an SSM block
  ([llama.cpp issue #27718](https://github.com/ggml-org/llama.cpp/issues/27718), fixed by
  [PR #27729](https://github.com/ggml-org/llama.cpp/pull/27729) on 2026-08-26). Our local file is
  SHA256 `61f87e75…0e3c`, i.e. the re-uploaded fixed one — our numbers are unaffected.
- **LFM2 uses a Pythonic tool-call format.** Per the official card, calls look like
  `<|tool_call_start|>[func(arg="x")]<|tool_call_end|>` with tools passed as JSON in the system prompt.
  Our harness sends OpenAI-style `tools`, which explains the mismatch we reported.
- **Bonsai Q1_0 expects a patched runtime.** The official repo asks for the PrismML llama.cpp fork with
  dedicated 1-bit kernels. We ran the stock build, so our degeneration result describes that setup only.
- **gpt-oss has known template bugs**: the `commentary` channel left valid without tools drops BFCL_v4 to ~3%
  ([#274](https://huggingface.co/openai/gpt-oss-20b/discussions/274)), and the template crashes on tool calls
  with `content: null` ([#272](https://huggingface.co/openai/gpt-oss-20b/discussions/272)).

Per-model threads now carry the relevant part of this.""" + COMMON_EN),

    ("ggml-org/NVIDIA-Nemotron-3.5-Lightning-30B-A3B-GGUF", 4, """**Follow-up: our file was the fixed conversion**

Our run is not affected by the metadata issue in
[llama.cpp #27718](https://github.com/ggml-org/llama.cpp/issues/27718): the local artifact is
SHA256 `61f87e75…0e3c`, while the buggy file in that report is `b1cc80f0…486f`. The fix
([PR #27729](https://github.com/ggml-org/llama.cpp/pull/27729)) was merged 2026-08-26, so we used the
re-uploaded file.

Also relevant: [discussion #1](https://huggingface.co/ggml-org/NVIDIA-Nemotron-3.5-Lightning-30B-A3B-GGUF/discussions/1)
describes the same pattern we measured — fast (400 tok/s there) but a simple agentic task failed while Qwen
solved it. That matches our "fast but structurally weak agent" conclusion.""" + COMMON_EN),

    ("lmstudio-community/Qwen3.5-9B-GGUF", 3, """**Follow-up: reasoning/content split is a known issue**

Our observations of empty and overlong answers line up with
[discussion #2](https://huggingface.co/lmstudio-community/Qwen3.5-9B-GGUF/discussions/2) here, where
`response_format` output is routed into `reasoning_content` while `content` returns empty.

Practical takeaway from our side: before measuring this model in an agent harness, check that the template
and reasoning channel behave as the harness expects — otherwise the difference in scores can come from the
template, not from the model.""" + COMMON_EN),

    ("lmstudio-community/LFM2-24B-A2B-GGUF", 2, """**Follow-up: the correct tool-call format from the official card**

Correction to our own framing. The official card ([LiquidAI/LFM2-24B-A2B](https://huggingface.co/LiquidAI/LFM2-24B-A2B))
specifies tool calls as **Python-style calls inside special tokens**:

```
<|tool_call_start|>[get_candidate_status(candidate_id="12345")]<|tool_call_end|>
```

and recommends passing the tool list as a JSON object in the system prompt.

In our agent run the harness sent OpenAI-style `tools`. Through the raw API the model did return proper
`tool_calls` (verified with 1, 4, 8, 20 and 32 tools), but inside the agent it wrote XML or bare JSON as text.
So the failure we reported is a protocol mismatch between the harness and this template, **not** evidence that
the model cannot call tools. Worth checking before ruling the model out for agent work.""" + COMMON_EN),

    ("lmstudio-community/Bonsai-27B-GGUF", 3, """**Follow-up: our result may be a runtime artifact**

Important correction. The official repository ([prism-ml/Bonsai-27B-gguf](https://huggingface.co/prism-ml/Bonsai-27B-gguf))
states that Q1_0_g128 needs the **PrismML fork of llama.cpp** with dedicated 1-bit hybrid-attention kernels,
and claims 76.11 average over 15 thinking benchmarks (89.5% of FP16, coding 81.88).

Our test ran the **stock llama.cpp build**. Under it the model degenerated — a single answer of 15,574 tokens
against a 8192 limit — and produced no successful build. That describes the stock configuration, not the model
in its intended runtime.

The base model is Qwen3.6-27B, which also explains
[discussion #2](https://huggingface.co/lmstudio-community/Bonsai-27B-GGUF/discussions/2) here, where the model
insists it is "Qwen hosted on Alibaba Cloud" and refuses local tools.""" + COMMON_EN),

    ("openai/gpt-oss-20b", 279, """**Follow-up: known template issues that affect agent runs**

Two template-level reports are worth linking to our numbers:

- [Discussion #274](https://huggingface.co/openai/gpt-oss-20b/discussions/274): the default Jinja template
  keeps the `commentary` channel valid even when no tools are present, and the author measures BFCL_v4 at
  ~3% on live tests versus 36–60% with a fixed template.
- [Discussion #272](https://huggingface.co/openai/gpt-oss-20b/discussions/272): the template raises on an
  assistant message carrying `content: null` together with `tool_calls` — exactly what a normal agent loop
  produces.

For our run this matters as context rather than as a correction: the console results were measured with tools
present in the request, where the channel bug does not bite. The WinForms failure has a different cause
(invented tool parameters and a never-finished implementation), but template behaviour should be pinned before
comparing scores across harnesses.""" + COMMON_EN),
]


def read_token():
    token = os.environ.get("HF_TOKEN") or os.environ.get("HUGGING_FACE_HUB_TOKEN")
    if token:
        return token.strip(), "env:HF_TOKEN"
    home = os.path.expanduser("~")
    for path in (
        os.path.join(home, ".cache", "huggingface", "token"),
        os.path.join(home, "Desktop", "hf_token.txt"),
    ):
        if os.path.isfile(path):
            with io.open(path, encoding="utf-8") as f:
                value = f.read().strip()
            if value:
                return value, path
    return None, None


def wipe(path):
    try:
        size = os.path.getsize(path)
        with io.open(path, "r+b") as f:
            f.write(b"\0" * size)
            f.flush()
        os.remove(path)
        print("Token file wiped and deleted:", path)
    except Exception as exc:
        print("could not wipe:", exc)


def main():
    confirm = "--confirm" in sys.argv
    token, source = read_token()
    if not token:
        print("NO TOKEN. Put it into %USERPROFILE%\\.cache\\huggingface\\token")
        return 2
    print("Token loaded from:", source)
    api = HfApi(token=token)
    print("Authenticated as:", api.whoami().get("name"))

    if not confirm:
        for repo, num, body in COMMENTS:
            print("  comment -> %s #%d (%d chars)" % (repo, num, len(body)))
        print("\nRe-run with --confirm to post.")
        return 0

    for repo, num, body in COMMENTS:
        try:
            api.comment_discussion(repo_id=repo, discussion_num=num, comment=body, repo_type="model")
            print("COMMENTED: https://huggingface.co/%s/discussions/%d" % (repo, num))
        except Exception as exc:
            print("FAILED %s #%d -> %s" % (repo, num, str(exc)[:200]))

    if source and source != "env:HF_TOKEN":
        wipe(source)
    print("REMINDER: revoke the token on https://huggingface.co/settings/tokens")
    return 0


if __name__ == "__main__":
    sys.exit(main())
