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
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    def convert_markdown_to_html(self, md_content, image_path=None):
        html_content = markdown.markdown(md_content)
        
        if image_path and os.path.exists(image_path):
            b64_data = self.get_base64_image(image_path)
            if b64_data:
                style = f'width:{self.settings.get("image_width", "100%")}; max-width:{self.settings.get("max_image_width", "800px")}; display:block; margin:auto;'
                image_html = f'<br><img src="data:image/png;base64,{b64_data}" alt="Post Image" style="{style}"><br>'
                if "[IMAGE_PLACEHOLDER]" in html_content:
                    html_content = html_content.replace("[IMAGE_PLACEHOLDER]", image_html)
                else:
                    html_content += image_html
                    
        return html_content

    def publish_post(self, title, content, image_path=None, is_markdown=True, is_draft=False):
        token = self.get_access_token()
        if not token:
            print("Failed to obtain access token.")
            return False
        
        if is_markdown:
            final_content = self.convert_markdown_to_html(content, image_path)
        else:
            final_content = content

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
