# SPDX-License-Identifier: GPL-3.0-only
"""Processo local: JSON por stdin/stdout, sem portas de rede."""
import argparse
import json
import math
import queue
import sys
import threading
import time
import traceback
from pathlib import Path
from game import Game

ALLOWED = {'panic','hide','monitor','panel','hover','music','cursor','drag-start','drag','drag-end','poke','caress','spin','sleep','work','notebook','corner','ball','mischief','dismiss','quiet','reset-memory'}

def finite(value, depth=0):
    if depth > 12: return False
    if isinstance(value,float): return math.isfinite(value)
    if isinstance(value,dict): return len(value) <= 200 and all(finite(v,depth+1) for v in value.values())
    if isinstance(value,list): return len(value) <= 200 and all(finite(v,depth+1) for v in value)
    return isinstance(value,(str,int,bool,type(None)))

def main():
    # O Python empacotado pode ignorar PYTHONUTF8 e herdar cp1252 do Windows.
    for stream in (sys.stdin, sys.stdout, sys.stderr):
        stream.reconfigure(encoding='utf-8', errors='backslashreplace' if stream is sys.stderr else 'strict')
    parser = argparse.ArgumentParser()
    parser.add_argument('--data-dir',required=True)
    parser.add_argument('--content-dir',required=True)
    args = parser.parse_args()
    messages = queue.Queue(256)
    def read():
        try:
            for line in sys.stdin:
                if len(line) > 65536: raise ValueError('Mensagem muito grande')
                message = json.loads(line)
                if not isinstance(message,dict) or not finite(message): raise ValueError('Mensagem inválida')
                messages.put(message)
        except Exception as error:
            print(str(error),file=sys.stderr)
        finally: messages.put({'type':'quit'})
    threading.Thread(target=read,daemon=True).start()
    if sys.platform == 'win32':
        import ctypes
        try: ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
        except (AttributeError,OSError): ctypes.windll.user32.SetProcessDPIAware()
    game = Game(Path(args.data_dir),Path(args.content_dir))
    previous = last_output = time.monotonic()
    while True:
        start = time.monotonic()
        for _ in range(256):
            try: message = messages.get_nowait()
            except queue.Empty: break
            kind = message.get('type')
            if kind == 'quit': game.save(); return
            try:
                if kind == 'desktop': game.desktop(message['value'])
                elif kind == 'preferences': game.configure(message['value'])
                elif kind in ALLOWED: game.interact(message)
            except (KeyError,ValueError,TypeError,OverflowError) as error:
                print(f'Evento rejeitado: {error}',file=sys.stderr)
        now = time.monotonic()
        game.tick(now - previous,now); previous = now
        paused = game.panicked or game.hidden or not game.available_areas()
        if now - last_output >= (1. if paused else 1/30):
            print(json.dumps(game.snapshot(),ensure_ascii=False,allow_nan=False),flush=True)
            last_output = now
        time.sleep(max(0.,(.1 if paused else 1/60) - (time.monotonic()-start)))

if __name__ == '__main__':
    try: main()
    except BrokenPipeError: pass
    except Exception: traceback.print_exc(file=sys.stderr); sys.exit(1)
