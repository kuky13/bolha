# SPDX-License-Identifier: GPL-3.0-or-later
# Bolha is based on Pestinha by @mille-okws and contributors; see NOTICE.md.
"""Plataformas usam o topo visível, em vez dos cantos de telas diferentes."""
import pytest
from geometry import visible_window_platforms
from pestinha.core.physics import Body, CLOSE_BUTTONS


def display(x=0, y=0, width=1920, height=1080, scale=1., native_x=None, native_y=None, id=0):
    return dict(id=id,x=x,y=y,width=width,height=height-40,monitorX=x,monitorY=y,
                monitorWidth=width,monitorHeight=height,scaleFactor=scale,
                nativeX=x if native_x is None else native_x,nativeY=y if native_y is None else native_y,
                nativeWidth=width*scale,nativeHeight=height*scale)


def usable(platform):
    identity,left,right,top=platform
    return identity,left,right-CLOSE_BUTTONS,top


def test_normal_window_and_close_button_area_are_in_logical_coordinates():
    result=visible_window_platforms([(7,(200,300,1200,900),False)],[display()])
    assert len(result)==1
    identity,left,right,top=usable(result[0])
    assert identity==(7,'0',0)
    assert (left,right,top)==pytest.approx((210,1050,300))
    assert result==visible_window_platforms([(7,(200,300,1200,900),False)],[display()])


def test_cross_screen_window_splits_top_with_own_dpi_and_no_double_close_button_trim():
    monitors=[display(),display(1920,width=1280,height=720,scale=1.5,id=1)]
    window=(7,(1700,300,2600,900),False)
    result=visible_window_platforms([window],monitors)
    first,second=map(usable,result)
    assert first[1:]==pytest.approx((1710,1920,300))
    assert second[1:]==pytest.approx((1920,1920+(2600-225-1920)/1.5,200))
    assert first[0]!=second[0]
    # A queda pousa também no fim do segmento primário, sem retirar 150 DIP
    # de cada lado da costura da mesma janela.
    body=Body(1880,289,10,10,circular=True);body.vy=50
    body.step(.016,(0,0,1920,1040),result)
    assert body.grounded and body.platform==result[0][0] and body.surface==300


def test_bottom_corner_on_other_monitor_does_not_change_top_width():
    monitors=[display(),display(0,1080,width=1280,height=720,scale=1.5,native_y=1080,id=1)]
    result=visible_window_platforms([(7,(200,300,1100,1600),False)],monitors)
    assert len(result)==1
    assert usable(result[0])[1:]==pytest.approx((210,950,300))


def test_negative_monitor_coordinates_and_dip_gap_produce_separate_surfaces():
    monitors=[display(),display(-1920,width=1280,height=720,scale=1.5,id=1)]
    result=visible_window_platforms([(7,(-800,300,500,900),False)],monitors)
    primary,left_screen=map(usable,result)
    assert primary[1:]==pytest.approx((0,350,300))
    assert left_screen[1:]==pytest.approx((-1920+1135/1.5,-640,200))
    assert all(not(-640<p[1]<0) and not(-640<p[2]<0) for p in map(usable,result))


def test_foreground_window_removes_covered_top_without_trimming_visible_segment_ends():
    front=(10,(500,150,800,600),False)
    back=(20,(100,300,1400,900),False)
    result=visible_window_platforms([front,back],[display()])
    parts=[usable(p) for p in result if p[0][0]==20]
    assert len(parts)==2
    assert parts[0][1:]==pytest.approx((110,500,300))
    assert parts[1][1:]==pytest.approx((800,1250,300))
    assert parts[0][2]<500
    assert len({p[0] for p in result})==len(result)
    body=Body(650,289,10,10,circular=True);body.vy=50
    body.step(.016,(0,0,1920,1040),result)
    assert not body.grounded
    body=Body(900,289,10,10,circular=True);body.vy=50
    body.step(.016,(0,0,1920,1040),result)
    assert body.grounded and body.platform==parts[1][0]


def test_maximized_foreground_occludes_without_producing_own_platform():
    windows=[(1,(0,0,1920,1040),True),(2,(100,300,1400,900),False)]
    assert visible_window_platforms(windows,[display()])==[]


