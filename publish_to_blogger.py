
import os
import json
import subprocess
import requests

def get_access_token():
    try:
        output = subprocess.check_output(["gws", "auth", "export", "--unmasked"], stderr=subprocess.STDOUT).decode()
        start = output.find('{')
        end = output.rfind('}') + 1
        creds = json.loads(output[start:end])
        
        # If access_token is not in creds, we need to refresh it
        refresh_token = creds.get("refresh_token")
        client_id = creds.get("client_id")
        client_secret = creds.get("client_secret")
        
        if not refresh_token:
            print("Error: No refresh token found.")
            return None
            
        # Refresh the token
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
            print(response.text)
            return None
            
    except Exception as e:
        print(f"Error getting token: {e}")
        return None

import base64

def get_base64_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def publish_post(blog_id, title, content, image_path=None):
    token = get_access_token()
    if not token:
        return
    
    if image_path and os.path.exists(image_path):
        b64_data = get_base64_image(image_path)
        image_html = f'<br><img src="data:image/png;base64,{b64_data}" alt="AI Coding Agent Army" style="width:100%; max-width:800px; display:block; margin:auto;"><br>'
        content = content.replace("[IMAGE_PLACEHOLDER]", image_html)
    elif "[IMAGE_PLACEHOLDER]" in content:
        content = content.replace("[IMAGE_PLACEHOLDER]", "")
    
    url = f"https://www.googleapis.com/blogger/v3/blogs/{blog_id}/posts"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    data = {
        "title": title,
        "content": content
    }
    
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        print("Success! Post published using Base64.")
        print(response.json().get("url"))
    else:
        print(f"Failed to publish: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    blog_id = "334619364211713413"
    title = "[AI 에이전트 시대] 터미널 속에 구축한 나만의 코딩 에이전트 군단 (Base64 완전판)"
    content = """
    <h1>AI 에이전트와 함께하는 미래형 개발 환경</h1>
    <p>안녕하세요! 오늘은 제 터미널 환경에 <b>Hermes, Claude Code, Goose, Codex, Copilot CLI</b>까지 모두 설치한 기념비적인 날입니다.</p>
    <p>이 에이전트들은 이제 단순한 도구를 넘어, 제 의도를 파악하고 함께 코드를 고민하는 강력한 파트너들입니다.</p>
    [IMAGE_PLACEHOLDER]
    <p>특히 Google Workspace와의 연동을 통해, 제가 코딩에만 집중할 수 있도록 행정적인 작업까지 자동화할 수 있게 되었습니다.</p>
    <p>앞으로 이 군단과 함께 만들어갈 프로젝트들이 기대됩니다!</p>
    """
    image_path = "./ai_coding_agent_army.png"
    publish_post(blog_id, title, content, image_path)
