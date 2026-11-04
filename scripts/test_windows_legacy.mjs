// SPDX-License-Identifier: GPL-3.0-only
// Electron antigo somente no runner descartável; o pacote Qt não inclui Node.
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { createReadStream } from 'node:fs';
import { readFile, writeFile, access, mkdir } from 'node:fs/promises';
import { createRequire } from 'node:module';
import { hostname } from 'node:os';
import { join, basename, dirname, resolve } from 'node:path';
import { spawnSync } from 'node:child_process';

assert.equal(process.platform, 'win32');
assert.equal(process.env.GITHUB_ACTIONS, 'true');
assert.equal(process.env.RUNNER_ENVIRONMENT, 'github-hosted');
assert.equal(process.env.RUNNER_OS, 'Windows');
assert.notEqual(hostname().toLowerCase(), 'kukybook26');
const request = JSON.parse(await readFile(process.argv[2], 'utf8'));
const { installer, install, data, feed, targetVersion, output, playwrightRoot } = request;
assert.equal(resolve(data).toLowerCase(), resolve(process.env.APPDATA, 'bolha').toLowerCase());
assert.match(feed, /^http:\/\/127\.0\.0\.1:\d+\/$/);
assert.equal(await access(data).then(() => true, () => false), false, 'Runner já contém dados da Bolha.');
assert.equal(basename(install), 'app');
assert.match(basename(dirname(install)), /^bolha-legacy-validation-/);
assert.equal(await access(install).then(() => true, () => false), false, 'O destino legado deve ser novo.');
const trusted = {
  'Bolha-Setup-0.1.0-x64.exe': 'f7cbd370555ed81d9bcc3fb949c1a7091e61433299c65c0958ca97cf09dc8599',
  'Bolha-Setup-0.2.1-x64.exe': '20078a4cda5d563b6ebac461103cf8a2a2f1b26589cb36dea41b26a8243d16a4',
};
const hash = createHash('sha256');
for await (const chunk of createReadStream(installer)) hash.update(chunk);
assert.equal(hash.digest('hex'), trusted[basename(installer)], 'Instalador legado sem hash conhecido.');
const require = createRequire(join(playwrightRoot, 'package.json'));
const { _electron: electron } = require('@playwright/test');
await mkdir(output, { recursive: true });
const setup = spawnSync(installer, ['/S', `/D=${install}`], { timeout: 180000, stdio: 'inherit' });
assert.equal(setup.status, 0, 'Instalação legada falhou.');
const executablePath = join(install, 'Bolha.exe');
await access(executablePath);
await mkdir(data, { recursive: true });
const deferral = join(data, 'update-deferred.json');
await writeFile(deferral, JSON.stringify({ version: targetVersion, until: Date.now() + 3600000 }));
const environment = { ...process.env, BOLHA_TEST: '1', BOLHA_TEST_STATUS: '1', BOLHA_TEST_ALLOW_STOP: '1',
  BOLHA_TEST_USER_DATA: data, BOLHA_TEST_INSTALL_DIR: install, BOLHA_TEST_UPDATE_URL: feed,
  BOLHA_TEST_LEGACY_CACHE: join(process.env.LOCALAPPDATA, 'bolha-updater'),
  BOLHA_TEST_DURATION: '120', BOLHA_TEST_REPORT: join(output, 'legacy-target-runtime.json') };
