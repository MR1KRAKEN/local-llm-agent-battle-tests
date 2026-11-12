r"""
Publishes the flint-24B agentic test post to a Hugging Face model discussion.

Usage:
    python publish_flint.py                 # dry run
    python publish_flint.py --confirm       # actually publish

Token is read from HF_TOKEN or %USERPROFILE%\.cache\huggingface\token and is wiped after use.
"""
import io
import json
import os
import sys

from huggingface_hub import HfApi

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = "lmstudio-community/flint-GGUF"
BODY = "flint-24b.md"
TITLE = ("Agentic coding test: flint-24B Q4_K_M - 55-62 tok/s, but 32k tokens of reasoning and zero tool calls")
OVERVIEW_URL = "https://huggingface.co/openai/gpt-oss-20b/discussions/278"
TOKEN_FILE = os.path.join(os.path.expanduser("~"), ".cache", "huggingface", "token")


def read_token():
    token = os.environ.get("HF_TOKEN") or os.environ.get("HUGGING_FACE_HUB_TOKEN")
    if token:
        return token.strip()
    with io.open(TOKEN_FILE, "r", encoding="utf-8", errors="ignore") as f:
        return f.read().strip()


def wipe_token():
    if not os.path.exists(TOKEN_FILE):
        return False
    try:
        size = os.path.getsize(TOKEN_FILE)
        with io.open(TOKEN_FILE, "r+b") as f:
            f.write(b"\0" * size)
            f.flush()
        os.remove(TOKEN_FILE)
        return True
    except Exception:
        return False


def main():
    confirm = "--confirm" in sys.argv
    with io.open(os.path.join(HERE, BODY), "r", encoding="utf-8") as f:
        body = f.read().replace("{{OVERVIEW_URL}}", OVERVIEW_URL)

    token = read_token()
    if not token:
        print("нет токена")
        return 1
    api = HfApi(token=token)
    try:
        me = api.whoami()
        print("аккаунт:", me.get("name"))
    except Exception as e:
        print("whoami не удался:", str(e)[:120])
        return 1

    print("репозиторий:", REPO)
    print("заголовок:", TITLE)
    print("длина тела:", len(body), "символов")

    if not confirm:
        print("\nDRY RUN. Запусти с --confirm, чтобы опубликовать.")
        return 0

    url = api.create_discussion(repo_id=REPO, repo_type="model", title=TITLE, description=body)
    print("опубликовано:", url)

    path = os.path.join(HERE, "published.json")
    data = {}
    if os.path.exists(path):
        with io.open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    data[BODY] = {"repo": REPO, "url": url}
    with io.open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print("записано в published.json")
    return 0


if __name__ == "__main__":
    code = main()
    if "--confirm" in sys.argv:
        print("токен затёрт:", wipe_token())
    sys.exit(code)
