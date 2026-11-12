# SPDX-License-Identifier: GPL-3.0-or-later
# Bolha is based on Pestinha by @mille-okws and contributors; see NOTICE.md.
"""Exercita o assistente NSIS real em pastas /TEST, sem tocar na instalação pessoal."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time


def validate(installer, output):
    import psutil
    import win32con as wc
    import win32gui as wg
    import win32process
    import pywintypes
    from test_windows_native import test_environment, registry_fingerprint, installer_version
    root=Path(tempfile.mkdtemp(prefix='bolha-wizard-'))
    parent=root/'Meus aplicativos ç'
    parent.mkdir()
    sentinel=parent/'documento.txt';sentinel.write_bytes(b'nao alterar')
    original_registry=registry_fingerprint()
    records=[]

    def wizard(selected, expected, allow_alternative):
        env=test_environment(root/'data',selected,root/'runtime.json')
        process=subprocess.Popen([str(installer),'/TEST','/D='+str(selected)],env=env)
        transaction=expected.with_name(expected.name+'.transaction.ini')
        previous=transaction.read_bytes() if transaction.exists() else None
        owned={process.pid}
        set_directory=False
        confirmed=False
        finished=False
        deadline=time.monotonic()+75
        last_page=[]
        def children(hwnd):
            found=[]
            wg.EnumChildWindows(hwnd,lambda h,_:found.append(h),None)
            return [h for h in found if wg.IsWindowVisible(h)]
        def click(hwnd, identity, finish=False):
            button=control(hwnd,identity)
            if button and wg.IsWindowEnabled(button):
                if finish:
                    wg.PostMessage(hwnd,wc.WM_COMMAND,identity,button)
                else:
                    wg.PostMessage(button,wc.BM_CLICK,0,0)
                return True
            return False
        def control(hwnd, identity):
            try:return wg.GetDlgItem(hwnd,identity)
            except pywintypes.error:return None
        try:
            while time.monotonic()<deadline:
                try:owned.update(p.pid for p in psutil.Process(process.pid).children(recursive=True))
                except psutil.NoSuchProcess:pass
                windows=[]
                def collect(hwnd,_):
                    if (wg.IsWindowVisible(hwnd) and wg.GetClassName(hwnd)=='#32770'
                            and win32process.GetWindowThreadProcessId(hwnd)[1] in owned):windows.append(hwnd)
                wg.EnumWindows(collect,None)
                for hwnd in windows:
                    controls=children(hwnd)
                    last_page=[(wg.GetDlgCtrlID(h),wg.GetClassName(h),wg.GetWindowText(h)) for h in controls]
                    if any(identity==1037 and ('abortada' in caption.casefold() or 'aborted' in caption.casefold())
                           for identity,_,caption in last_page):
                        raise AssertionError(f'Assistente abortou: {last_page!r}')
                    # O assistente NSIS também pode ter uma janela proprietária oculta.
                    if not control(hwnd,3):
                        if control(hwnd,wc.IDYES) and allow_alternative:
                            confirmed=True;click(hwnd,wc.IDYES)
                        else:
                            text=' | '.join(wg.GetWindowText(h) for h in controls if wg.GetWindowText(h))
                            raise AssertionError('Diálogo inesperado: '+text)
                        continue
                    edit=next((h for h in controls if wg.GetClassName(h)=='Edit' and wg.GetDlgCtrlID(h)==1019),None)
                    if edit and not set_directory:
                        wg.SendMessage(edit,wc.WM_SETTEXT,0,str(selected))
                        time.sleep(.3)
                        button=control(hwnd,1)
                        assert wg.IsWindowEnabled(button), 'Instalar desabilitado ao selecionar pasta válida'
                        set_directory=True
                        click(hwnd,1)
                    elif not set_directory:
                        click(hwnd,1)  # boas-vindas e licença
                    elif not finished and (expected/'Bolha.exe').is_file():
                        run_checkbox=next((h for h in controls if wg.GetDlgCtrlID(h)==1203
                                           and wg.GetClassName(h)=='Button'),None)
                        if run_checkbox:
                            wg.SendMessage(run_checkbox,wc.BM_SETCHECK,wc.BST_UNCHECKED,0)
                            finished=click(hwnd,1,finish=True)
                if process.poll() is not None:break
                time.sleep(.15)
            else:raise TimeoutError(f'Assistente NSIS não concluiu: destino={expected.is_dir()}, '
                                    f'confirmação={confirmed}, controles={last_page!r}')
            assert process.returncode==0, f'Código do instalador: {process.returncode}; controles={last_page!r}'
            assert set_directory
            assert confirmed==allow_alternative
            assert (expected/'bolha-native-installation.flag').is_file()
            assert transaction.read_bytes()!=previous
            assert 'state=committed' in transaction.read_text(encoding='utf-16')
            assert sentinel.read_bytes()==b'nao alterar'
            assert registry_fingerprint()==original_registry
            records.append(dict(selected=str(selected),installed=str(expected),alternative=confirmed,passed=True))
        finally:
            if process.poll() is None:
                process.terminate();process.wait(timeout=10)
    try:
        new=root/'Nova instalação'/'Bolha'
        wizard(new,new,False)
        wizard(parent,parent/'Bolha',True)
        wizard(parent/'Bolha',parent/'Bolha',False)
        unknown=root/'Instalação antiga'/'Bolha'
        unknown.mkdir(parents=True)
        saved=unknown/'arquivo-importante.txt';saved.write_bytes(b'preservar pasta antiga')
        wizard(unknown,unknown.parent/('Bolha-'+installer_version(installer)),True)
        assert saved.read_bytes()==b'preservar pasta antiga'
        report=dict(passed=True,scenarios=records)
    except Exception as error:
        report=dict(passed=False,scenarios=records,error=str(error),retained=str(root))
        raise
    finally:
        output.parent.mkdir(parents=True,exist_ok=True)
        output.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--installer',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if os.name!='nt':parser.error('Somente Windows executa o assistente real.')
    validate(args.installer.resolve(),args.output.resolve())
