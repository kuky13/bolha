# SPDX-License-Identifier: GPL-3.0-only
"""Preferências locais: contrato compatível com config.json da versão Electron."""
import math
from pathlib import Path
from .migration import atomic_json, prepare_data, read_json

DEFAULTS = dict(avatarSize=136, opacity=1., roaming=True, position=None,
                toyAppearance='peanut',
                mischiefEnabled=True, mischiefInterval=300, maxObjects=3,
                senseApp=True,senseIdle=True,senseCursor=True,senseWindows=True,
                adaptiveBehavior=True,learnRoutine=True)
BOOLEAN_KEYS = ('roaming','mischiefEnabled','senseApp','senseIdle','senseCursor','senseWindows',
                'adaptiveBehavior','learnRoutine')
SENSOR_KEYS = ('senseApp','senseIdle','senseCursor','senseWindows')


def defaults():
    return dict(DEFAULTS)


def number(value):
    return type(value) in (int,float) and math.isfinite(value)


def sanitize(patch, previous=None):
    result = dict(previous if previous is not None else DEFAULTS)
    if not isinstance(patch,dict): return result
    if patch.get('toyAppearance') in ('peanut','ball'):result['toyAppearance']=patch['toyAppearance']
    for key in BOOLEAN_KEYS:
        if type(patch.get(key)) is bool: result[key]=patch[key]
    for key,low,high in (('avatarSize',80,200),('mischiefInterval',60,1800),('maxObjects',1,5)):
        if number(patch.get(key)):result[key]=math.floor(max(low,min(high,patch[key]))+.5)
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
