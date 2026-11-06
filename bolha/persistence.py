# SPDX-License-Identifier: GPL-3.0-or-later
# Bolha is based on Pestinha by @mille-okws and contributors; see NOTICE.md.
"""Grava snapshots imutáveis fora do desenho e conserva falhas para repetição."""
from collections import OrderedDict
from pathlib import Path
import queue
import threading
import time
from pestinha.store import atomic_write_text

class PersistenceWriter:
    def __init__(self):
        self.pending=OrderedDict();self.failed={};self.failures={}
        self.condition=threading.Condition();self.errors=queue.SimpleQueue()
        self.active=False;self.closed=False
        self.thread=threading.Thread(target=self._run,name='bolha-save',daemon=True);self.thread.start()
    @property
    def failure(self):return next(iter(self.failures.values()),None)
    def submit(self,path,text,append=False):
        assert isinstance(text,str),'Somente snapshots serializados podem cruzar a thread.'
        with self.condition:
            if self.closed:raise OSError('Gravador já encerrado.')
            key=(Path(path),bool(append))
            # Append falho permanece até o próximo envio/retry; snapshots completos são substituíveis.
            old=self.failed.pop(key,'')
            previous=self.pending.pop(key,'')
            self.pending[key]=(old+previous+text) if append else text
            self.condition.notify()
    def retry(self):
        with self.condition:
            for key,text in list(self.failed.items()):
                previous=self.pending.pop(key,'')
                self.pending[key]=text+previous if key[1] else (previous or text)
            self.failed.clear();self.condition.notify()
    def _run(self):
        while True:
            with self.condition:
                while not self.pending and not self.closed:self.condition.wait()
                if not self.pending and self.closed:return
                key,text=self.pending.popitem(last=False)
                previous=self.failed.pop(key,'')
                if key[1]:text=previous+text
                self.active=True
            path,append=key
            try:atomic_write_text(path,text,append)
            except OSError as error:
                with self.condition:
                    self.failed[key]=self.failed.get(key,'')+text if append else text
                    self.failures[path]=error
                self.errors.put((str(path),str(error)))
            else:
                with self.condition:self.failures.pop(path,None)
            finally:
                with self.condition:self.active=False;self.condition.notify_all()
    def flush(self,timeout=10):
        deadline=time.monotonic()+timeout
        with self.condition:
            while self.pending or self.active:
                left=deadline-time.monotonic()
                if left<=0:return False
                self.condition.wait(min(.1,left))
            return not self.failures
    def close(self):
        good=self.flush()
        with self.condition:self.closed=True;self.condition.notify()
        self.thread.join(timeout=2);return good
