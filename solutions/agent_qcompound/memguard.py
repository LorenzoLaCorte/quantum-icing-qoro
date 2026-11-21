"""Import and call start() at the top of any long run: kills this process if RAM runs low."""
import os, threading, time

def mem_available_mb():
    with open('/proc/meminfo') as f:
        for line in f:
            if line.startswith('MemAvailable:'):
                return int(line.split()[1]) // 1024
    return 10**9

def start(min_mb=1200, period=2.0):
    def loop():
        while True:
            if mem_available_mb() < min_mb:
                print(f'[memguard] MemAvailable < {min_mb} MB: exiting', flush=True)
                os._exit(3)
            time.sleep(period)
    threading.Thread(target=loop, daemon=True).start()
