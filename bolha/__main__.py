# SPDX-License-Identifier: GPL-3.0-or-later
# Bolha is based on Pestinha by @mille-okws and contributors; see NOTICE.md.
"""Entrada única da Bolha nativa; não cria servidor nem processo do cérebro."""
import os
from pathlib import Path
import sys

# BLAS pequeno: evitar dezenas de threads para uma rede de470neurônios.
for key in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS'):os.environ[key]='1'
root=Path(getattr(sys,'_MEIPASS',Path(__file__).resolve().parents[1]))
sys.path.insert(0,str(root/'brain'))

def main():
    # Fixture exclusiva do teste de recuperação: nunca ativa em execução normal.
    from . import VERSION
    if os.getenv('BOLHA_TEST')=='1' and os.getenv('BOLHA_TEST_FAIL_START')==VERSION:return 2
    from PySide6.QtGui import QGuiApplication
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QApplication,QMessageBox
    QGuiApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    from .platform import set_app_id
    app_id_warning=set_app_id()
    app=QApplication(sys.argv);app.setApplicationName('Bolha');app.setOrganizationName('solutions.kuky');app.setQuitOnLastWindowClosed(False)
    from .app import NativeApp,palette,icon
    palette(app);app.setWindowIcon(icon())
    try:controller=NativeApp(app)
    except Exception as error:
        # Janela local: builds windowed não têm stderr nem console.
        try:
            from .app import data_directory
            data=data_directory();data.mkdir(parents=True,exist_ok=True)
            import traceback
            (data/'startup-error.log').write_text(traceback.format_exc(),encoding='utf-8')
        except OSError:pass
        QMessageBox.critical(None,'Bolha não iniciou',str(error));return 1
    if app_id_warning:controller.warn(app_id_warning)
    app.aboutToQuit.connect(controller.quit)
    return app.exec()

if __name__=='__main__':raise SystemExit(main())
