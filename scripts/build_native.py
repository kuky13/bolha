# SPDX-License-Identifier: GPL-3.0-only
"""Empacotamento Windows x64; Python/Qt, sem Node, npm ou credenciais."""
import argparse
from importlib.metadata import distribution
import json
import hashlib
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from bolha import VERSION
from scripts.release_metadata import generate


def collect_licenses(target):
    target.mkdir(parents=True,exist_ok=True)
    for name in ('LICENSE','NOTICE.md'):
        shutil.copy2(ROOT/name,target/name)
    shutil.copytree(ROOT/'licenses',target,dirs_exist_ok=True)
    for name in ('numpy','psutil','PyInstaller','PySide6-Essentials','shiboken6','pywin32'):
        try: package=distribution(name)
        except Exception:
            if name=='pywin32' and os.name!='nt':continue
            raise
        for item in package.files or ():
            if any(word in str(item).lower() for word in ('license','copying','notice')):
                source=Path(package.locate_file(item))
                if source.is_file():
                    output=target/'third-party'/name/str(item)
                    output.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,output)
    python_license=Path(sys.base_prefix)/'LICENSE.txt'
    if not python_license.exists():python_license=Path(sys.base_prefix)/'lib/python3.11/LICENSE.txt'
    if not python_license.exists():raise FileNotFoundError('Licença do Python não localizada.')
    shutil.copy2(python_license,target/'PYTHON-LICENSE.txt')


def icon(output):
    from PySide6.QtGui import QGuiApplication, QImage, QPainter
    from PySide6.QtCore import Qt
    from bolha.character import draw_character
    app=QGuiApplication.instance() or QGuiApplication([])
    picture=QImage(256,256,QImage.Format.Format_ARGB32);picture.fill(Qt.GlobalColor.transparent)
    painter=QPainter(picture);painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    draw_character(painter,128,128,scale=2.05,emotion='observando');painter.end()
    output.mkdir(parents=True,exist_ok=True)
    for name in ('icon.png','tray.png','icon.ico'):
        if not picture.save(str(output/name)):raise OSError('Falha ao gravar '+name)


def prune_optional_qt(bundle):
    """O hook QtGui coleta TUIO por padrão; o pet não usa entrada multitoque por UDP."""
    import pefile
    plugin=bundle/'_internal/PySide6/plugins/generic/qtuiotouchplugin.dll'
    if plugin.exists():plugin.unlink()
    network=bundle/'_internal/PySide6/Qt6Network.dll'
    if not network.exists():return
    importers=[]
    for path in bundle.rglob('*'):
        if path.suffix.lower() not in ('.dll','.pyd','.exe') or path==network:continue
        image=pefile.PE(str(path),fast_load=True)
        try:
            image.parse_data_directories(directories=[pefile.DIRECTORY_ENTRY['IMAGE_DIRECTORY_ENTRY_IMPORT'],
                                                     pefile.DIRECTORY_ENTRY['IMAGE_DIRECTORY_ENTRY_DELAY_IMPORT']])
            entries=getattr(image,'DIRECTORY_ENTRY_IMPORT',[])+getattr(image,'DIRECTORY_ENTRY_DELAY_IMPORT',[])
            if any(item.dll.lower()==b'qt6network.dll' for item in entries):importers.append(str(path.relative_to(bundle)))
        finally:image.close()
    if importers:raise ValueError('QtNetwork ainda é necessária por: '+', '.join(importers))
    network.unlink()


