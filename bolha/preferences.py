# SPDX-License-Identifier: GPL-3.0-or-later
# Bolha is based on Pestinha by @mille-okws and contributors; see NOTICE.md.
"""Preferências locais: contrato compatível com config.json da versão Electron."""
import math
import copy
from pathlib import Path
from .migration import atomic_json, prepare_data, read_json

OBJECT_SCALE_TYPES = ('toy','notebook','reaction','note','sign','corner','effects')
ACTIVITY_SWITCHES = (
    ('Brincadeiras', 'chaseEnabled', 'Correr atrás do brinquedo'),
    ('Brincadeiras', 'juggleEnabled', 'Fazer embaixadinhas'),
    ('Brincadeiras', 'pingpongEnabled', 'Jogar pingue-pongue'),
    ('Brincadeiras', 'notebookEnabled', 'Usar o notebook'),
    ('Expressões e companhia', 'speechEnabled', 'Falas e pensamentos'),
    ('Expressões e companhia', 'notesEnabled', 'Trazer bilhetes'),
    ('Expressões e companhia', 'fireworksEnabled', 'Soltar fogos'),
    ('Protestos e revolução', 'protestsEnabled', 'Protestar e fazer greve'),
    ('Protestos e revolução', 'signsEnabled', 'Segurar cartazes'),
    ('Protestos e revolução', 'revolutionEnabled', 'Lançar brinquedos na revolução'),
)
DEFAULTS = dict(avatarSize=90, opacity=1., roaming=True, position=None,
                mouthEnabled=True, cursorPrankEnabled=False,
                objectScales=dict.fromkeys(OBJECT_SCALE_TYPES, 1.) | {'toy': 1.3, 'notebook': 1.2},
                toyAppearance='ball',
                mischiefEnabled=True, onlineReactions=True, mischiefInterval=120, maxObjects=3,
                popEnabled=True, popThrowLimit=5,
                senseApp=True,senseIdle=True,senseCursor=True,senseWindows=True,
                adaptiveBehavior=True,learnRoutine=True,
                finderEnabled=True,finderDouble=True,finderKey='Alt esquerdo',
                mediaEnabled=True,mediaKey='Ctrl+=',spotifyEnabled=True,
                batteryEnabled=True,batteryAlerts=True,batteryThreshold=15,
                batteryHiddenTrayDevices=[],batteryHiddenPanelDevices=[],mascotTrayIcon=False)
DEFAULTS.update({key: True for _, key, _ in ACTIVITY_SWITCHES})
BOOLEAN_KEYS = ('roaming','mouthEnabled','cursorPrankEnabled','mischiefEnabled','onlineReactions','senseApp','senseIdle','senseCursor','senseWindows',
                'adaptiveBehavior','learnRoutine','popEnabled','finderEnabled','finderDouble','mediaEnabled',
                'spotifyEnabled','batteryEnabled','batteryAlerts','mascotTrayIcon') + tuple(key for _, key, _ in ACTIVITY_SWITCHES)
SENSOR_KEYS = ('senseApp','senseIdle','senseCursor','senseWindows')


def defaults():
    return copy.deepcopy(DEFAULTS)


def previous_install_defaults(*, mobile=False):
    values = defaults()
    values.update(avatarSize=120 if mobile else 136, mischiefInterval=300, popThrowLimit=12,
                  objectScales=dict.fromkeys(OBJECT_SCALE_TYPES, 1.))
    return values


def number(value):
    return type(value) in (int,float) and math.isfinite(value)


def sanitize(patch, previous=None):
    result = copy.deepcopy(previous if previous is not None else DEFAULTS)
    if not isinstance(patch,dict): return result
    if patch.get('toyAppearance') in ('peanut','ball'):result['toyAppearance']=patch['toyAppearance']
    for key in BOOLEAN_KEYS:
        if type(patch.get(key)) is bool: result[key]=patch[key]
    if isinstance(patch.get('objectScales'),dict):
        scales=dict(result.get('objectScales',{}))
        for key in OBJECT_SCALE_TYPES:
            value=patch['objectScales'].get(key)
            if number(value):scales[key]=max(.6,min(1.8,float(value)))
        result['objectScales']=scales
    for key,low,high in (('avatarSize',48,200),('mischiefInterval',60,1800),('maxObjects',1,5)):
        if number(patch.get(key)):result[key]=math.floor(max(low,min(high,patch[key]))+.5)
    if type(patch.get('batteryThreshold')) is int:
        result['batteryThreshold'] = max(1, min(50, patch['batteryThreshold']))
    for setting in ('batteryHiddenTrayDevices', 'batteryHiddenPanelDevices'):
        if isinstance(patch.get(setting), list):
            result[setting] = sorted({key for key in patch[setting] if isinstance(key, str) and key})
    for key in ('finderKey', 'mediaKey'):
        value = patch.get(key)
        if isinstance(value, str) and 0 < len(value) <= 48 and value.isprintable():
            result[key] = value
    if type(patch.get('popThrowLimit')) is int:
        result['popThrowLimit']=max(5,min(30,patch['popThrowLimit']))
    if number(patch.get('opacity')): result['opacity']=max(.2,min(1.,patch['opacity']))
    if 'position' in patch:
        point=patch['position']
        if point is None:result['position']=None
        elif isinstance(point,dict) and all(number(point.get(k)) and abs(point[k])<=100000 for k in ('x','y')):
            result['position']={k:point[k] for k in ('x','y')}
    return result


class PreferencesStore:
    def __init__(self,data_dir):
        self.data_dir=Path(data_dir)
        prepare_data(self.data_dir)
        self.path=self.data_dir/'config.json'
        self.error=''
        try:
            saved=read_json(self.path)
            if not isinstance(saved,dict) or not isinstance(saved.get('preferences'),dict):
                raise ValueError('Estrutura de preferências inválida.')
        except FileNotFoundError:
            saved={}
        except (ValueError,UnicodeError) as error:
            self.error='Configuração ilegível preservada no backup: '+str(error)
            saved={}
            self.preferences=defaults()
            for key in SENSOR_KEYS:self.preferences[key]=False
            return
        self.preferences=sanitize(saved.get('preferences'), previous_install_defaults() if saved else None)
        if saved and saved.get('schemaVersion')!=1:
            self.save({})

    def save(self,patch):
        next_preferences=sanitize(patch,self.preferences)
        atomic_json(self.path,{'schemaVersion':1,'preferences':next_preferences})
        self.preferences=next_preferences
        return dict(self.preferences)

    def reset_appearance(self):
        return self.save({key:DEFAULTS[key] for key in ('avatarSize','opacity')})
