#!/bin/bash

# Cron job script for Gmail News Analyzer
# Add this to crontab: */15 * * * * /root/marketMan/run_analyzer.sh

cd /root/marketMan

# Activate virtual environment if you're using one
# source venv/bin/activate

# Run the analyzer
python news_gpt_analyzer.py >> analyzer.log 2>&1

# Optional: Rotate logs if they get too large
if [ -f analyzer.log ] && [ $(stat -c%s analyzer.log) -gt 10485760 ]; then
    mv analyzer.log analyzer.log.old
fi
