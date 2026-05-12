import argparse
import os
from core.blogger_api import BloggerAPI

def main():
    parser = argparse.ArgumentParser(description="Auto-Blogger CLI")
    parser.add_argument("--file", help="Path to markdown file", default="posts/sample_post.md")
    parser.add_argument("--title", help="Post title", default="AI 에이전트 군단 구축기 (Automated)")
    parser.add_argument("--image", help="Path to image", default="./ai_coding_agent_army.png")
    parser.add_argument("--draft", action="store_true", help="Save as draft")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.file):
        print(f"File not found: {args.file}")
        return

    with open(args.file, "r") as f:
        content = f.read()

    api = BloggerAPI()
    api.publish_post(
        title=args.title,
        content=content,
        image_path=args.image,
        is_markdown=True,
        is_draft=args.draft
    )

if __name__ == "__main__":
    main()
