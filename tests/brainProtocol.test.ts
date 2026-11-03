// SPDX-License-Identifier: GPL-3.0-only
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { mergeBrainSnapshot, validBrainEvent } from '../src/shared/brainProtocol';
import type { BrainSnapshot } from '../src/shared/types';

test('gestos válidos passam, payloads inválidos e comandos genéricos são rejeitados',()=>{
  assert.ok(validBrainEvent({type:'drag-end',x:-400,y:800,vx:1200,vy:20}));
  assert.ok(validBrainEvent({type:'panel',value:true}));
  assert.ok(validBrainEvent({type:'rest'}));
  for(const invalid of [null,[],{type:'exec',command:'bad'},{type:'drag',x:NaN,y:1},{type:'drag',x:1},{type:'cursor',x:2,y:3},{type:'poke',url:'https://example.com'},{type:'hover',value:'yes'}])assert.equal(validBrainEvent(invalid),false);
});

test('metadados neurais são mantidos entre quadros e liberados ao fechar o painel',()=>{
  const neural={positions:[[0,0]],trace:[.5],kind:[0],pools:{}};
  const previous={neural,learned:[['a','b',.1]],intelligence:{label:'Observar'}} as BrainSnapshot;
  const next={x:10,learned:[]} as unknown as BrainSnapshot;
  const merged=mergeBrainSnapshot(next,previous,true);
  assert.equal(merged.neural,neural);
  assert.equal(merged.x,10);
  assert.deepEqual(merged.learned,previous.learned);
  assert.equal(mergeBrainSnapshot(next,previous,false).neural,undefined);
});
