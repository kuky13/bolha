# SPDX-License-Identifier: GPL-3.0-or-later
# Bolha is based on Pestinha by @mille-okws and contributors; see NOTICE.md.
"""Menu e configurações usam o modelo real, sem conexão de rede."""
from pathlib import Path
from types import SimpleNamespace
from types import MethodType

from bolha.app import NativeApp
from bolha.preferences import defaults, sanitize
from bolha.scene import NativeScene
from game import Game


class Fetcher:
    def __init__(self): self.requests=[]
    def submit(self,*request): self.requests.append(request);return True
    def poll(self): return []
    def cancel(self,*_): pass
    def clear(self): pass
    def stop(self): pass


def controller(tmp_path):
    game=Game(tmp_path,Path(__file__).resolve().parents[2]/'assets/bolha/content')
    prefs=defaults();prefs.update(senseApp=False,senseIdle=False,senseCursor=False,senseWindows=False)
    game.configure(prefs)
    fetcher=Fetcher()
    scene=NativeScene(game,reaction_fetcher=fetcher)
    app=SimpleNamespace(game=game,scene=scene,pet=SimpleNamespace(sync=lambda:None),store=SimpleNamespace(preferences=prefs))
    app.interact=MethodType(NativeApp.interact,app)
    app.reaction_status=MethodType(NativeApp.reaction_status,app)
    return app,fetcher


def test_manual_reaction_works_with_settings_open(qt_application,tmp_path):
    app,fetcher=controller(tmp_path)
    app.game.panel=True
    try:
        status=NativeApp.request_reaction(app)
        assert len(fetcher.requests)==1
        assert any(row['state']=='loading' for row in status.values())
    finally:app.scene.close()


def test_manual_reaction_reports_disabled_without_network(qt_application,tmp_path):
    app,fetcher=controller(tmp_path)
    app.store.preferences['onlineReactions']=False
    app.game.configure(app.store.preferences)
    try:
        status=NativeApp.request_reaction(app)
        assert not fetcher.requests
        assert 'Ative as reações' in status['request']['reason']
    finally:app.scene.close()


def test_size_adjustment_preserves_other_types_and_avatar():
    saved=[];prefs=defaults()
    def save(patch):
        value=sanitize(patch,prefs);saved.append(value);return value
    app=SimpleNamespace(store=SimpleNamespace(preferences=prefs),save_preferences=save)
    result=NativeApp.adjust_object_scale(app,'toy',.7)
    assert result['objectScales']['toy']==.7
    assert result['objectScales']['notebook']==1.
    assert result['avatarSize']==136
    assert prefs['objectScales']['toy']==1.
    assert NativeApp.adjust_object_scale(app,'toy',reset=True)['objectScales']['toy']==1.
