// SPDX-License-Identifier: GPL-3.0-only
import { _electron as electron } from '@playwright/test';
import { createServer } from 'node:http';
import { readFile,writeFile,copyFile,mkdir,mkdtemp,readdir,access,stat,rm } from 'node:fs/promises';
import { createReadStream } from 'node:fs';
import { join,basename } from 'node:path';
import { tmpdir } from 'node:os';
import { spawn,spawnSync } from 'node:child_process';
import assert from 'node:assert/strict';

if(process.platform!=='win32')throw new Error('Este teste exige Windows.');
const root=await mkdtemp(join(tmpdir(),'bolha-native-')),installDir=join(root,'app');
const setup=(await readdir('release')).find(x=>x.endsWith('.exe'));
if(!setup)throw new Error('Instalador base não encontrado.');
const baseInstaller=process.env.BOLHA_UPDATE_TEST_BASE??join(process.cwd(),'release',setup);
await new Promise((resolve,reject)=>{const proc=spawn(baseInstaller,['/S',`/D=${installDir}`],{stdio:'inherit'});proc.once('error',reject);proc.once('exit',code=>code===0?resolve():reject(new Error('Instalação base falhou: '+code)));});
const exe=join(installDir,'Bolha.exe');await access(exe);
const feed=process.env.BOLHA_UPDATE_TEST_FEED??join(process.cwd(),'validation/update-feed');
const versionMatch=(await readFile(join(feed,'latest.yml'),'utf8')).match(/^version:\s*['"]?([0-9.]+)/m);
if(!versionMatch)throw new Error('Versão do feed ausente.');
const targetVersion=versionMatch[1];
let corrupt=true, interrupt=false, interrupted=false;
const server=createServer(async(req,res)=>{
  try{
    const name=basename(new URL(req.url,'http://127.0.0.1').pathname);
    if(!/^(?:latest\.yml|Bolha-Setup-[\w.-]+(?:\.exe|\.blockmap))$/.test(name)){res.writeHead(404);res.end();return;}
    const path=join(feed,name);
    if(name==='latest.yml'){
      let text=await readFile(path,'utf8');
      if(corrupt)text=text.replace(/sha512: .+/g,'sha512: '+'A'.repeat(86)+'==');
      res.end(text);
    }else {
      await access(path);
      if(interrupt&&name.endsWith('.exe')){
        interrupted=true;
        res.writeHead(200,{'Content-Length':(await stat(path)).size});
        const stream=createReadStream(path,{end:65535});
        stream.on('error',()=>res.destroy()).on('end',()=>res.destroy()).pipe(res,{end:false});
      }else createReadStream(path).on('error',()=>res.destroy()).pipe(res);
    }
  }catch{res.writeHead(404);res.end();}
});
await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
const url=`http://127.0.0.1:${server.address().port}/`;
const apps=[];
let automaticData;
const launch=async (data,normalProfile=false)=>{
  const env={...process.env,BOLHA_TEST:'1',BOLHA_TEST_USER_DATA:data,BOLHA_TEST_UPDATE_URL:url,BOLHA_TEST_EXIT_VERSION:targetVersion};
  if(normalProfile)delete env.BOLHA_TEST_USER_DATA;
  const app=await electron.launch({executablePath:exe,env,timeout:60000});
  apps.push(app);
  const page=await app.firstWindow();await page.waitForSelector('[data-app-ready]',{timeout:45000});await page.waitForSelector('.companion',{timeout:45000});return{app,page};
};
async function waitUpdate(page,predicate,timeout=120000){
  const deadline=Date.now()+timeout;let state;
  do{
    state=(await page.evaluate(()=>window.bolha.bootstrap())).update;
    if(predicate(state))return state;
    await new Promise(resolve=>setTimeout(resolve,200));
  }while(Date.now()<deadline);
  throw new Error('Atualização não chegou ao estado esperado: '+JSON.stringify(state));
}
try{
  const firstData=join(root,'first'),first=await launch(firstData);
  await waitUpdate(first.page,state=>state.phase==='error');
  const hashLogs=await first.page.evaluate(()=>window.bolha.logs());
  assert.ok(hashLogs.some(entry=>/checksum|sha512/i.test(entry.message)),'O download com checksum inválido deve ser rejeitado.');
  console.log('Checksum inválido rejeitado; aplicativo continua funcionando.');
  assert.equal((await first.page.evaluate(()=>window.bolha.bootstrap())).brain.neurons,470);
  corrupt=false;interrupt=true;await first.page.evaluate(()=>window.bolha.checkUpdates());
  await waitUpdate(first.page,state=>state.phase==='error');
  assert.ok(interrupted,'A conexão de download deve ser interrompida pelo servidor de teste.');
  console.log('Download interrompido tratado; aplicativo continua funcionando.');
  assert.equal((await first.page.evaluate(()=>window.bolha.bootstrap())).brain.neurons,470);
  interrupt=false;await first.page.evaluate(()=>window.bolha.checkUpdates());
  let state=await waitUpdate(first.page,state=>state.phase==='ready'&&Number.isFinite(state.installAt));
  console.log(JSON.stringify({stage:'download-ready',state,now:Date.now(),remaining:state.installAt-Date.now()}));
  assert.ok(state.installAt-Date.now()<=31000&&state.installAt-Date.now()>15000);
  await first.page.evaluate(()=>window.bolha.deferUpdate());
  state=(await first.page.evaluate(()=>window.bolha.bootstrap())).update;
  assert.ok(state.installAt-Date.now()>3500000);
  await first.page.evaluate(()=>window.bolha.savePreferences({avatarSize:152}));
  await first.app.close();
  const resumed=await launch(firstData);
  state=await waitUpdate(resumed.page,state=>state.phase==='ready');
  assert.ok(state.installAt-Date.now()>3500000,'O adiamento deve sobreviver ao reinício.');
  console.log('Adiamento de uma hora preservado após reiniciar.');
  await resumed.app.close();

  // NSIS restarts through the Windows shell, which need not inherit test env vars.
  const data=join(process.env.APPDATA,'bolha');
  assert.equal(await access(data).then(()=>true,()=>false),false,'Este teste precisa de um runner sem perfil Bolha anterior.');
  automaticData=data;
  const memoryFolder=(await readdir(join(firstData,'brain'),{withFileTypes:true})).find(entry=>entry.isDirectory());
  assert.ok(memoryFolder,'A versão anterior deve ter salvo sua pasta de memória.');
  await mkdir(join(data,'brain',memoryFolder.name),{recursive:true});
  await copyFile(join(firstData,'config.json'),join(data,'config.json'));
  const seeded=JSON.parse(await readFile(join(firstData,'brain',memoryFolder.name,'nervous.json'),'utf8'));
  const post=Object.keys(seeded.learned.PRESO)[0];
  seeded.learned.PRESO[post]=.06;
  await writeFile(join(data,'brain',memoryFolder.name,'nervous.json'),JSON.stringify(seeded));
  const second=await launch(data,true);
  await second.page.evaluate(()=>window.bolha.brainEvent({type:'caress'}));
  const deadline=Date.now()+180000;
  let applied=false,downloadedInstaller;
  while(Date.now()<deadline){
    try{
      try{downloadedInstaller=JSON.parse(await readFile(join(data,'pending-update.json'),'utf8')).installer;}catch{}
      const health=JSON.parse(await readFile(join(data,'health.json'),'utf8'));
      const markerExists=await access(join(data,'pending-update.json')).then(()=>true,()=>false);
      if(health.version===targetVersion&&health.neurons===470&&!markerExists){applied=true;break;}
    }catch{}
    await new Promise(resolve=>setTimeout(resolve,500));
  }
  if(!applied){
    const diagnostics={};
    for(const [name,path] of Object.entries({health:join(data,'health.json'),pending:join(data,'pending-update.json'),logs:join(data,'logs/session.log')})){
      diagnostics[name]=await readFile(path,'utf8').catch(error=>String(error));
    }
    console.log(JSON.stringify({stage:'update-timeout',diagnostics}));
    await writeFile('validation/native-update-debug.json',JSON.stringify(diagnostics,null,2));
  }
  assert.ok(applied,'A atualização automática e a limpeza não concluíram.');
  const memory=JSON.parse(await readFile(join(data,'brain/bolha/nervous.json'),'utf8'));
  assert.equal(memory.seed,1313);
  assert.ok(memory.learned.PRESO[post]>.04,'O aprendizado anterior deve sobreviver à atualização.');
  assert.equal(JSON.parse(await readFile(join(data,'config.json'),'utf8')).preferences.avatarSize,152);
  assert.ok(downloadedInstaller,'O teste deve observar o instalador no cache.');
  assert.equal(await access(downloadedInstaller).then(()=>true,()=>false),false,'O instalador deve ser apagado depois da nova versão saudável.');
  console.log('Windows nativo: instalação, hash inválido, download interrompido, continuidade, adiamento persistente de 1h, instalação automática após 30s, cérebro, memória e limpeza passaram.');
}finally{
  server.closeAllConnections();server.close();
  for(const app of apps){
    try{await Promise.race([app.close(),new Promise(resolve=>setTimeout(resolve,5000))]);}catch{}
    try{app.process().kill();}catch{}
  }
  if(automaticData){
    try{
      const health=JSON.parse(await readFile(join(automaticData,'health.json'),'utf8'));
      if(health.version===targetVersion&&Number.isInteger(health.pid))spawnSync('taskkill',['/PID',String(health.pid),'/T','/F'],{stdio:'ignore'});
    }catch{}
    await rm(automaticData,{recursive:true,force:true,maxRetries:5,retryDelay:1000});
  }
}
