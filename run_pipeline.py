import sys
import json
import os
import datetime
import re
import uuid
import logging

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

# Add auto-blogger to path
sys.path.append("/home/ubuntu/auto-blogger")

from core.trend_hunter import TrendHunter
from core.blogger_api import BloggerAPI
from core.image_generator import ImageGenerator

if len(sys.argv) < 2:
    logger.error("Pipeline ID required")
    sys.exit(1)

pipeline_id = sys.argv[1]
PIPELINES_FILE = "/home/ubuntu/auto-blogger/config/pipelines.json"

with open(PIPELINES_FILE, 'r') as f:
    pipelines = json.load(f)

pipeline = next((p for p in pipelines if p['id'] == pipeline_id), None)
if not pipeline:
    logger.error(f"Pipeline {pipeline_id} not found.")
    sys.exit(1)

topic = pipeline.get('topic', 'General Tech')
persona = pipeline.get('persona', 'Masterpiece')
rules = pipeline.get('rules', '')

logger.info(f"=== Pipeline [{pipeline_id}] Started ===")
logger.info(f"Topic: {topic}")
logger.info(f"Persona: {persona}")
logger.info(f"Rules: {rules}")

# 1. Initialize
hunter = TrendHunter()
api = BloggerAPI()
img_gen = ImageGenerator()

# 2. Generate Masterpiece
run_stamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
run_nonce = str(uuid.uuid4())[:6]

logger.info(f"✍️ AI 작가들이 '{topic}'에 대한 깊이 있는 통찰을 수집하고 집필을 시작합니다...")
content = hunter.create_masterpiece_post(custom_topic=topic, custom_rules=rules, persona=persona)

# 3. Save draft for quality audit
abs_post_dir = os.path.abspath("/home/ubuntu/auto-blogger/posts")
if not os.path.exists(abs_post_dir):
    os.makedirs(abs_post_dir)
draft_name = f"pipeline_{pipeline_id}_{run_stamp}_{run_nonce}.md"
draft_path = os.path.join(abs_post_dir, draft_name)
with open(draft_path, "w", encoding="utf-8") as f:
    f.write(content)
logger.info(f"📝 품질 검수용 원문 저장 완료: {draft_path}")

# 4. Generate Image
logger.info(f"🎨 본문 문맥에 맞는 미디어(이미지)를 생성합니다...")
fresh_image_name = f"pipe_{pipeline_id}_{run_stamp}_{run_nonce}.png"
fresh_image_path = os.path.join(abs_post_dir, fresh_image_name)

img_success = img_gen.generate_image(topic, fresh_image_path)
final_image = fresh_image_path if img_success and os.path.exists(fresh_image_path) else "/home/ubuntu/auto-blogger/trend_visual.png"

# 5. Extract Title
html_title_match = re.search(r'<h1[^>]*>(.*?)</h1>', content, re.IGNORECASE | re.DOTALL)
markdown_title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
if html_title_match:
    title = html_title_match.group(1).strip()
    title = re.sub(r'<[^>]+>', '', title)
elif markdown_title_match:
    title = markdown_title_match.group(1).strip()
else:
    title = f"[{persona} 인사이트] {topic}"

# 6. Publish
logger.info(f"🚀 블로거 API를 통해 최종 퍼블리싱을 진행합니다...")
api.publish_post(
    title=title,
    content=content,
    image_path=final_image, 
    is_markdown=True,
    is_draft=False  # Publish directly based on pipeline
)

logger.info(f"✅ Pipeline [{pipeline_id}] Finished ===")
