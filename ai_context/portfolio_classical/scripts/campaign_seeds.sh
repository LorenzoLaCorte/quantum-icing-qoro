#!/bin/sh
# a200/a400 seed instances (s00-s02), 2026-11-22. Run from the repo root.
# 1) build the integer caches, 3 in parallel
# 2) pass 1: all 8 lambdas, longest jobs first (a400 high lambda 12 min ... a200 low lambda 3 min)
# 3) pass 2: lambda >= 5e-4 again, warm start, another seed
# 4) official-scorer verify + status
# Max 6 runs at once; a run starts only if MemAvailable >= 1 GB (7.4 GB machine).
set -e
. .venv/bin/activate
export PORTFOLIO_SOL_DIR="${PORTFOLIO_SOL_DIR:-solutions/portfolio_seeds}"
S=ai_context/portfolio_classical/scripts
LOGS="${LOGS:-ai_context/portfolio_classical/logs/campaign_seeds}"
mkdir -p "$LOGS" "$PORTFOLIO_SOL_DIR"
export LOGS
echo "build start $(date +%T)"
cut -d' ' -f1 $S/campaign_seeds_pass1.txt | sort -u | xargs -P 3 -n 1 python portfolio_search.py build --inst > "$LOGS/build.log" 2>&1
echo "build done $(date +%T)"
run_pass() {  # $1 = job file, $2 = tag
  xargs -P 6 -L 1 sh -c '
    while [ "$(awk "/MemAvailable/{print \$2}" /proc/meminfo)" -lt 1000000 ]; do sleep 10; done
    python portfolio_search.py run --inst $0 --lam $1 --minutes $2 --method $3 --seed $4 \
      > "$LOGS/'"$2"'_$0_$1.log" 2>&1 || echo "FAILED $0 $1"
  ' < "$1"
}
echo "pass1 start $(date +%T)"; run_pass $S/campaign_seeds_pass1.txt p1; echo "pass1 done $(date +%T)"
echo "pass2 start $(date +%T)"; run_pass $S/campaign_seeds_pass2.txt p2; echo "pass2 done $(date +%T)"
python portfolio_search.py verify > "$LOGS/verify_official_scorer.txt" 2>&1
python portfolio_search.py status > "$LOGS/status.txt" 2>&1
echo "ALL DONE $(date +%T): $(grep -c '^OK' "$LOGS/verify_official_scorer.txt") OK, $(grep -vc '^OK' "$LOGS/verify_official_scorer.txt") not OK"
