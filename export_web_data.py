import json
from core.monitor import AgentMonitor
from core.blogger_api import BloggerAPI
import requests

def export_data():
    monitor = AgentMonitor()
    claude = monitor.get_claude_activities()
    hermes = monitor.get_hermes_activities()
    
    api = BloggerAPI()
    token = api.get_access_token()
    
    recent_posts = []
    if token:
        url = f"https://www.googleapis.com/blogger/v3/blogs/{api.blog_id}/posts"
        headers = {"Authorization": f"Bearer {token}"}
        resp = requests.get(url, headers=headers)
        if resp.status_code == 200:
            recent_posts = resp.json().get("items", [])[:5]

    data = {
        "activities": {
            "Claude": claude[:10],
            "Hermes": hermes[:10]
        },
        "posts": recent_posts,
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    os.makedirs("web", exist_ok=True)
    with open("web/data.json", "w") as f:
        json.dump(data, f, indent=4)
    print("Web data exported to web/data.json")

if __name__ == "__main__":
    from datetime import datetime
    import os
    export_data()
