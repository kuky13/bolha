// SPDX-License-Identifier: GPL-3.0-only
import { readdir, mkdtemp } from 'node:fs/promises';
import { join } from 'node:path';
import { tmpdir } from 'node:os';
import { spawnSync } from 'node:child_process';
import { build } from 'esbuild';

const output = await mkdtemp(join(tmpdir(),'bolha-tests-'));
const files = (await readdir('tests')).filter(name=>name.endsWith('.test.ts'));
if (!files.length) throw new Error('Nenhum teste encontrado.');
for (const file of files) {
  const target=join(output,file+'.mjs');
  await build({entryPoints:[join('tests',file)],bundle:true,platform:'node',format:'esm',outfile:target,packages:'external'});
  const result=spawnSync(process.execPath,['--test',target],{stdio:'inherit'});
  if(result.status!==0)process.exit(result.status??1);
}
