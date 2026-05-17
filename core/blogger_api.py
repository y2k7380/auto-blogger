import os
import json
import subprocess
import requests
import base64
import markdown
import re
import logging

logger = logging.getLogger(__name__)

class BloggerAPI:
    def __init__(self, settings_path="config/settings.json"):
        with open(settings_path, "r") as f:
            self.settings = json.load(f)
        self.blog_id = self.settings.get("blog_id")

    def get_access_token(self):
        try:
            env = os.environ.copy()
            env["PATH"] = f"/home/ubuntu/.local/share/fnm/node-versions/v20.20.2/installation/bin:{env.get('PATH', '')}"
            output = subprocess.check_output(["gws", "auth", "export", "--unmasked"], stderr=subprocess.STDOUT, env=env).decode()
            start = output.find('{')
            end = output.rfind('}') + 1
            creds = json.loads(output[start:end])
            
            refresh_token = creds.get("refresh_token")
            client_id = creds.get("client_id")
            client_secret = creds.get("client_secret")
            
            if not refresh_token:
                logger.error("Error: No refresh token found in gws output.")
                return None
                
            response = requests.post("https://oauth2.googleapis.com/token", data={
                "client_id": client_id,
                "client_secret": client_secret,
                "refresh_token": refresh_token,
                "grant_type": "refresh_token"
            })
            
            if response.status_code == 200:
                return response.json().get("access_token")
            else:
                logger.error(f"Error refreshing token: {response.status_code} - {response.text}")
                return None
        except FileNotFoundError:
            logger.error("Error: 'gws' CLI not found. Please install or ensure it is in PATH.")
            return None
        except subprocess.CalledProcessError as e:
            logger.error(f"Error executing gws: {e.output.decode() if e.output else str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting token: {e}")
            return None

    def get_base64_image(self, image_path):
        if not os.path.exists(image_path):
            return None
            
        try:
            from PIL import Image
            import io
            
            # 이미지 최적화 (압축 및 리사이징)
            with Image.open(image_path) as img:
                # 최대 너비를 1100px로 조정 (가독성 최적화)
                if img.width > 1100:
                    aspect_ratio = img.height / img.width
                    new_height = int(1100 * aspect_ratio)
                    img = img.resize((1100, new_height), Image.Resampling.LANCZOS)
                
                # 용량 압축을 위해 JPEG로 변환하여 메모리에 저장
                buffer = io.BytesIO()
                # 원본이 PNG여도 용량을 위해 JPEG로 변환 (투명도가 필요 없는 배경용)
                if img.mode in ("RGBA", "P"):
                    img = img.convert("RGB")
                img.save(buffer, format="JPEG", quality=85, optimize=True)
                return base64.b64encode(buffer.getvalue()).decode('utf-8')
        except Exception as e:
            logger.warning(f"⚠️ 이미지 최적화 중 오류 발생 (원본 사용 시도): {e}")
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')

    def normalize_related_posts_marker(self, md_content):
        pattern = r'\n+###\s*함께 읽으면 좋은 글\s*\n+(?:\s*[-*]\s+.*\n*){0,8}'
        md_content = re.sub(pattern, "\n\n[RELATED_POSTS]\n", md_content, flags=re.MULTILINE)
        return md_content

    def convert_markdown_to_html(self, md_content, image_path=None):
        md_content = self.normalize_related_posts_marker(md_content)
        # 마크다운 렌더링 (HTML 태그 허용)
        html_content = markdown.markdown(md_content)
        
        if image_path and os.path.exists(image_path):
            b64_data = self.get_base64_image(image_path)
            if b64_data:
                # 레이아웃 겹침 방지 및 완벽한 중앙 정렬 래퍼
                style = f'width:100%; max-width:{self.settings.get("max_image_width", "1100px")}; display:block; margin: 0 auto; border-radius:15px; box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);'
                alt_text = os.path.basename(image_path).replace(".png", "").replace("_", " ").title()
                image_html = f"""
                <div style="margin: 4rem 0; text-align: center; clear: both; width: 100%;">
                    <img src="data:image/png;base64,{b64_data}" alt="{alt_text}" style="{style}">
                    <p style="color: #64748b; font-size: 0.85rem; margin-top: 1.5rem; font-style: italic; text-align: center;">▲ {alt_text}</p>
                </div>
                """
                if "[IMAGE_PLACEHOLDER]" in html_content:
                    html_content = html_content.replace("[IMAGE_PLACEHOLDER]", image_html)
                else:
                    html_content = image_html + html_content
                    
        # 프리미엄 마스터피스 CSS 강제 주입
        masterpiece_css = """
        <style>
          @import url('https://fonts.googleapis.com/css2?family=Pretendard:wght@300;400;500;700;900&display=swap');
          .masterpiece-container { font-family: 'Pretendard', -apple-system, sans-serif; line-height: 2.05; color: #334155; max-width: 780px; margin: 0 auto; padding: 0 24px; word-break: keep-all; }
          .masterpiece-container h1 { font-size: 2.4rem; font-weight: 900; margin-bottom: 1rem; color: #0f172a; line-height: 1.35; letter-spacing: -0.5px; }
          .masterpiece-container h2 { font-size: 1.6rem; font-weight: 800; margin-top: 56px; margin-bottom: 20px; color: #0f172a; padding-bottom: 10px; border-bottom: 2px solid #e2e8f0; display: block; }
          .masterpiece-container h3 { font-size: 1.25rem; color: #475569; margin-top: 32px; font-weight: 700; }
          .masterpiece-container p { font-size: 1.08rem; margin-bottom: 22px; color: #475569; letter-spacing: -0.01em; }
          .masterpiece-container ul, .masterpiece-container ol { margin: 16px 0 24px 20px; color: #475569; font-size: 1.05rem; }
          .masterpiece-container li { margin-bottom: 8px; line-height: 1.85; }
          .masterpiece-container blockquote { border-left: 4px solid #6366f1; padding: 18px 24px; margin: 32px 0; background: #f8fafc; font-size: 1.12rem; font-weight: 500; color: #334155; border-radius: 0 8px 8px 0; font-style: normal; }
          .masterpiece-container strong { color: #1e293b; font-weight: 700; }
          .masterpiece-container code { background: #f1f5f9; padding: 2px 7px; border-radius: 4px; font-size: 0.92em; color: #6366f1; font-family: 'JetBrains Mono', monospace; }
          .masterpiece-container pre { background: #1e293b; color: #e2e8f0; padding: 20px; border-radius: 10px; overflow-x: auto; margin: 24px 0; font-size: 0.9rem; line-height: 1.7; }
          .masterpiece-container hr { border: none; border-top: 1px solid #e2e8f0; margin: 48px 0; }
          .masterpiece-container a { color: #6366f1; text-decoration: underline; text-underline-offset: 3px; }
        </style>
        """
        
        # 전체 래퍼 씌우기
        html_content = f"{masterpiece_css}\n<div class='masterpiece-container'>\n{html_content}\n</div>"
        
        return html_content

    def get_related_posts_html(self):
        token = self.get_access_token()
        if not token: return ""
        
        try:
            url = f"https://www.googleapis.com/blogger/v3/blogs/{self.blog_id}/posts?maxResults=3"
            headers = {"Authorization": f"Bearer {token}"}
            resp = requests.get(url, headers=headers)
            if resp.status_code == 200:
                posts = resp.json().get("items", [])
                if not posts: return ""
                html = '<div style="background:#f8fafc; padding:1rem; border-radius:10px; border:1px solid #e2e8f0; margin-top:2rem;">'
                html += '<h3 style="margin-top:0;">함께 읽으면 좋은 글</h3><ul>'
                for p in posts:
                    html += f'<li><a href="{p["url"]}">{p["title"]}</a></li>'
                html += '</ul></div>'
                return html
        except:
            return ""
        return ""

    def publish_post(self, title, content, image_path=None, is_markdown=True, is_draft=False):
        token = self.get_access_token()
        if not token:
            logger.error("Failed to obtain access token.")
            return False
        
        if is_markdown:
            final_content = self.convert_markdown_to_html(content, image_path)
        else:
            final_content = content

        # SEO: Add Related Posts
        related_html = self.get_related_posts_html()
        if "[RELATED_POSTS]" in final_content:
            final_content = final_content.replace("<p>[RELATED_POSTS]</p>", related_html)
            final_content = final_content.replace("[RELATED_POSTS]", related_html)
        else:
            final_content += related_html

        url = f"https://www.googleapis.com/blogger/v3/blogs/{self.blog_id}/posts"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        data = {
            "title": title,
            "content": final_content,
            "status": "DRAFT" if is_draft else "LIVE"
        }
        
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            result = response.json()
            logger.info(f"Success! Post {'drafted' if is_draft else 'published'}.")
            logger.info(f"URL: {result.get('url')}")
            return result.get("url") or True
        else:
            logger.error(f"Failed to publish: {response.status_code}")
            logger.error(response.text)
            return False
