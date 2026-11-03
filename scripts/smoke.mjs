// SPDX-License-Identifier: GPL-3.0-only
import { _electron as electron } from '@playwright/test';
import assert from 'node:assert/strict';
import { mkdir,mkdtemp,readFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join,resolve } from 'node:path';

const data=await mkdtemp(join(tmpdir(),'bolha-smoke-'));
const packaged=process.env.BOLHA_SMOKE_EXE;
const args=packaged?[]:['.'];
if(process.platform==='linux')args.unshift('--no-sandbox');
const app=await electron.launch({executablePath:packaged,args,env:{...process.env,BOLHA_TEST:'1',BOLHA_TEST_USER_DATA:data},timeout:45000});
try {
  const page=await app.firstWindow();const errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.waitForSelector('[data-app-ready]',{timeout:30000});
  await page.waitForSelector('[data-testid=drippy]',{timeout:30000});
  const boot=await page.evaluate(()=>window.bolha.bootstrap());
  assert.equal(boot.preferences.roaming,true);assert.equal(boot.brain.neurons,470);
  assert.equal(boot.preferences.adaptiveBehavior,true);assert.equal(boot.preferences.learnRoutine,true);
  await page.evaluate(()=>window.bolha.brainEvent({type:'caress'}));
  await page.getByText('Tá, esse carinho eu aceito. ♡',{exact:true}).waitFor();
  assert.equal((await page.evaluate(()=>window.bolha.bootstrap())).brain.ready,true);
  await page.evaluate(()=>window.bolha.brainEvent({type:'panel',value:true}));
  await page.evaluate(()=>window.bolha.brainEvent({type:'monitor',value:true}));
  await page.evaluate(()=>window.dispatchEvent(new MouseEvent('contextmenu')));
  await page.evaluate(()=>document.querySelector('[data-testid=drippy]').dispatchEvent(new MouseEvent('contextmenu',{bubbles:true,cancelable:true})));
  await page.getByRole('heading',{name:'Bolha',exact:true}).waitFor();
  await page.getByRole('button',{name:'Vida',exact:true}).click();
  assert.equal(await page.getByRole('slider').count(),3);
  await page.getByRole('button',{name:'Acompanhar o cérebro'}).click();
  await page.getByRole('heading',{name:'Por dentro da Drippy'}).waitFor();
  await page.waitForFunction(()=>document.querySelector('canvas')?.width===420);
  await page.getByRole('heading',{name:'Objetivo agora'}).waitFor();
  await mkdir('validation',{recursive:true});
  await page.screenshot({path:'validation/neural-smoke.png'});
  await page.getByRole('button',{name:'Fechar painel'}).click();
  await page.evaluate(()=>document.querySelector('[data-testid=drippy]').dispatchEvent(new MouseEvent('contextmenu',{bubbles:true,cancelable:true})));
  await page.getByRole('heading',{name:'Bolha',exact:true}).waitFor();
  await page.screenshot({path:'validation/settings-smoke.png'});
  assert.deepEqual(errors,[]);
  const health=JSON.parse(await readFile(join(data,'health.json'),'utf8'));
  assert.equal(health.neurons,470);
  console.log(JSON.stringify({platform:process.platform,renderer:true,brain:470,settings:true,neuralPanel:true,screenshot:'validation/settings-smoke.png',errors}));
} finally { await app.close(); }
