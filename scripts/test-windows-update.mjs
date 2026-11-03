// SPDX-License-Identifier: GPL-3.0-only
import { _electron as electron } from '@playwright/test';
import { createServer } from 'node:http';
import { readFile,mkdtemp,readdir,access } from 'node:fs/promises';
import { createReadStream } from 'node:fs';
import { join,basename } from 'node:path';
import { tmpdir } from 'node:os';
import { spawn } from 'node:child_process';
import assert from 'node:assert/strict';

if(process.platform!=='win32')throw new Error('Este teste exige Windows.');
const root=await mkdtemp(join(tmpdir(),'bolha-native-')),installDir=join(root,'app');
const setup=(await readdir('release')).find(x=>x.endsWith('.exe'));
if(!setup)throw new Error('Instalador base não encontrado.');
await new Promise((resolve,reject)=>{const proc=spawn(join(process.cwd(),'release',setup),['/S',`/D=${installDir}`],{stdio:'inherit'});proc.once('error',reject);proc.once('exit',code=>code===0?resolve():reject(new Error('Instalação base falhou: '+code)));});
const exe=join(installDir,'Bolha.exe');await access(exe);
const feed=join(process.cwd(),'validation/update-feed');
const versionMatch=(await readFile(join(feed,'latest.yml'),'utf8')).match(/^version:\s*['"]?([0-9.]+)/m);
if(!versionMatch)throw new Error('Versão do feed ausente.');
const targetVersion=versionMatch[1];
let corrupt=true;
const server=createServer(async(req,res)=>{
  try{
    const name=basename(new URL(req.url,'http://127.0.0.1').pathname);
    if(!/^(?:latest\.yml|Bolha-Setup-[\w.-]+(?:\.exe|\.blockmap))$/.test(name)){res.writeHead(404);res.end();return;}
    const path=join(feed,name);
    if(name==='latest.yml'){
      let text=await readFile(path,'utf8');
      if(corrupt)text=text.replace(/sha512: .+/g,'sha512: '+'A'.repeat(86)+'==');
      res.end(text);
    }else {await access(path);createReadStream(path).on('error',()=>res.destroy()).pipe(res);}
  }catch{res.writeHead(404);res.end();}
});
await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
const url=`http://127.0.0.1:${server.address().port}/`;
const launch=async data=>{
  const app=await electron.launch({executablePath:exe,env:{...process.env,BOLHA_TEST:'1',BOLHA_TEST_USER_DATA:data,BOLHA_TEST_UPDATE_URL:url,BOLHA_TEST_EXIT_VERSION:targetVersion},timeout:60000});
  const page=await app.firstWindow();await page.waitForSelector('[data-app-ready]',{timeout:45000});await page.waitForSelector('[data-testid=drippy]',{timeout:45000});return{app,page};
};
try{
  const first=await launch(join(root,'first'));
  await first.page.waitForFunction(async()=> (await window.bolha.bootstrap()).update.phase==='error',{},{timeout:120000});
  assert.equal((await first.page.evaluate(()=>window.bolha.bootstrap())).brain.neurons,470);
  corrupt=false;await first.page.evaluate(()=>window.bolha.checkUpdates());
  await first.page.waitForFunction(async()=> (await window.bolha.bootstrap()).update.phase==='ready',{},{timeout:120000});
  let state=(await first.page.evaluate(()=>window.bolha.bootstrap())).update;
  assert.ok(state.installAt-Date.now()<=31000&&state.installAt-Date.now()>15000);
  await first.page.evaluate(()=>window.bolha.deferUpdate());
  state=(await first.page.evaluate(()=>window.bolha.bootstrap())).update;
  assert.ok(state.installAt-Date.now()>3500000);
  await first.app.close();

  // A separate test profile verifies the real 30-second automatic installation.
  const data=join(root,'automatic');
  const second=await launch(data);
  await second.page.evaluate(()=>window.bolha.brainEvent({type:'caress'}));
  const deadline=Date.now()+180000;
  let applied=false;
  while(Date.now()<deadline){
    try{
      const health=JSON.parse(await readFile(join(data,'health.json'),'utf8'));
      const markerExists=await access(join(data,'pending-update.json')).then(()=>true,()=>false);
      if(health.version===targetVersion&&health.neurons===470&&!markerExists){applied=true;break;}
    }catch{}
    await new Promise(resolve=>setTimeout(resolve,500));
  }
  assert.ok(applied,'A atualização automática e a limpeza não concluíram.');
  const memory=JSON.parse(await readFile(join(data,'brain/drippy/nervous.json'),'utf8'));
  assert.equal(memory.seed,1313);
  console.log('Windows nativo: instalação, hash inválido, continuidade, adiamento de 1h, instalação automática após 30s, cérebro, memória e limpeza passaram.');
}finally{server.close();}
