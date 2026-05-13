import datetime
import fcntl
import json
import os
import re
import sys
import uuid
from contextlib import contextmanager

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(line_buffering=True)
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(line_buffering=True)

sys.path.append("/home/ubuntu/auto-blogger")

from core.trend_hunter import TrendHunter
from core.blogger_api import BloggerAPI
from core.image_generator import ImageGenerator

BASE_DIR = "/home/ubuntu/auto-blogger"
POSTS_DIR = os.path.join(BASE_DIR, "posts")
HISTORY_FILE = os.path.join(BASE_DIR, "config", "oneoff_history.json")
HISTORY_LOCK_FILE = os.path.join(BASE_DIR, "config", "oneoff_history.lock")


def load_json(path, default):
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


@contextmanager
def file_lock(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as lock_file:
        fcntl.flock(lock_file, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lock_file, fcntl.LOCK_UN)


def save_history(record):
    with file_lock(HISTORY_LOCK_FILE):
        history = load_json(HISTORY_FILE, [])
        history.insert(0, record)
        os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history[:100], f, ensure_ascii=False, indent=2)


def update_history(request_id, **updates):
    with file_lock(HISTORY_LOCK_FILE):
        history = load_json(HISTORY_FILE, [])
        for item in history:
            if item.get("id") == request_id:
                item.update(updates)
                break
        os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history[:100], f, ensure_ascii=False, indent=2)


def extract_title(content, fallback):
    html_title_match = re.search(r'<h1[^>]*>(.*?)</h1>', content, re.IGNORECASE | re.DOTALL)
    markdown_title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
    if html_title_match:
        return re.sub(r'<[^>]+>', '', html_title_match.group(1)).strip()
    if markdown_title_match:
        return markdown_title_match.group(1).strip()
    return fallback


def infer_topic_seed(prompt):
    for raw_line in prompt.splitlines():
        line = raw_line.strip()
        if not line or line.startswith(("http://", "https://")):
            continue
        line = re.sub(r'^[#>*\-\d\.\)\s]+', '', line).strip()
        line = re.sub(r'https?://\S+', '', line).strip()
        if len(line) >= 8:
            return line[:90]
    compact = re.sub(r'\s+', ' ', re.sub(r'https?://\S+', '', prompt)).strip()
    return compact[:90] if compact else "사용자 입력 자료 기반 마스터피스 블로그"


def main():
    if len(sys.argv) < 2:
        print("Error: request JSON path required")
        sys.exit(1)

    request_path = sys.argv[1]
    with open(request_path, "r", encoding="utf-8") as f:
        request = json.load(f)

    request_id = request.get("id") or str(uuid.uuid4())[:8]
    user_topic = (request.get("topic") or "").strip()
    prompt = (request.get("prompt") or "").strip()
    auto_title = bool(request.get("auto_title")) or not user_topic
    topic = user_topic if not auto_title else infer_topic_seed(prompt)
    persona = request.get("persona") or "Masterpiece"
    publish_mode = request.get("publish_mode") or "live"
    is_draft = publish_mode == "draft"

    if not prompt:
        print("Error: prompt is required")
        update_history(request_id, status="failed", message="prompt is required", finished_at=datetime.datetime.now().isoformat(timespec="seconds"))
        sys.exit(1)

    print(f"\n=== One-off [{request_id}] Started: {datetime.datetime.now()} ===")
    print(f"Topic: {topic}")
    print(f"Auto title: {'yes' if auto_title else 'no'}")
    print(f"Persona: {persona}")
    print(f"Publish mode: {'draft' if is_draft else 'live'}")

    update_history(request_id, status="running", started_at=datetime.datetime.now().isoformat(timespec="seconds"))

    hunter = TrendHunter()
    api = BloggerAPI()
    img_gen = ImageGenerator()

    rules = f"""
[단발성 마스터피스 작성 요청]
사용자가 아래에 붙인 내용은 주제일 수도 있고, 링크 목록일 수도 있고, 외부에서 조사한 심층 자료일 수도 있습니다.
이 자료를 단순 복사하지 말고 핵심 주장, 근거, 반론, 실무적 의미를 재구성해 하나의 완성된 마스터피스 블로그로 작성하세요.
링크가 포함되어 있다면 링크 자체를 제목처럼 나열하지 말고, 링크가 암시하는 쟁점과 독자에게 필요한 판단 기준을 중심으로 해석하세요.
자료가 단편적이면 무리하게 사실을 꾸며내지 말고, 확인 가능한 범위와 추론을 구분하세요.
{"사용자가 별도 제목을 입력하지 않았습니다. 아래 자료 전체를 읽고 클릭을 유도하면서도 본문에서 반드시 회수되는 강한 H1 제목을 직접 만드세요. 임시 주제 문구를 그대로 제목으로 쓰지 마세요." if auto_title else "사용자가 입력한 제목 방향을 존중하되, 본문에서 회수되는 더 강한 H1 제목으로 다듬어도 됩니다."}

[사용자 입력 자료]
{prompt}
"""

    try:
        content = hunter.create_masterpiece_post(custom_topic=topic, custom_rules=rules, persona=persona)

        os.makedirs(POSTS_DIR, exist_ok=True)
        stamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        draft_path = os.path.join(POSTS_DIR, f"oneoff_{request_id}_{stamp}.md")
        with open(draft_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"📝 단발성 원문 저장 완료: {draft_path}")

        print("🎨 본문 문맥에 맞는 미디어(이미지)를 생성합니다...")
        image_path = os.path.join(POSTS_DIR, f"oneoff_{request_id}_{stamp}.png")
        img_success = img_gen.generate_image(topic, image_path)
        final_image = image_path if img_success and os.path.exists(image_path) else os.path.join(BASE_DIR, "trend_visual.png")

        title = extract_title(content, f"[마스터피스] {topic}")
        print("🚀 블로거 API를 통해 단발성 포스트를 발행합니다...")
        published_url = api.publish_post(
            title=title,
            content=content,
            image_path=final_image,
            is_markdown=True,
            is_draft=is_draft,
        )
        status = "completed" if published_url else "failed"
        update_history(
            request_id,
            status=status,
            title=title,
            url=published_url if isinstance(published_url, str) else "",
            draft_path=draft_path,
            finished_at=datetime.datetime.now().isoformat(timespec="seconds"),
            message="published" if published_url else "publish failed",
        )
        print(f"✅ One-off [{request_id}] Finished: {datetime.datetime.now()} ===\n")
        sys.exit(0 if published_url else 1)
    except Exception as e:
        update_history(
            request_id,
            status="failed",
            message=str(e),
            finished_at=datetime.datetime.now().isoformat(timespec="seconds"),
        )
        print(f"❌ One-off [{request_id}] Failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
