# SPDX-License-Identifier: GPL-3.0-only
"""O protocolo deve continuar UTF-8 mesmo com o padrão Windows cp1252."""
import json
import os
import queue
import subprocess
import sys
import threading
import time
from pathlib import Path


def test_carinho_com_coracao_nao_encerra_worker_cp1252(tmp_path):
    root = Path(__file__).resolve().parents[2]
    process = subprocess.Popen(
        [sys.executable, str(root/'brain/worker.py'), '--data-dir', str(tmp_path/'memória'),
         '--content-dir', str(root/'assets/bolha/content')],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        env=dict(os.environ, PYTHONIOENCODING='cp1252', PYTHONUTF8='0', OPENBLAS_NUM_THREADS='1'),
    )
    output = queue.Queue()
    def read():
        for line in process.stdout: output.put(line)
        output.put(None)
    threading.Thread(target=read, daemon=True).start()
    try:
        process.stdin.write(b'{"type":"caress"}\n')
        process.stdin.flush()
        deadline = time.monotonic()+15
        while time.monotonic() < deadline:
            line = output.get(timeout=15)
            assert line is not None, process.stderr.read().decode('utf-8', errors='replace')
            state = json.loads(line.decode('utf-8'))
            if state['speech']:
                assert state['speech'] == 'Tá, esse carinho eu aceito. ♡'
                assert state['ready']
                break
        else: raise AssertionError('O carinho não apareceu no estado do cérebro.')
        process.stdin.write(b'{"type":"quit"}\n')
        process.stdin.flush()
        assert process.wait(timeout=10) == 0
        assert 'UnicodeEncodeError' not in process.stderr.read().decode('utf-8')
        assert (tmp_path/'memória/bolha/nervous.json').is_file()
    finally:
        if process.poll() is None: process.kill()
        process.wait(timeout=10)
