"""Log local UTF-8; funciona sem terminal no executável e nunca derruba o pet."""
import datetime
import sys
import traceback
from pathlib import Path
from .store import write_text
MAX_BYTES=1_000_000
_file=None

def setup(path):
    global _file
    _file=Path(path)
    # Rotaciona antes do loop gráfico, preservando o log anterior.
    try:
        if _file.exists() and _file.stat().st_size>MAX_BYTES:
            import time
            _file.rename(_file.with_name(_file.name+'.'+str(time.time_ns())+'.old'))
    except OSError:pass

def desligar_arquivo():
    global _file
    _file=None

def log(*parts):
    text=' '.join(str(p) for p in parts)
    stream=sys.stderr
    if stream is not None:
        try:stream.write(text+'\n')
        except UnicodeEncodeError:
            try:stream.write(text.encode('ascii','replace').decode('ascii')+'\n')
            except (OSError,ValueError,AttributeError):pass
        except (OSError,ValueError,AttributeError):pass
    _gravar(text)

def _gravar(text):
    if _file is None:return
    try:write_text(_file,f'{datetime.datetime.now().isoformat(timespec="seconds")} {text}\n',append=True)
    except (OSError,ValueError):pass

def capturar_erros():
    anterior=sys.excepthook
    if getattr(anterior,'_do_pestinha',False):return
    def gancho(tipo,valor,rastro):
        _gravar('[erro] '+''.join(traceback.format_exception(tipo,valor,rastro)).rstrip())
        try:anterior(tipo,valor,rastro)
        except (OSError,ValueError,AttributeError):pass
    gancho._do_pestinha=True;sys.excepthook=gancho
