# SPDX-License-Identifier: GPL-3.0-or-later
# Bolha is based on Pestinha by @mille-okws and contributors; see NOTICE.md.
"""Compila só o assistente NSIS para testes rápidos. Payload falso nunca é executado/publicado."""
from pathlib import Path
import os
import struct
import subprocess
import tomllib
from fetch_nsis import fetch

ROOT=Path(__file__).resolve().parents[1]


def build():
    if os.name!='nt':raise OSError('Execute a fixture somente no Windows.')
    version=tomllib.loads((ROOT/'pyproject.toml').read_text())['project']['version']
    work=ROOT/'validation/installer-ui-fixture'
    bundle=work/'dummy';bundle.mkdir(parents=True,exist_ok=True)
    (bundle/'Bolha.exe').write_bytes(b'MZ\0NSIS UI fixture: not an application')
    w=32
    pixels=b'\x94\x66\x30\xff'*(w*w)
    mask=b'\0'*(w*w//8)
    dib=struct.pack('<IIIHHIIIIII',40,w,w*2,1,32,0,len(pixels)+len(mask),0,0,0,0)+pixels+mask
    icon=work/'fixture.ico'
    icon.write_bytes(struct.pack('<HHH',0,1,1)+struct.pack('<BBBBHHII',w,w,0,0,1,32,len(dib),22)+dib)
    filelist=work/'files.nsh';filelist.write_text('Delete "$INSTDIR\\Bolha.exe"\n')
    subprocess.run([str(fetch(ROOT/'build/tools')),'/V2','/WX','/INPUTCHARSET','UTF8',
                    '/DDIRECTORY_TRACE','/DVERSION='+version,'/DBUNDLE='+str(bundle),'/DOUTPUT='+str(work),
                    '/DICON='+str(icon),'/DFILELIST='+str(filelist),str(ROOT/'packaging/bolha.nsi')],check=True,cwd=ROOT)


if __name__=='__main__':build()
