// SPDX-License-Identifier: GPL-3.0-only
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { validBrainEvent } from '../src/shared/brainProtocol';

test('gestos válidos passam, payloads inválidos e comandos genéricos são rejeitados',()=>{
  assert.ok(validBrainEvent({type:'drag-end',x:-400,y:800,vx:1200,vy:20}));
  assert.ok(validBrainEvent({type:'panel',value:true}));
  for(const invalid of [null,[],{type:'exec',command:'bad'},{type:'drag',x:NaN,y:1},{type:'drag',x:1},{type:'cursor',x:2,y:3},{type:'poke',url:'https://example.com'},{type:'hover',value:'yes'}])assert.equal(validBrainEvent(invalid),false);
});
