#!/usr/bin/env python3
"""اعمال لینک‌های تأییدشدهٔ دستی کاربر + حذف ۷ اسکیل مرده

- لینک‌های blob/.../SKILL.md به tree تبدیل و اول نسخهٔ HEAD تست می‌شود؛
  اگر HEAD نبود، همان ref کاربر (SHA/main) و در نهایت URL دقیق کاربر نگه داشته می‌شود.
- ۷ اسکیلِ «حذف شود» از دیتاست بیرون می‌روند و در removed.jsonl ثبت می‌شوند
  تا update_index.py دیگر آن‌ها را برنگرداند.
"""
import json, os, time, threading
import requests

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, 'skills-index-flat.jsonl')
REMOVED = os.path.join(HERE, 'removed.jsonl')
S = requests.Session()
S.headers.update({'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/131.0 Safari/537.36',
                  'Accept-Encoding': 'gzip'})
_lock, _next = threading.Lock(), [0.0]

def head(url):
    with _lock:
        n = max(_next[0], time.monotonic()); _next[0] = n + 0.3
    t = n - time.monotonic()
    if t > 0: time.sleep(t)
    for _ in range(2):
        try:
            r = S.head(url, timeout=20, allow_redirects=True)
            if r.status_code != 429: return r.status_code
            time.sleep(6)
        except requests.RequestException:
            time.sleep(3)
    return 0

# key ← لینک ارائه‌شده توسط کاربر (keys دقیقاً مطابق flat)
LINKS = {
 "better-auth/email-&amp;-password-best-practices": "https://github.com/better-auth/skills/blob/20c9e88a5c007461a703f1c213572b073196113e/better-auth/emailAndPassword/SKILL.md",
 "canva/social-media-resize": "https://github.com/canva-sdks/canva-skills/blob/main/plugins/canva/skills/resize-for-social-media/SKILL.md",
 "cloudflare/building-ai-agent-on-cloudflare": "https://github.com/cloudflare/skills/blob/main/skills/agents-sdk/SKILL.md",
 "cloudflare/building-mcp-server-on-cloudflare": "https://github.com/cloudflare/skills/blob/main/skills/agents-sdk/SKILL.md",
 "cloudflare/sandbox-sdk": "https://github.com/cloudflare/skills/blob/main/skills/sandbox-stable/SKILL.md",
 "figma/figma-code-connect-components": "https://github.com/figma/mcp-server-guide/blob/main/figma-power/steering/code-connect-components.md",
 "figma/figma-create-design-system-rules": "https://github.com/figma/mcp-server-guide/blob/main/figma-power/steering/create-design-system-rules.md",
 "figma/figma-implement-design": "https://github.com/figma/mcp-server-guide/blob/main/figma-power/steering/implement-design.md",
 "huggingface/hugging-face-cli": "https://github.com/huggingface/skills/blob/main/skills/hf-cli/SKILL.md",
 "huggingface/hugging-face-datasets": "https://github.com/huggingface/skills/blob/main/skills/huggingface-datasets/SKILL.md",
 "huggingface/hugging-face-jobs": "https://github.com/huggingface/skills/blob/main/skills/huggingface-llm-trainer/SKILL.md",
 "huggingface/hugging-face-model-trainer": "https://github.com/huggingface/skills/blob/main/skills/huggingface-llm-trainer/SKILL.md",
 "huggingface/hugging-face-paper-publisher": "https://github.com/huggingface/skills/blob/main/skills/huggingface-paper-publisher/SKILL.md",
 "huggingface/hugging-face-tool-builder": "https://github.com/huggingface/skills/blob/main/skills/huggingface-tool-builder/SKILL.md",
 "huggingface/hugging-face-trackio": "https://github.com/huggingface/skills/blob/main/skills/huggingface-trackio/SKILL.md",
 "langchain-ai/deep-agents-memory-&amp;-filesystem": "https://github.com/langchain-ai/langchain-skills/blob/main/config/skills/deep-agents-memory/SKILL.md",
 "langchain-ai/langchain-middleware-&amp;-hitl": "https://github.com/langchain-ai/langchain-skills/blob/main/config/skills/langchain-middleware/SKILL.md",
 "langchain-ai/langchain-structured-output-&amp;-hitl": "https://github.com/langchain-ai/langchain-skills/blob/main/config/skills/langchain-fundamentals/SKILL.md",
 "langchain-ai/langgraph-persistence-&amp;-memory": "https://github.com/langchain-ai/langchain-skills/blob/main/config/skills/langgraph-persistence/SKILL.md",
 "microsoft/azure-cost-optimization": "https://github.com/microsoft/GitHub-Copilot-for-Azure/blob/main/plugins/azure-cost/skills/cost-optimization/SKILL.md",
 "sentry/sentry-setup-logging": "https://github.com/getsentry/sentry-for-ai/blob/main/src/skills/sentry-instrument/SKILL.md",
 "sentry/sentry-setup-metrics": "https://github.com/getsentry/sentry-for-ai/blob/main/src/skills/sentry-instrument/SKILL.md",
 "sentry/sentry-setup-tracing": "https://github.com/getsentry/sentry-for-ai/blob/main/src/skills/sentry-instrument/SKILL.md",
}
REMOVE = [
 ("huggingface/hugging-face-evaluation", "اسکیل در ریپوی huggingface/skills وجود ندارد (تأیید دستی کاربر)"),
 ("microsoft/azure-hosted-copilot-sdk", "منبع گیتهاب ندارد / مرده (تأیید دستی کاربر)"),
 ("microsoft/azure-observability", "منبع گیتهاب ندارد / مرده (تأیید دستی کاربر)"),
 ("microsoft/azure-rbac", "منبع گیتهاب ندارد / مرده (تأیید دستی کاربر)"),
 ("zapier/code-review", "منبع گیتهاب ندارد / مرده (تأیید دستی کاربر)"),
 ("zapier/git-commit", "منبع گیتهاب ندارد / مرده (تأیید دستی کاربر)"),
 ("zapier/work-on-ticket", "منبع گیتهاب ندارد / مرده (تأیید دستی کاربر)"),
]

