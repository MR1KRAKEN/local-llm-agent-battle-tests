r"""
Publishes the agentic-coding test posts to Hugging Face model discussions.

Usage:
    python publish.py                 # dry run: only whoami + preview
    python publish.py --confirm       # actually publish

Token is read from HF_TOKEN env var or %USERPROFILE%\.cache\huggingface\token.
Nothing is printed from the token itself.
"""
import io
import json
import os
import sys

from huggingface_hub import HfApi

HERE = os.path.dirname(os.path.abspath(__file__))

# (repo_id, body file, discussion title)
MODEL_POSTS = [
    ("ggml-org/NVIDIA-Nemotron-3.5-Lightning-30B-A3B-GGUF", "nemotron-30b.md",
     "Agentic coding test: Nemotron-3.5-Lightning-30B-A3B Q4_0 (exe built, keyboard crash found)"),
    ("lmstudio-community/Qwen3.5-9B-GGUF", "qwen3.5-9b.md",
     "Agentic coding test: Qwen3.5-9B Q4_K_M (fastest, but C and Java 0/8)"),
    ("lmstudio-community/LFM2-24B-A2B-GGUF", "lfm2-24b-a2b.md",
     "Agentic coding test: LFM2-24B-A2B (tool calls never reached the harness)"),
    ("lmstudio-community/Bonsai-27B-GGUF", "bonsai-27b.md",
     "Agentic coding test: Bonsai-27B Q1_0 (degeneration, no build)"),
    ("openai/gpt-oss-20b", "gpt-oss-20b.md",
     "Agentic coding test: gpt-oss:20b via Ollama (console 40/40, GUI weak)"),
]

OVERVIEW_FILE = "00-overview.md"
OVERVIEW_TITLE = "Agentic coding test of 5 local models: WinForms exe + 5 console languages (full matrix)"
DEFAULT_OVERVIEW_REPO = "openai/gpt-oss-20b"


def read_token():
    token = os.environ.get("HF_TOKEN") or os.environ.get("HUGGING_FACE_HUB_TOKEN")
    if token:
        return token.strip(), "env:HF_TOKEN"
    home = os.path.expanduser("~")
    candidates = [
        os.path.join(home, ".cache", "huggingface", "token"),
        os.path.join(home, ".huggingface", "token"),
        os.path.join(home, "Desktop", "hf_token.txt"),
        os.path.join(home, "Projects", "agent", "hf_token.txt"),
    ]
    for path in candidates:
        if os.path.isfile(path):
            with io.open(path, encoding="utf-8") as f:
                value = f.read().strip()
            if value:
                return value, path
    return None, None


def body(name):
    with io.open(os.path.join(HERE, name), encoding="utf-8") as f:
        return f.read()


def wipe_token_file(path):
    """Overwrite the token file with zeros and delete it."""
    try:
        size = os.path.getsize(path)
        with io.open(path, "r+b") as f:
            f.write(b"\0" * size)
            f.flush()
        os.remove(path)
        print("Token file wiped and deleted:", path)
    except Exception as exc:
        print("could not wipe token file:", exc)


def main():
    confirm = "--confirm" in sys.argv
    overview_repo = DEFAULT_OVERVIEW_REPO
    for arg in sys.argv[1:]:
        if arg.startswith("--overview-repo="):
            overview_repo = arg.split("=", 1)[1]

    token, source = read_token()
    if not token:
        print("NO TOKEN. Put it into one of these files (one line, no quotes):")
        print("  %USERPROFILE%\\.cache\\huggingface\\token")
        print("  %USERPROFILE%\\Desktop\\hf_token.txt")
        return 2
    print("Token loaded from:", source)

    api = HfApi(token=token)
    who = api.whoami()
    print("Authenticated as:", who.get("name"))

    if not confirm:
        print("\nDRY RUN. Bodies to publish:")
        print("  overview ->", overview_repo, "|", OVERVIEW_TITLE)
        for repo, fname, title in MODEL_POSTS:
            print("  %-55s %s | %s" % (repo, fname, title))
        print("\nRe-run with --confirm to publish.")
        return 0

    overview_body = body(OVERVIEW_FILE)
    ov = api.create_discussion(repo_id=overview_repo, title=OVERVIEW_TITLE,
                               description=overview_body, repo_type="model")
    overview_url = "https://huggingface.co/%s/discussions/%d" % (overview_repo, ov.num)
    print("OVERVIEW:", overview_url)

    published = {"overview": {"repo": overview_repo, "url": overview_url}}
    for repo, fname, title in MODEL_POSTS:
        text = body(fname).replace("{{OVERVIEW_URL}}", overview_url)
        try:
            d = api.create_discussion(repo_id=repo, title=title, description=text, repo_type="model")
            url = "https://huggingface.co/%s/discussions/%d" % (repo, d.num)
            published[fname] = {"repo": repo, "url": url}
            print("POSTED:", url)
        except Exception as exc:  # keep going: one failing repo must not stop the rest
            published[fname] = {"repo": repo, "error": str(exc)[:300]}
            print("FAILED:", repo, "->", str(exc)[:300])

    links = ["Per-model reports:"]
    for repo, fname, _ in MODEL_POSTS:
        item = published.get(fname) or {}
        if item.get("url"):
            links.append("- [%s](%s)" % (repo, item["url"]))
    try:
        api.comment_discussion(repo_id=overview_repo, discussion_num=ov.num,
                               comment="\n".join(links), repo_type="model")
        print("COMMENTED overview with", len(links) - 1, "links")
    except Exception as exc:
        print("comment failed:", str(exc)[:200])

    with io.open(os.path.join(HERE, "published.json"), "w", encoding="utf-8") as f:
        json.dump(published, f, ensure_ascii=False, indent=1)
    print("\nSaved published.json")

    if "--keep-token" not in sys.argv and source and source != "env:HF_TOKEN":
        wipe_token_file(source)
    print("REMINDER: revoke the token on https://huggingface.co/settings/tokens")
    return 0


if __name__ == "__main__":
    sys.exit(main())
