// SPDX-License-Identifier: GPL-3.0-only
import { readdir,readFile,stat } from 'node:fs/promises';
import { join } from 'node:path';
import assert from 'node:assert/strict';

async function files(dir){const out=[];for(const name of await readdir(dir)){const p=join(dir,name);if((await stat(p)).isDirectory())out.push(...await files(p));else out.push(p);}return out;}
const forbidden=/supabase|db\.kuky\.solutions|onedrip\.com\.br|drippy\.kuky\.solutions|dropnoids|signup-safe|chat-ai/i;
for(const file of [...await files('src'),...await files('out')]){
  if(/\.(?:ts|tsx|js|json|html|css)$/.test(file))assert.ok(!forbidden.test(await readFile(file,'utf8')),`Dependência antiga em ${file}`);
}
const pkg=JSON.parse(await readFile('package.json','utf8'));
assert.equal(pkg.name,'bolha');assert.equal(pkg.productName,'Bolha');assert.ok(!('@supabase/supabase-js' in pkg.dependencies));
for(const file of await files('brain')){
  if(file.endsWith('.py'))assert.ok(!/^\s*(?:from|import) PySide6/m.test(await readFile(file,'utf8')),`Qt não deve entrar no processo local: ${file}`);
}
console.log('Auditoria passou: código independente, sem serviços antigos nem renderer Qt.');