def test_window_below_top_does_not_occlude_and_hidden_platform_support_is_released():
    back=(20,(100,300,1400,900),False)
    low=(10,(500,350,800,700),False)
    initial=visible_window_platforms([low,back],[display()])
    p=next(p for p in initial if p[0][0]==20)
    assert usable(p)[1:]==pytest.approx((110,1250,300))
    body=Body(650,290,10,10,circular=True)
    body.grounded=True;body.platform=p[0];body.surface=300
    updated=visible_window_platforms([(10,(500,150,800,700),False),back],[display()])
    body.step(.1,(0,0,1920,1040),updated)
    assert not body.grounded and body.platform is None


def test_work_area_clips_native_edges_and_offscreen_and_degenerate_windows_are_ignored():
    screen=display();screen['x']=40;screen['width']=1880
    assert visible_window_platforms([(1,(20,-50,800,500),False)],[screen])==[]
    result=visible_window_platforms([(1,(-100,300,2300,900),False)],[screen])
    assert usable(result[0])[1:]==pytest.approx((40,1920,300))
    assert visible_window_platforms([(1,(100,300,100,900),False)], [screen])==[]


def test_above_monitor_with_negative_native_y_maps_only_its_top():
    monitors=[display(),display(0,-1080,width=960,height=1080,scale=2.,native_y=-2160,id=1)]
    result=visible_window_platforms([(7,(100,-1800,1500,400),False)],monitors)
    assert len(result)==1
    assert usable(result[0])[1:]==pytest.approx((60,600,-900))


def test_supported_body_finds_right_segment_again_after_window_moves_horizontally():
    monitor=display()
    front=(10,(500,150,800,700),False)
    original=visible_window_platforms([front,(20,(100,300,1400,900),False)],[monitor])
    p=next(p for p in original if p[0][0]==20 and p[1]>=800)
    body=Body(900,290,10,10,circular=True)
    body.grounded=True;body.surface=300;body.platform=p[0]
    moved=visible_window_platforms([front,(20,(180,300,1480,900),False)],[monitor])
    body.step(.016,(0,0,1920,1040),moved)
    assert body.grounded and body.platform==p[0] and body.y==290


def test_native_context_builds_cross_app_platforms_and_respects_sensor(tmp_path, monkeypatch):
    import sys
    from types import SimpleNamespace
    from pathlib import Path
    import pestinha.plataforma
    from game import Game
    game=Game(tmp_path,Path(__file__).resolve().parents[2]/'assets/bolha/content')
    game.configure(dict(senseIdle=False,senseApp=False,senseWindows=True))
    game.displays=[display(),display(1920,width=1280,height=720,scale=1.5,id=1)]
    windows=[(7,(1700,300,2600,900),False),(8,(100,550,1000,900),False)]
    native=SimpleNamespace(janelas_visiveis=lambda _:windows,
        win32con=SimpleNamespace(GWL_STYLE=-16,GWL_EXSTYLE=-20,WS_EX_LAYERED=0x80000,
                                 WS_CAPTION=0xc00000,WS_THICKFRAME=0x40000),
        win32gui=SimpleNamespace(GetWindowLong=lambda _hwnd,kind:0xc00000 if kind==-16 else 0))
    monkeypatch.setattr(pestinha.plataforma,'windows',native,raising=False)
    monkeypatch.setitem(sys.modules,'pestinha.plataforma.windows',native)
    with monkeypatch.context() as platform:
        platform.setattr(sys,'platform','win32')
        game.read_context(100.)
    assert game.native_error is None
    assert len(game.platforms)==3
    assert {p[0][0] for p in game.platforms}=={7,8}
    assert {p[3] for p in game.platforms}=={300.,200.,550.}
    game.configure(dict(senseWindows=False))
    native.janelas_visiveis=lambda _:pytest.fail('Leitura desativada foi executada')
    with monkeypatch.context() as platform:
        platform.setattr(sys,'platform','win32')
        game.read_context(101.)
    assert game.platforms==[] and game.native_error is None
