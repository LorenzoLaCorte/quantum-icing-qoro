#!/bin/sh
# Campaign of 2026-11-22 (00:15-00:50): 124 configurations, 6 processes in parallel, seed 11.
# Each line of campaign_jobs.txt is "<instance> <lambda> <minutes>". Run from the repo root.
# Every run warm-starts from the .sol already in $PORTFOLIO_SOL_DIR and only overwrites it if better.
set -e
. .venv/bin/activate
export PORTFOLIO_SOL_DIR="${PORTFOLIO_SOL_DIR:-solutions/portfolio}"
LOGS="${LOGS:-ai_context/portfolio_classical/logs/campaign}"
mkdir -p "$LOGS"
xargs -P 6 -L 1 sh -c 'python portfolio_search.py run --inst $0 --lam $1 --minutes $2 --seed 11 > '"$LOGS"'/c_$0_$1.log 2>&1' \
  < ai_context/portfolio_classical/scripts/campaign_jobs.txt
echo CAMPAIGN DONE
