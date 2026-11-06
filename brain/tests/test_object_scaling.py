# SPDX-License-Identifier: GPL-3.0-or-later
# Bolha is based on Pestinha by @mille-okws and contributors; see NOTICE.md.
from pestinha.scene import Ball, object_scale, set_scene
from bolha.preferences import defaults, sanitize


class Scene:
    def __init__(self): self.next_id=1; self.objects={}


def test_type_scale_and_collision_geometry():
    app=Scene();set_scene(app)
    ball=Ball(100,100)
    assert object_scale(ball,68,{'toy':1.5}) == .75
    ball.apply_scale(.75)
    assert (ball.width(),ball.height()) == (48,48)
    assert ball.body.half_w == 12.75


def test_scale_preferences_are_finite_bounded_and_independent():
    first=defaults();first['objectScales']['toy']=.6
    assert defaults()['objectScales']['toy']==1.
    values=sanitize({'objectScales':{'toy':float('inf'),'note':3,'reaction':.8}})
    assert values['objectScales']['toy']==1.
    assert values['objectScales']['note']==1.8
    assert values['objectScales']['reaction']==.8
    assert values['avatarSize']==136


def test_pequeno_brinquedo_mantem_raio_legivel_e_padrao_original():
    set_scene(Scene());small=Ball(100,100);small.apply_scale(object_scale(small,48,{'toy':.6}))
    assert small.body.half_w==10
    assert (small.width(),small.height())==(48,48)
    set_scene(Scene());normal=Ball(100,100);normal.apply_scale(1.)
    assert normal.body.half_w==17
