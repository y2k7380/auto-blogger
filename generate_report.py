import os
from datetime import datetime
from core.monitor import AgentMonitor
from core.blogger_api import BloggerAPI

def main():
    monitor = AgentMonitor()
    summary = monitor.generate_daily_summary()
    
    date_str = datetime.now().strftime("%Y-%m-%d")
    filename = f"posts/daily_report_{date_str}.md"
    
    with open(filename, "w") as f:
        f.write(summary)
    
    print(f"Report generated: {filename}")
    
    # Optionally publish
    api = BloggerAPI()
    title = f"Daily AI Agent Activity Report ({date_str})"
    api.publish_post(
        title=title,
        content=summary,
        is_markdown=True,
        is_draft=True  # Save as draft by default
    )

if __name__ == "__main__":
    main()