def resolve(key, url):
    """tree/HEAD ترجیح، بعد ref کاربر، بعد URL دقیق کاربر."""
    if '/blob/' not in url:
        return url, head(url)
    pre, post = url.split('/blob/', 1)
    ref, path = post.split('/', 1)
    dirpath = path.rsplit('/', 1)[0]
    cands = [(f"{pre}/tree/HEAD/{dirpath}", 'HEAD')]
    if ref not in ('HEAD', 'main', 'master'):
        cands.append((f"{pre}/tree/{ref}/{dirpath}", f'pin:{ref[:8]}'))
    elif ref != 'HEAD':
        cands.append((f"{pre}/tree/{ref}/{dirpath}", ref))
    cands.append((url, 'exact'))
    for u, tag in cands:
        c = head(u)
        if c == 200:
            return u, tag
    return cands[-1][0], f'⚠{c}'

def main():
    rows = [json.loads(l) for l in open(SRC, encoding='utf-8')]
    byk = {f"{r['author']}/{r['name']}": r for r in rows}
    print("── تأیید و اعمال لینک‌ها ──")
    applied = 0
    for k, url in LINKS.items():
        final, tag = resolve(k, url)
        if k in byk:
            byk[k]['github'] = final; applied += 1
        print(f"  {tag:<16} {k}")
    print(f"اعمال‌شده: {applied}/23")

    # حذف‌ها
    remove_keys = {k for k, _ in REMOVE}
    with open(REMOVED, 'w', encoding='utf-8') as f:
        for k, why in sorted(REMOVE):
            f.write(json.dumps({'key': k, 'reason': why}, ensure_ascii=False) + '\n')
    kept = [r for r in rows if f"{r['author']}/{r['name']}" not in remove_keys]
    print(f"\nحذف‌شده: {len(rows) - len(kept)} | باقی: {len(kept):,}")
    tmp = SRC + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        for r in kept: f.write(json.dumps(r, ensure_ascii=False) + '\n')
    os.replace(tmp, SRC)
    nogh = sum(1 for r in kept if not r.get('github', '').startswith('http'))
    print(f"بدون گیتهاب در دیتاست جدید: {nogh}")

if __name__ == '__main__':
    main()
