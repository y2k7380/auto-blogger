from core.trend_hunter import TrendHunter
from core.blogger_api import BloggerAPI
import os

def main():
    hunter = TrendHunter()
    
    # 글 쓰기 전 실시간 정보 수집 필수 단계
    hunter.perform_realtime_research([
        "Latest AI Agent trends May 2026",
        "Trending GitHub repositories in Python/Rust",
        "Recent Tech SNS discussions (X/Reddit)"
    ])
    
    trends = hunter.get_trending_topics()
    
    # 피상적인 글이 아닌, 깊이 있는 '마스터피스' 생성 모드 가동
    category = "Professional"
    top_trend = trends[category][0]
    content = hunter.create_masterpiece_post(category, 0)
    
    filename = f"posts/trend_post_{top_trend['topic'].replace(' ', '_').lower()}.md"
    with open(filename, "w") as f:
        f.write(content)
    
    print(f"Trend post generated: {filename}")
    
    # Publish as draft
    api = BloggerAPI()
    title = f"[AI 트렌드] {top_trend['topic']}"
    api.publish_post(
        title=title,
        content=content,
        image_path="./trend_visual.png",
        is_markdown=True,
        is_draft=True
    )

if __name__ == "__main__":
    main()
