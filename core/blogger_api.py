import os
import json
import subprocess
import requests
import base64
import markdown

class BloggerAPI:
    def __init__(self, settings_path="config/settings.json"):
        with open(settings_path, "r") as f:
            self.settings = json.load(f)
        self.blog_id = self.settings.get("blog_id")

    def get_access_token(self):
        try:
            output = subprocess.check_output(["gws", "auth", "export", "--unmasked"], stderr=subprocess.STDOUT).decode()
            start = output.find('{')
            end = output.rfind('}') + 1
            creds = json.loads(output[start:end])
            
            refresh_token = creds.get("refresh_token")
            client_id = creds.get("client_id")
            client_secret = creds.get("client_secret")
            
            if not refresh_token:
                print("Error: No refresh token found.")
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
                print(f"Error refreshing token: {response.status_code}")
                return None
        except Exception as e:
            print(f"Error getting token: {e}")
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
            print(f"⚠️ 이미지 최적화 중 오류 발생 (원본 사용 시도): {e}")
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')

    def convert_markdown_to_html(self, md_content, image_path=None):
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
                    
        # SEO: Add Call to Action
        html_content += '<hr><p><i>이 글이 도움이 되셨다면 <b>공감</b>과 <b>댓글</b> 부탁드립니다! 여러분의 에이전트 구축 경험도 공유해 주세요.</i></p>'
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
                html += '<h3 style="margin-top:0;">📂 함께 읽으면 좋은 글</h3><ul>'
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
            print("Failed to obtain access token.")
            return False
        
        if is_markdown:
            final_content = self.convert_markdown_to_html(content, image_path)
        else:
            final_content = content

        # SEO: Add Related Posts
        related_html = self.get_related_posts_html()
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
            print(f"Success! Post {'drafted' if is_draft else 'published'}.")
            print(f"URL: {result.get('url')}")
            return True
        else:
            print(f"Failed to publish: {response.status_code}")
            print(response.text)
            return False