delete environment.BOLHA_TEST_FAIL_START;
delete environment.BOLHA_TEST_EXIT_VERSION;
const opened = [];
const readJSON = async path => JSON.parse(await readFile(path, 'utf8'));
async function waitFor(description, predicate, timeout = 120000) {
  const deadline = Date.now() + timeout;
  while (Date.now() < deadline) {
    const result = await predicate().catch(() => false);
    if (result) return result;
    await new Promise(resolve => setTimeout(resolve, 200));
  }
  throw new Error(description);
}
async function launch() {
  const app = await electron.launch({ executablePath, env: environment, timeout: 60000 });
  opened.push(app);
  const page = await app.firstWindow();
  await page.waitForSelector('[data-app-ready]', { timeout: 45000 });
  await page.waitForSelector('.companion', { timeout: 45000 });
  return { app, page };
}
try {
  const first = await launch();
  await first.page.evaluate(() => window.bolha.savePreferences({ avatarSize: 152,
    senseApp: false, senseIdle: false, senseCursor: false, senseWindows: false }));
  await waitFor('Download legado não terminou.', async () => {
    const state = (await first.page.evaluate(() => window.bolha.bootstrap())).update;
    return state.phase === 'ready' && state.installAt - Date.now() > 3500000 && state;
  });
  const pending = await readJSON(join(data, 'pending-update.json'));
  assert.equal(pending.version, targetVersion);
  await first.app.close();
  const candidates = ['bolha', 'drippy'].map(name => join(data, 'brain', name, 'nervous.json'));
  const memoryPath = await waitFor('Memória legada ausente.', async () => {
    for (const path of candidates) if (await access(path).then(() => true, () => false)) return path;
  }, 15000);
  const memory = await readJSON(memoryPath);
  assert.equal(memory.seed, 1313);
  assert(memory.learned?.PRESO && 'CALM' in memory.learned.PRESO);
  memory.learned.PRESO.CALM = .06;
  await writeFile(memoryPath, JSON.stringify(memory));
  await writeFile(deferral, JSON.stringify({ version: targetVersion, until: 0 }));
  const second = await launch();
  const ready = await waitFor('Contagem legada não iniciou.', async () => {
    const state = (await second.page.evaluate(() => window.bolha.bootstrap())).update;
    return state.phase === 'ready' && Number.isFinite(state.installAt) && state;
  });
  assert(ready.installAt - Date.now() > 15000 && ready.installAt - Date.now() <= 31000);
  const health = await waitFor('A versão Qt não confirmou a migração.', async () => {
    const health = await readJSON(join(data, 'health.json'));
    return health.version === targetVersion && health.ready === true && health.neurons === 470 && health;
  }, 180000);
  assert(Date.now() >= ready.installAt - 1000, 'Atualização instalou antes dos 30 segundos.');
  await waitFor('Limpeza do instalador legado não concluiu.', async () =>
    !(await access(join(data, 'pending-update.json')).then(() => true, () => false)) &&
    !(await access(pending.installer).then(() => true, () => false)), 90000);
  assert.equal(await access(join(install, 'resources', 'app.asar')).then(() => true, () => false), false);
  const saved = await readJSON(join(data, 'config.json'));
  assert.equal(saved.preferences.avatarSize, 152);
  for (const key of ['senseApp', 'senseIdle', 'senseCursor', 'senseWindows']) assert.equal(saved.preferences[key], false);
  const learned = await readJSON(join(data, 'brain', 'bolha', 'nervous.json'));
  assert.equal(learned.seed, 1313);
  assert(learned.learned.PRESO.CALM > .04);
  const migration = await readJSON(join(data, 'native-migration.json'));
  assert.equal(migration.schemaVersion, 1);
  assert(migration.backup, 'A migração precisa guardar um backup anterior.');
  const backupFile = join(migration.backup, 'brain', basename(dirname(memoryPath)), 'nervous.json');
  const backupMemory = await readJSON(backupFile);
  assert.equal(backupMemory.seed, 1313);
  assert(backupMemory.learned.PRESO.CALM > .04, 'O backup deve preservar o aprendizado legado.');
  await writeFile(join(data, 'test-stop.request'), 'isolated migration validated');
  const metrics = await waitFor('A versão Qt não encerrou com relatório.', async () => {
    const report = await readJSON(environment.BOLHA_TEST_REPORT);
    return report.version === targetVersion && report.healthy && report;
  }, 25000);
  await writeFile(join(output, 'report.json'), JSON.stringify({ passed: true, mode: 'disposable-legacy',
    legacy: basename(installer), target: targetVersion, health, metrics,
    preferencesPreserved: true, learningPreserved: true, migrationBackupVerified: true,
    installerCleaned: true }, null, 2));
  console.log('PASS Electron → Qt:', basename(installer), '→', targetVersion);
} catch (error) {
  await writeFile(join(output, 'report.json'), JSON.stringify({ passed: false,
    mode: 'disposable-legacy', error: String(error) }, null, 2));
  throw error;
} finally {
  for (const app of opened) {
    try { await app.close(); } catch {}
    try { app.process().kill(); } catch {}
  }
  // Somente o perfil recém-criado neste runner é sinalizado; nenhum taskkill global.
  await writeFile(join(data, 'test-stop.request'), 'isolated validation cleanup').catch(() => {});
}
