// SPDX-License-Identifier: GPL-3.0-only
import { _electron as electron } from '@playwright/test';
import { mkdtemp,mkdir,writeFile,readFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
const data=await mkdtemp(join(tmpdir(),'bolha-benchmark-'));
const packaged=process.env.BOLHA_SMOKE_EXE;
const args=packaged?[]:['.'];
if(process.platform==='linux')args.unshift('--no-sandbox');
const app=await electron.launch({executablePath:packaged,args,env:{...process.env,BOLHA_TEST:'1',BOLHA_TEST_USER_DATA:data}});
const started=Date.now();
const results={at:new Date().toISOString(),version:JSON.parse(await readFile('package.json','utf8')).version,scenarios:{},method:'Soma do RSS dos processos (memória compartilhada pode ser contada mais de uma vez); CPU em porcentagem de um núcleo.'};
try{
  const page=await app.firstWindow();await page.waitForSelector('[data-testid=drippy]',{timeout:45000});
  const measure=async name=>{
    const {stdout}=await promisify(execFile)(process.env.BOLHA_PYTHON??'python',['scripts/measure-tree.py',String(app.process().pid),process.env.BOLHA_BENCH_SECONDS??'20'],{maxBuffer:1024*1024,timeout:3700000});
    results.scenarios[name]=JSON.parse(stdout);console.log(name,stdout.trim());
  };
  await measure('active');
  await page.evaluate(()=>window.bolha.brainEvent({type:'monitor',value:true}));
  await measure('neuralMonitor');
  results.intelligence=(await page.evaluate(()=>window.bolha.bootstrap())).brain.intelligence;
  results.selectorCpuPercent=results.intelligence?.cpuSeconds/((Date.now()-started)/1000)*100;
  await page.evaluate(()=>{window.bolha.brainEvent({type:'monitor',value:false});window.bolha.brainEvent({type:'panic'});});
  await measure('paused');
  results.brainTargetMet=Object.values(results.scenarios).every(s=>s.peakBrainRssMiB>0&&s.peakBrainRssMiB*1048576<=100000000);
  await mkdir('validation',{recursive:true});
  await writeFile(`validation/performance-${process.platform}.json`,JSON.stringify(results,null,2)+'\n');
}finally{await app.close();}
