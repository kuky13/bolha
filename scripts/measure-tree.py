# SPDX-License-Identifier: GPL-3.0-or-later
# Bolha is based on Pestinha by @mille-okws and contributors; see NOTICE.md.
"""Amostrador de teste: soma RSS e CPU da árvore inteira, sem telemetria."""
import json
import sys
import time
import psutil

root = psutil.Process(int(sys.argv[1]))
seconds = max(5, min(3600, int(sys.argv[2])))
rows, seen, previous = [], {}, {}
started = time.monotonic()
while time.monotonic()-started < seconds:
    rss = brain_rss = cpu = brain_cpu = 0.
    for process in [root]+root.children(recursive=True):
        try:
            resident = process.memory_info().rss
            rss += resident
            is_brain = 'worker.py' in ' '.join(process.cmdline()) or process.name().lower() == 'bolhabrain.exe'
            if is_brain: brain_rss += resident
            current = sum(process.cpu_times()[:2])
            if process.pid in previous:
                delta = max(0, current-previous[process.pid])
                cpu += delta
                if is_brain: brain_cpu += delta
            previous[process.pid] = current
            seen[process.pid] = process.name()
        except psutil.Error: pass
    rows.append((rss, brain_rss, cpu, brain_cpu))
    time.sleep(1)
elapsed = time.monotonic()-started
print(json.dumps(dict(platform=sys.platform, seconds=round(elapsed,2), samples=len(rows),
                     peakTreeRssMiB=round(max(r[0] for r in rows)/1048576,2),
                     meanTreeRssMiB=round(sum(r[0] for r in rows)/len(rows)/1048576,2),
                     peakBrainRssMiB=round(max(r[1] for r in rows)/1048576,2),
                     oneCoreCpuPercent=round(sum(r[2] for r in rows)/max(1,elapsed-1)*100,2),
                     brainOneCoreCpuPercent=round(sum(r[3] for r in rows)/max(1,elapsed-1)*100,2),
                     processes=seen)))