def build(version, output, makensis=None, reuse_bundle=None):
    if os.name!='nt' or sys.maxsize<=2**32:raise OSError('Compile no Windows x64.')
    if sys.version_info[:2]!=(3,11):raise OSError('Use Python3.11.')
    if not re.fullmatch(r'\d+\.\d+\.\d+',version):raise ValueError('Versão inválida.')
    output=Path(output).resolve();output.mkdir(parents=True,exist_ok=True)
    work=ROOT/'build'/version;work.mkdir(parents=True,exist_ok=True)
    resource=work/'resources';resource.mkdir(exist_ok=True)
    (resource/'bolha-version.json').write_text(json.dumps({'version':version}),encoding='utf-8')
    collect_licenses(resource/'licenses')
    shutil.copy2(ROOT/'packaging/THIRD-PARTY-NOTICES.txt',resource/'THIRD-PARTY-NOTICES.txt')
    # Geometria Qt aprovada sem boca; o ícone antigo nunca entra no pacote.
    icon(resource/'icons')
    args=[sys.executable,'-m','PyInstaller','--noconfirm','--clean','--windowed','--onedir','--name','Bolha',
          '--distpath',str(work/'dist'),'--workpath',str(work/'pyinstaller'),'--specpath',str(work),
          '--paths',str(ROOT/'brain'),'--icon',str(resource/'icons/icon.ico')]
    for source,target in ((ROOT/'assets/bolha/content','assets/bolha/content'),
                          (resource/'icons','assets/bolha'),(resource/'licenses','licenses'),
                          (resource/'bolha-version.json','.'),(resource/'THIRD-PARTY-NOTICES.txt','.')):
        args+=['--add-data',str(source)+os.pathsep+target]
    for module in ('PySide6.QtQml','PySide6.QtQuick','PySide6.QtWebEngineCore','PySide6.QtWebEngineWidgets',
                   'PySide6.QtNetwork','tkinter','matplotlib','scipy','pytest'):
        args+=['--exclude-module',module]
    args += [str(ROOT/'launcher.py')]
    bundle=work/'dist/Bolha'
    if reuse_bundle:
        if Path(reuse_bundle).resolve()!=bundle.resolve():
            shutil.copytree(Path(reuse_bundle).resolve(),bundle,dirs_exist_ok=True)
        shutil.copy2(resource/'bolha-version.json',bundle/'_internal/bolha-version.json')
    else:
        subprocess.run(args,cwd=ROOT,check=True)
    prune_optional_qt(bundle)
    subprocess.run([sys.executable,str(ROOT/'scripts/audit_native.py'),str(bundle)],check=True)
    manifest={}
    for path in bundle.rglob('*'):
        if path.is_file() and path.name!='installed-files.json':
            with path.open('rb') as source: manifest[path.relative_to(bundle).as_posix()]=hashlib.file_digest(source,'sha256').hexdigest()
    (bundle/'installed-files.json').write_text(json.dumps(dict(appId='solutions.kuky.bolha',version=version,files=manifest)),encoding='utf-8')
    files=sorted(path.relative_to(bundle) for path in bundle.rglob('*') if path.is_file())
    directories=sorted((path.relative_to(bundle) for path in bundle.rglob('*') if path.is_dir()), key=lambda p:len(p.parts),reverse=True)
    filelist=work/'uninstall-files.nsh'
    # Nenhum nome vem da rede: os caminhos são produzidos pelo próprio PyInstaller.
    def nsis_path(path):
        return str(path).replace('/',chr(92)).replace('$','$$')
    commands=[f'Delete "$INSTDIR{chr(92)}{nsis_path(path)}"' for path in files]
    commands+=[f'RMDir "$INSTDIR{chr(92)}{nsis_path(path)}"' for path in directories]
    filelist.write_text('\n'.join(commands)+'\n',encoding='utf-8-sig')
    compiler=makensis or shutil.which('makensis')
    if not compiler:
        from scripts.fetch_nsis import fetch
        compiler=str(fetch(ROOT/'build/tools'))
    # /D before script: paths stay separate arguments, no shell interpolation.
    subprocess.run([compiler,'/V2','/WX','/INPUTCHARSET','UTF8','/DVERSION='+version,'/DBUNDLE='+str(bundle),
                    '/DOUTPUT='+str(output),'/DICON='+str(resource/'icons/icon.ico'),'/DFILELIST='+str(filelist),
                    str(ROOT/'packaging/bolha.nsi')],check=True,cwd=ROOT)
    shutil.copy2(ROOT/'packaging/THIRD-PARTY-NOTICES.txt',output/'THIRD-PARTY-NOTICES.txt')
    generate(output,version)
    print(bundle)
    return bundle


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--version',default=VERSION)
    parser.add_argument('--output',default='release');parser.add_argument('--makensis');parser.add_argument('--reuse-bundle')
    args=parser.parse_args();build(args.version,args.output,args.makensis,args.reuse_bundle)
