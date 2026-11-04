# SPDX-License-Identifier: GPL-3.0-only
"""A expressão de irritação continua ativa sem fazer o corpo escapar da pegada."""
import pytest

from bolha.motion import animation_pose


@pytest.mark.parametrize('phase', [0., 60., 3600.])
@pytest.mark.parametrize('strength', [0., .6, 1.])
def test_segurada_longa_mantem_corpo_firme_sem_offset_do_centro(phase, strength):
    poses = [animation_pose('held', phase + frame / 120, strength)
             for frame in range(3601)]
    for pose in poses:
        assert abs(pose['squash']) <= .03
        assert abs(pose['angle_offset']) <= 1.5
        assert 'x' not in pose and 'y' not in pose
    assert max(pose['squash'] for pose in poses) > .029
    assert min(pose['squash'] for pose in poses) < -.029
    assert max(pose['angle_offset'] for pose in poses) > 1.4
    assert min(pose['angle_offset'] for pose in poses) < -1.4


def test_segurada_firme_preserva_progressao_dos_olhos_orelhas_e_risquinhos():
    early, middle, late = [animation_pose('held', seconds, .8)
                           for seconds in (.1, 1.5, 4.)]
    assert [pose['emotion'] for pose in (early, middle, late)] == ['curioso', 'entediado', 'bravo']
    assert early['eye_open'] > middle['eye_open'] > late['eye_open']
    assert early['ear_raise'] > middle['ear_raise'] > late['ear_raise']
    assert early['ear_tilt'] < middle['ear_tilt'] < late['ear_tilt']
    assert all(pose['effect'] == 'bravo' for pose in (early, middle, late))
    assert early['effect_strength'] < middle['effect_strength'] < late['effect_strength']
