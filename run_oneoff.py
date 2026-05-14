import datetime
import fcntl
import json
import os
import re
import sys
import uuid
import logging
from contextlib import contextmanager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

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
        logger.error("Error: request JSON path required")
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
        logger.error("Error: prompt is required")
        update_history(request_id, status="failed", message="prompt is required", finished_at=datetime.datetime.now().isoformat(timespec="seconds"))
        sys.exit(1)

    logger.info(f"=== One-off [{request_id}] Started ===")
    logger.info(f"Topic: {topic}")
    logger.info(f"Auto title: {'yes' if auto_title else 'no'}")
    logger.info(f"Persona: {persona}")
    logger.info(f"Publish mode: {'draft' if is_draft else 'live'}")

    update_history(request_id, status="running", started_at=datetime.datetime.now().isoformat(timespec="seconds"))

    hunter = TrendHunter()
    api = BloggerAPI()
    img_gen = ImageGenerator()

    rules = f"""
[단발성 블로그 작성 요청]
사용자가 아래에 붙인 내용은 주제일 수도 있고, 링크 목록일 수도 있고, 외부에서 조사한 심층 자료일 수도 있습니다.
이 자료를 단순 복사하지 말고, 독자가 읽고 '이건 저장해둬야겠다'고 느끼는 글로 재구성하세요.

[글쓰기 핵심 원칙]
1. AI가 쓴 글처럼 보이면 실패. '~의 시대가 도래했습니다' 같은 거창한 선언, 모든 문단을 '~입니다'로 끝내기, 기계적 나열 금지.
2. 대신 '솔직히 말하면~', '제가 실제로 겪어본 바로는~', '근데 함정이 하나 있어요' 같은 자연스러운 톤 사용.
3. 어미를 ~입니다/~거든요/~예요/~죠/~했어요 등으로 자연스럽게 섞으세요.
4. 전문 용어가 나오면 반드시 (쉬운 설명) 병기 또는 '쉽게 말해~' 보충.
5. 반드시 '이번 주에 바로 해볼 수 있는 것' 섹션 포함. 실제 도구명, 명령어, URL 등 구체적 액션을 담으세요.
6. 확인되지 않은 수치는 '약~', '추정~'으로 표현. 뻔한 홍보 문장 금지.
7. 독자에게 직접 말 걸기: '여러분이 만약~', '한번 상상해 보세요' 등 2인칭 표현 활용.
{"사용자가 별도 제목을 입력하지 않았습니다. 아래 자료 전체를 읽고 호기심을 자극하면서도 본문에서 반드시 회수되는 강한 H1 제목을 직접 만드세요. 임시 주제 문구를 그대로 제목으로 쓰지 마세요." if auto_title else "사용자가 입력한 제목 방향을 존중하되, 본문에서 회수되는 더 강한 H1 제목으로 다듬어도 됩니다."}

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
        logger.info(f"📝 단발성 원문 저장 완료: {draft_path}")

        logger.info("🎨 본문 문맥에 맞는 미디어(이미지)를 생성합니다...")
        image_path = os.path.join(POSTS_DIR, f"oneoff_{request_id}_{stamp}.png")
        img_success = img_gen.generate_image(topic, image_path)
        final_image = image_path if img_success and os.path.exists(image_path) else os.path.join(BASE_DIR, "trend_visual.png")

        title = extract_title(content, f"[마스터피스] {topic}")
        logger.info("🚀 블로거 API를 통해 단발성 포스트를 발행합니다...")
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
        logger.info(f"✅ One-off [{request_id}] Finished ===")
        sys.exit(0 if published_url else 1)
    except Exception as e:
        update_history(
            request_id,
            status="failed",
            message=str(e),
            finished_at=datetime.datetime.now().isoformat(timespec="seconds"),
        )
        logger.error(f"❌ One-off [{request_id}] Failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
