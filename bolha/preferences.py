# SPDX-License-Identifier: GPL-3.0-only
"""Preferências locais: contrato compatível com config.json da versão Electron."""
import math
import copy
from pathlib import Path
from .migration import atomic_json, prepare_data, read_json

OBJECT_SCALE_TYPES = ('toy','notebook','reaction','note','sign','corner','effects')
DEFAULTS = dict(avatarSize=136, opacity=1., roaming=True, position=None,
                objectScales={key:1. for key in OBJECT_SCALE_TYPES},
                toyAppearance='peanut',
                mischiefEnabled=True, onlineReactions=True, mischiefInterval=300, maxObjects=3,
                popEnabled=True, popThrowLimit=12,
                senseApp=True,senseIdle=True,senseCursor=True,senseWindows=True,
                adaptiveBehavior=True,learnRoutine=True)
BOOLEAN_KEYS = ('roaming','mischiefEnabled','onlineReactions','senseApp','senseIdle','senseCursor','senseWindows',
                'adaptiveBehavior','learnRoutine','popEnabled')
SENSOR_KEYS = ('senseApp','senseIdle','senseCursor','senseWindows')


def defaults():
    return copy.deepcopy(DEFAULTS)


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
        self.preferences=sanitize(saved.get('preferences'))
        if saved and saved.get('schemaVersion')!=1:
            self.save({})

    def save(self,patch):
        next_preferences=sanitize(patch,self.preferences)
        atomic_json(self.path,{'schemaVersion':1,'preferences':next_preferences})
        self.preferences=next_preferences
        return dict(self.preferences)

    def reset_appearance(self):
        return self.save({key:DEFAULTS[key] for key in ('avatarSize','opacity')})
