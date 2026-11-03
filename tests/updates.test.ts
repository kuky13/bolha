// SPDX-License-Identifier: GPL-3.0-only
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp,writeFile,readFile,access } from 'node:fs/promises';
import { join } from 'node:path';
import { tmpdir } from 'node:os';
import { compareVersions,installationDeadline,COUNTDOWN,DEFER_INTERVAL } from '../src/shared/updatePolicy';
import { cleanupAppliedUpdate,recordUpdate } from '../src/main/updateCleanup';

test('ordem de versões e prazos de instalação/adiamento',()=>{
  assert.equal(compareVersions('0.1.10','0.1.2'),1);assert.equal(compareVersions('0.1.0','0.1.0'),0);
  assert.throws(()=>compareVersions('../bad','1.0.0'));
  assert.equal(installationDeadline(1000,false),1000+COUNTDOWN);assert.equal(installationDeadline(1000,true),1000+DEFER_INTERVAL);
});
test('instalador só é apagado depois de abrir a versão nova',async()=>{
  const root=await mkdtemp(join(tmpdir(),'bolha-cleanup-')),exe=join(root,'setup.exe'),marker=join(root,'pending.json');
  await writeFile(exe,'fixture');await recordUpdate(marker,{version:'0.1.1',installer:exe},root);
  assert.equal(await cleanupAppliedUpdate(marker,'0.1.0',root),false);assert.equal(await readFile(exe,'utf8'),'fixture');
  assert.equal(await cleanupAppliedUpdate(marker,'0.1.1',root),true);await assert.rejects(access(exe));await assert.rejects(access(marker));
});
test('a limpeza não pode apagar arquivo fora do cache próprio',async()=>{
  const root=await mkdtemp(join(tmpdir(),'bolha-path-')),outside=join(root,'..','unrelated.exe');
  await assert.rejects(recordUpdate(join(root,'pending.json'),{version:'0.1.1',installer:outside},root));
});
