#!/bin/bash
# 2026 Autonomous Masterpiece Blogger - Daily Scheduler
PROJECT_DIR="/home/ubuntu/auto-blogger"
PYTHON_PATH="/home/ubuntu/.pyenv/shims/python3"
LOG_FILE="$PROJECT_DIR/auto_blog.log"

cd $PROJECT_DIR

echo "--- Daily Auto-Publish Started: $(date) ---" >> $LOG_FILE
$PYTHON_PATH blogger-cli.py auto >> $LOG_FILE 2>&1
echo "--- Daily Auto-Publish Finished: $(date) ---" >> $LOG_FILE
echo "" >> $LOG_FILE
