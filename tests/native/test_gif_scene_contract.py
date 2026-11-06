# SPDX-License-Identifier: GPL-3.0-only
from pathlib import Path
import os
import pytest

os.environ.setdefault('QT_QPA_PLATFORM','offscreen')

@pytest.fixture
def qt_app():
    from PySide6.QtWidgets import QApplication
    return QApplication.instance() or QApplication([])


class RejectingFetcher:
    def __init__(self): self.calls=0
    def submit(self,*_): self.calls+=1; return False
    def cancel(self,*_): pass
    def poll(self): return []
    def clear(self): pass
    def stop(self): pass


class ErrorFetcher(RejectingFetcher):
    def submit(self,item_id,emotion,kind='meme'):
        self.calls+=1;self.ready=[(str(item_id),None,'Nenhum candidato válido retornado')];return True
    def poll(self):
        ready=getattr(self,'ready',[]);self.ready=[];return ready


class ReadyFetcher(RejectingFetcher):
    def __init__(self,payload):super().__init__();self.payload=payload
    def submit(self,item_id,emotion,kind='meme'):
        self.calls+=1;self.ready=[(str(item_id),self.payload,None)];return True
    def poll(self):
        ready=getattr(self,'ready',[]);self.ready=[];return ready


def test_online_reaction_does_not_require_local_meme_and_failed_queue_releases_slot(qt_app,tmp_path,monkeypatch):
    import sys
    sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
    from game import Game
    from pestinha import config
    from bolha.scene import NativeScene
    content=Path(__file__).resolve().parents[2]/'assets/bolha/content'
    game=Game(tmp_path,content)
    game.mischief.max_objects=1
    monkeypatch.setattr(config,'meme_for',lambda *_:None)
    monkeypatch.setattr(config,'list_images',lambda *_:[])
    perms=dict(config.DEFAULT_PERMISSIONS,travessuras=True,memes=True,bilhetes=False,fotos=False)
    assert 'meme' in game.mischief.available('feliz',perms)
    item=game.mischief._make('meme','feliz',False)
    assert item.valida and item.reaction_kind=='online' and item.image is None
    decision=game.intelligence.current_decision
    assert decision['action']=='mischief_content' and decision['target']=='0'
    assert decision['source']=='mischief_world' and 'neural' in decision['factors']
    item.place(300,300);game.mischief._add(item)
    fetcher=RejectingFetcher();scene=NativeScene(game,reaction_fetcher=fetcher)
    scene.sync()
    assert fetcher.calls==1
    assert item.closed and item.id not in game.objects
    assert scene.get_reaction_status(item.id)['state']=='canceled'
    scene.sync()
    assert fetcher.calls==1
    # A worker/network error also removes a manual online item while retaining diagnosis.
    failed=game.mischief.create_online_reaction('feliz')
    failed.place(320,300)
    errors=ErrorFetcher();scene.fetcher=errors
    scene.sync()
    assert errors.calls==1 and failed.closed and failed.id not in game.objects
    assert scene.get_reaction_status(failed.id)['state']=='no-results'
    # The object slot is available for the user's next request.
    retry=game.mischief.create_online_reaction('feliz')
    assert retry is not None
    next_fetcher=RejectingFetcher();next_fetcher.submit=lambda *_:(setattr(next_fetcher,'calls',next_fetcher.calls+1) or True)
    scene.fetcher=next_fetcher;scene.sync()
    assert next_fetcher.calls==1 and retry.id in game.objects
    scene.close()


def test_scene_toy_size_mask_and_negative_monitor_clamp(qt_app,tmp_path):
    import sys
    sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
    from game import Game
    from pestinha.scene import SignThing
    from bolha.scene import NativeScene
    repo=Path(__file__).resolve().parents[2]
    game=Game(tmp_path,repo/'assets/bolha/content')
    game.configure({'avatarSize':48,'objectScales':{'toy':.6}})
    game.ball.body.x,game.ball.body.y=-450,100;game.ball.place()
    scene=NativeScene(game)
    toywindow=None
    scene.sync()
    toywindow=scene.windows[game.ball.id]
    assert game.ball.body.half_w>=10 and toywindow.width()==48
    game.ball.body.y=game.bounds()[3]-game.ball.body.half_h-4
    settled=game.ball.body.y
    for _ in range(100):scene.sync()
    assert game.ball.body.y==settled
    game.areas=[(-800.,-100.,-160.,600.)]
    sign=SignThing('legível');sign.place(-200.,-50.)
    game.prefs.update({'avatarSize':200,'objectScales':{'sign':1.8}})
    scene.sync()
    window=scene.windows[sign.id]
    assert window.width()<=game.areas[0][2]-game.areas[0][0]
    assert window.height()<=game.areas[0][3]-game.areas[0][1]
    assert window.mask().boundingRect().width()==window.width()
    assert game.areas[0][0] <= sign._cx-window.width()/2
    assert sign._cx+window.width()/2 <= game.areas[0][2]
    scene.close()


def test_online_gif_uses_random_usable_desktop_corners_without_repeat(qt_app,tmp_path,monkeypatch):
    import sys
    sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
    import bolha.scene as scene_module
    from game import Game
    from bolha.scene import NativeScene
    repo=Path(__file__).resolve().parents[2]
    game=Game(tmp_path,repo/'assets/bolha/content')
    game.areas=[(-900.,-200.,-200.,500.),(100.,0.,700.,500.)]
    first=game.mischief.create_online_reaction('feliz')
    second=game.mischief.create_online_reaction('observando')
    scene=NativeScene(game)
    monkeypatch.setattr(scene_module.random,'choice',lambda options:options[0])
    assert scene._place_reaction_in_corner(first)
    first_point=(first._cx,first._cy)
    assert scene._place_reaction_in_corner(second)
    second_point=(second._cx,second._cy)
    assert first_point!=second_point
    for thing in (first,second):
        left,top,right,bottom=game.bounds((thing._cx,thing._cy))
        assert left<=thing._cx-thing.width()/2
        assert thing._cx+thing.width()/2<=right
        assert top<=thing._cy-thing.height()/2
        assert thing._cy+thing.height()/2<=bottom
    assert first_point[0]<0 or second_point[0]<0
    scene.close()


def test_gif_fica_limpo_expira_apos_exibicao_e_pausa_no_hover(qt_app,tmp_path,monkeypatch):
    import sys
    sys.path.insert(0,str(Path(__file__).resolve().parents[0]))
    from test_online_reactions import make_payload
    from game import Game
    import bolha.scene as scene_module
    from bolha.scene import NativeScene
    repo=Path(__file__).resolve().parents[2]
    game=Game(tmp_path,repo/'assets/bolha/content')
    game.mischief.max_objects=1
    item=game.mischief.create_online_reaction('feliz');item.place(320,300)
    clock=[100.];monkeypatch.setattr(scene_module.time,'monotonic',lambda:clock[0])
    scene=NativeScene(game,ReadyFetcher(make_payload()))
    scene.sync();window=scene.windows[item.id]
    assert window.reaction_media is not None and window.reaction_remaining==15.
    monkeypatch.setattr(window,'underMouse',lambda:True)
    clock[0]+=20;scene.sync()
    assert item.id in game.objects and window.reaction_remaining==15.
    monkeypatch.setattr(window,'underMouse',lambda:False)
    clock[0]+=14.9;scene.sync();assert item.id in game.objects
    clock[0]+=.2;scene.sync()
    assert item.id not in game.objects and item.closed
    assert scene.get_reaction_status(item.id)['state']=='expired'
    assert window.reaction_media is None
    assert game.mischief.create_online_reaction('feliz') is not None
    scene.close()
