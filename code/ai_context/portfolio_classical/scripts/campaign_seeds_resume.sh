#!/bin/sh
# Resume of campaign_seeds.sh, started at about 03:20 on 2026-11-22 because the user wanted the
# campaign to finish as early as possible.
# campaign_seeds.sh was stopped after pass-1 job 36; the six a200 lambda=1e-3 runs it had started
# (10 min each) were left to finish. campaign_seeds_resume.txt holds the 60 pass-1 jobs left,
# shortened: a200 5e-4 10->3 min, a200 1e-4 10->2 min, a400 lambda <= 5e-5 4->1 min,
# a200 lambda <= 5e-5 3->0.5 min (low lambda converges in seconds).
# Pass 2 (campaign_seeds_pass2.txt, warm-started second seed) was dropped entirely.
# Evidence for the cuts, from the 24 finished a400 pass-1 logs (12 min): gain in the last 6 min
# was 1-5.6% for lambda 1e-2, ~0.7% for 1e-3, ~0.3% for 5e-4, ~0.07% for 1e-4.
# Line format: <tag> <inst> <lam> <minutes> <method> <seed>. Longest jobs first.
# At most 6 solver processes at once (counting the runs left over from the first driver), and a
# job starts only with at least 1 GB of MemAvailable. The final verify runs one process per
# instance, up to 3 at once, each starting only with at least 1.4 GB of MemAvailable.
. .venv/bin/activate
export PORTFOLIO_SOL_DIR="${PORTFOLIO_SOL_DIR:-solutions/portfolio_seeds}"
S=ai_context/portfolio_classical/scripts
LOGS="${LOGS:-ai_context/portfolio_classical/logs/campaign_seeds}"
VT="${VERIFY_TMP:-/tmp/portfolio_seeds_verify}"
MAXJ=6
nrun() { pgrep -fc "^python portfolio_search.py run" || true; }
mem() { awk '/MemAvailable/{print $2}' /proc/meminfo; }

echo "resume start $(date +%T)"
while read tag inst lam min method seed; do
  while [ "$(nrun)" -ge $MAXJ ] || [ "$(mem)" -lt 1000000 ]; do sleep 5; done
  ( python portfolio_search.py run --inst $inst --lam $lam --minutes $min --method $method --seed $seed \
      > "$LOGS/${tag}_${inst}_${lam}.log" 2>&1 || echo "FAILED $tag $inst $lam" ) &
  echo "  $(date +%T) start $tag $inst $lam ${min}min"
  sleep 2
done < $S/campaign_seeds_resume.txt
while [ "$(nrun)" -gt 0 ]; do sleep 5; done
echo "runs done $(date +%T)"

# parallel verify: one folder of symlinks per instance
rm -rf "$VT"; mkdir -p "$VT"
for inst in $(ls "$PORTFOLIO_SOL_DIR" | grep '\.sol$' | sed 's/_b[0-9]*_l.*//' | sort -u); do
  mkdir "$VT/$inst"; ln -s "$PWD/$PORTFOLIO_SOL_DIR"/${inst}_b*.sol "$VT/$inst/"
done
ls "$VT" | sort -r | xargs -P 3 -I{} sh -c '
  while [ "$(awk "/MemAvailable/{print \$2}" /proc/meminfo)" -lt 1400000 ]; do sleep 5; done
  PORTFOLIO_SOL_DIR="$0/{}" python portfolio_search.py verify > "$0/{}.txt" 2>&1' "$VT"
cat "$VT"/*.txt > "$LOGS/verify_official_scorer.txt"
python portfolio_search.py status > "$LOGS/status.txt" 2>&1
echo "ALL DONE $(date +%T): $(grep -c '^OK' "$LOGS/verify_official_scorer.txt") OK, $(grep -vc '^OK' "$LOGS/verify_official_scorer.txt") not OK"
