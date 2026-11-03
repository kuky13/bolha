// SPDX-License-Identifier: GPL-3.0-only
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { defaults, sanitizePreferences, validShortcut } from '../src/shared/preferences';

test('a primeira sessão é independente, com passeio e travessuras normais',()=>{
  const prefs=defaults();assert.equal(prefs.roaming,true);assert.equal(prefs.burstLimit,12);assert.equal(prefs.mischiefInterval,300);assert.equal(prefs.maxObjects,3);
});
test('configuração inválida não injeta campos nem valores não finitos',()=>{
  const prefs=sanitizePreferences({avatarSize:NaN,position:{x:Infinity,y:1},maxObjects:999,burstLimit:-9,apiKey:'should not exist',senseWindows:'yes'});
  assert.equal(prefs.avatarSize,136);assert.equal(prefs.position,null);assert.equal(prefs.maxObjects,5);assert.equal(prefs.burstLimit,6);assert.equal(prefs.senseWindows,true);assert.ok(!('apiKey' in prefs));
});
test('atalhos essenciais do sistema não podem ser registrados',()=>{
  assert.equal(validShortcut('Alt+F4'),false);assert.equal(validShortcut('Esc'),false);assert.equal(validShortcut('CommandOrControl+Shift+P'),true);assert.equal(validShortcut('MediaPlayPause'),true);
});
