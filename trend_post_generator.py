from core.trend_hunter import TrendHunter
from core.blogger_api import BloggerAPI
from core.image_generator import ImageGenerator
import os
import sys
import datetime
import re
import uuid

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(line_buffering=True)
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(line_buffering=True)

def safe_slug(value, max_length=80):
    slug = re.sub(r'[^0-9A-Za-z가-힣_-]+', '_', value.strip())
    slug = re.sub(r'_+', '_', slug).strip('_').lower()
    return (slug or "post")[:max_length]

def unique_post_paths(topic):
    os.makedirs("posts", exist_ok=True)
    stamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    nonce = str(uuid.uuid4())[:6]
    slug = safe_slug(topic)
    base = f"{slug}_{stamp}_{nonce}"
    return {
        "content": os.path.join("posts", f"trend_post_{base}.md"),
        "image": os.path.abspath(os.path.join("posts", f"image_{base}.png")),
    }

def main():
    hunter = TrendHunter()
    
    # 오늘(2026-05-12)의 생생한 팩트와 기술적 돌파구를 찾기 위한 초정밀 쿼리
    hunter.perform_realtime_research([
        "Breaking AI news May 12 2026",
        "New GitHub trending repos for AI Agents May 2026",
        "Anthropic/OpenAI/Google latest model updates this week",
        "Technical deep dive into current LLM optimization trends"
    ])
    
    trends = hunter.get_trending_topics()
    
    # 피상적인 글이 아닌, 깊이 있는 '마스터피스' 생성 모드 가동
    category = "Professional"
    top_trend = trends[category][0]
    
    print(f"🌟 '{top_trend['topic']}'에 대한 자율 마스터피스 발행 프로세스를 시작합니다...")
    content = hunter.create_masterpiece_post(category, 0)
    
    paths = unique_post_paths(top_trend['topic'])
    filename = paths["content"]
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)
    
    print(f"Trend post generated: {filename}")
    
    # 2. 이미지 자율 생성 단계 추가 (Codex 사용)
    img_gen = ImageGenerator()
    fresh_image_path = paths["image"]
    
    img_success = img_gen.generate_image(top_trend['topic'], fresh_image_path)
    
    # 생성 실패 시 기본 이미지 폴백
    final_image = fresh_image_path if img_success and os.path.exists(fresh_image_path) else "./trend_visual.png"

    # 3. 블로그 발행 (제목을 LLM이 만든 내용에서 추출하거나 동적으로 생성)
    api = BloggerAPI()
    
    # 텍스트 내에서 첫 번째 H1을 찾아 제목으로 사용 (트렌디한 제목 반영)
    import re
    html_title_match = re.search(r'<h1[^>]*>(.*?)</h1>', content, re.IGNORECASE | re.DOTALL)
    markdown_title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
    if html_title_match:
        title = re.sub(r'<[^>]+>', '', html_title_match.group(1)).strip()
    elif markdown_title_match:
        title = markdown_title_match.group(1).strip()
    else:
        title = f"[AI 인사이트] {top_trend['topic']}"
    
    api.publish_post(
        title=title,
        content=content,
        image_path=final_image, 
        is_markdown=True,
        is_draft=True
    )

if __name__ == "__main__":
    main()
