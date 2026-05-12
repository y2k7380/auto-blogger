import os
import json
from datetime import datetime, timedelta

class AgentMonitor:
    def __init__(self):
        self.claude_history_path = os.path.expanduser("~/.claude/history.jsonl")
        self.hermes_log_path = os.path.expanduser("~/.hermes/logs/agent.log")

    def get_claude_activities(self, limit_hours=24):
        activities = []
        if not os.path.exists(self.claude_history_path):
            return activities

        now_ts = datetime.now().timestamp() * 1000
        limit_ts = now_ts - (limit_hours * 3600 * 1000)

        with open(self.claude_history_path, "r") as f:
            for line in f:
                try:
                    data = json.loads(line)
                    if data.get("timestamp", 0) > limit_ts:
                        activities.append({
                            "agent": "Claude",
                            "action": data.get("display", ""),
                            "timestamp": data.get("timestamp")
                        })
                except:
                    continue
        return activities

    def get_hermes_activities(self, limit_hours=24):
        # Hermes logs are a bit more complex, let's just grab recent INFO lines for now
        activities = []
        if not os.path.exists(self.hermes_log_path):
            return activities

        limit_time = datetime.now() - timedelta(hours=limit_hours)
        
        with open(self.hermes_log_path, "r") as f:
            for line in f:
                # Basic parsing: 2026-05-12 02:46:36,323 INFO ...
                try:
                    parts = line.split(" ", 2)
                    if len(parts) < 3: continue
                    log_time_str = f"{parts[0]} {parts[1].split(',')[0]}"
                    log_time = datetime.strptime(log_time_str, "%Y-%m-%d %H:%M:%S")
                    
                    if log_time > limit_time:
                        if "INFO" in line or "WARNING" in line:
                            activities.append({
                                "agent": "Hermes",
                                "action": parts[2].strip(),
                                "timestamp": log_time.timestamp() * 1000
                            })
                except:
                    continue
        return activities

    def generate_daily_summary(self):
        claude = self.get_claude_activities()
        hermes = self.get_hermes_activities()
        
        all_activities = claude + hermes
        all_activities.sort(key=lambda x: x["timestamp"], reverse=True)
        
        if not all_activities:
            return "No recent agent activity found."

        summary = f"# Daily Agent Activity Report - {datetime.now().strftime('%Y-%m-%d')}\n\n"
        summary += "Today, the AI Agent Army was busy with the following tasks:\n\n"
        
        # Group by agent
        agents = {}
        for act in all_activities:
            name = act["agent"]
            if name not in agents: agents[name] = []
            agents[name].append(act["action"])

        for name, actions in agents.items():
            summary += f"## {name} Activity\n"
            # Deduplicate and limit
            unique_actions = list(dict.fromkeys(actions))[:10]
            for action in unique_actions:
                if action:
                    summary += f"- {action}\n"
            summary += "\n"
            
        return summary
