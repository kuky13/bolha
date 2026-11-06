# SPDX-License-Identifier: GPL-3.0-only
from pathlib import Path
from types import SimpleNamespace

from PySide6.QtCore import Qt
from bolha.app import NativeApp
from bolha.pingpong_view import PingPongView
from game import Game


def test_menu_inicia_e_fecha_placar_transparente(qt_application,tmp_path):
    game = Game(tmp_path, Path(__file__).resolve().parents[2]/'assets/bolha/content')
    game.desktop({'areas':[dict(x=-1000,y=-50,width=1000,height=620)]})
    view = PingPongView()
    noop = lambda *args: None
    app = NativeApp.__new__(NativeApp)
    app.__dict__.update(game=game,pingpong_view=view,show_settings=noop,show_neural=noop,
                        request_reaction=noop,updater=SimpleNamespace(check=noop,defer=noop),
                        quit=noop,cancel_interactions=noop,dialogs=[])
    app.interact = lambda kind,**data:game.interact(dict(type=kind,**data))
    menu = app.make_menu()
    try:
        app.pingpong_action.trigger()
        assert game.pingpong is not None and view.isVisible()
        assert view.geometry().getRect()==(-680,-38,360,64)
        assert view.windowFlags() & Qt.WindowTransparentForInput
        assert view.testAttribute(Qt.WA_ShowWithoutActivating)
        assert not view.grab().isNull()
        menu.aboutToShow.emit()
        assert app.pingpong_action.text()=='Encerrar pingue-pongue'
        app.pingpong_action.trigger()
        assert game.pingpong is None and not view.isVisible()
    finally:
        menu.close()
        view.close()
