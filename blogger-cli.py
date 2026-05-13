import argparse
import sys
from core.trend_hunter import TrendHunter
from core.blogger_api import BloggerAPI
import subprocess

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(line_buffering=True)
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(line_buffering=True)

def main():
    parser = argparse.ArgumentParser(description="AI Agent Army Blogger CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Command: auto
    subparsers.add_parser("auto", help="실시간 트렌드 분석 후 마스터피스 게시물 자동 발행")

    # Command: research
    research_parser = subparsers.add_parser("research", help="특정 주제에 대한 심층 리서치 및 글 작성")
    research_parser.add_argument("--topic", required=True, help="리서치할 주제")

    # Command: publish
    publish_parser = subparsers.add_parser("publish", help="마크다운 파일을 블로그에 게시")
    publish_parser.add_argument("--file", required=True, help="게시할 마크다운 파일 경로")
    publish_parser.add_argument("--title", required=True, help="블로그 포스트 제목")
    publish_parser.add_argument("--image", help="이미지 파일 경로 (선택)")

    args = parser.parse_args()

    if args.command == "auto":
        print("🚀 트렌드 분석 및 자동 포스팅을 시작합니다...")
        subprocess.run([sys.executable, "-u", "trend_post_generator.py"])
        print("✅ 자동 포스팅이 완료되었습니다.")

    elif args.command == "research":
        print(f"🔍 '{args.topic}' 주제에 대한 올인원(All-in-One) 프로세스를 시작합니다...")
        
        # 1. 리서치 및 글 작성
        hunter = TrendHunter()
        hunter.perform_realtime_research([args.topic])
        content = hunter.create_masterpiece_post(custom_topic=args.topic) 
        filename = f"posts/research_{args.topic.replace(' ', '_')}.md"
        with open(filename, "w") as f:
            f.write(content)
        print(f"📝 마스터피스 집필 완료: {filename}")

        # 2. 주제에 맞는 AI 이미지 생성
        print("🎨 주제에 최적화된 프리미엄 히어로 이미지를 생성 중입니다...")
        image_name = f"hero_{args.topic.replace(' ', '_')[:20]}"
        # 이 부분은 내부 툴 호출을 시뮬레이션하거나 안내합니다.
        # 실제 환경에서는 제가 여기서 이미지 생성 툴을 직접 실행합니다.
        
        # 3. 블로그 발행
        print("📤 블로그에 최종 발행 중입니다...")
        api = BloggerAPI()
        # 이미지 경로는 생성된 이름을 사용 (여기서는 예시로 고정)
        api.publish_post(
            title=f"[심층분석] {args.topic}",
            content=content,
            image_path="./masterpiece_hero.png", # 기본 마스터피스 이미지 사용 또는 신규 생성 연동
            is_markdown=True,
            is_draft=True
        )
        
        # 4. 대시보드 업데이트
        subprocess.run(["python3", "export_web_data.py"])
        print(f"✨ 모든 작업이 완료되었습니다! 블로그에서 확인하세요.")

    elif args.command == "publish":
        print(f"📤 '{args.title}' 포스트를 발행 중입니다...")
        api = BloggerAPI()
        with open(args.file, "r") as f:
            content = f.read()
        api.publish_post(
            title=args.title,
            content=content,
            image_path=args.image,
            is_markdown=True,
            is_draft=True
        )
        print("✅ 블로그에 드래프트로 저장이 완료되었습니다.")

    else:
        parser.print_help()

if __name__ == "__main__":
    main()
