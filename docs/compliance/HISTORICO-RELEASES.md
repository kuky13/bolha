# Histórico das 24 releases públicas

A API do GitHub retornou 24 releases públicas (`v0.1.0` a `v0.5.9.2`). As referências Git foram resolvidas ao commit do tag. A inspeção estática listou o conteúdo de 24 instaladores Windows, oito APKs Android e cinco ZIPs de fonte. Instaladores Electron foram abertos com 7-Zip para examinar o arquivo ASAR. Os SHA-256 de 139 arquivos obtidos localmente coincidiram com os digests da API. Os 15 itens auxiliares sem cópia local (`.blockmap` e `.tar.gz`) apresentam o digest informado pelo GitHub. Nenhum hash comparado divergiu. Essa evidência não demonstra equivalência completa entre fonte e binário. [Releases públicas](https://github.com/kuky13/bolha/releases).

## Resumo por Gerações

| Geração | Releases | Stack | Estado Jurídico / Conformidade | Achados Principais |
|---|---|---|---|---|
| **1. Electron legado** | `v0.1.0`, `v0.1.1`, `v0.2.1` | Electron `45.2.1`, Chrome `156.0.8078.75`, Node `24.22.1`, React `18.3.1`, `app.asar` + `BolhaBrain.exe` | **Revisão histórica** | `package.json` declara `GPL-3.0-only`; artes em `CC BY-NC 4.0` (`CC-BY-NC-4.0.txt`); `v0.1.0` e `v0.1.1` incluem `DRIPPY-ASSETS.md` e 412 ocorrências `drippy` no `app.asar`; sem anexo de fonte próprio |
| **2. Qt inicial (pré-PR #2)** | `v0.3.0`, `v0.3.3`, `v0.4.0`, `v0.4.1`, `v0.4.2`, `v0.4.3` | Python `3.11.9`, `PySide6-Essentials 6.11.3`, `OpenSSL 3.0.13`, `Mesa 11.2.2/LLVM 3.6.2`, NSIS | **Revisão histórica** | `THIRD-PARTY-NOTICES.txt` declara Bolha `GPL-3.0-only` e artes `CC BY-NC 4.0` (com `CC-BY-NC-4.0.txt` dentro do instalador); omite avisos de OpenSSL 3.0.13, Mesa/LLVM e QtSvg; `v0.3.3`–`v0.4.2` incluíram `Bolha-*-fonte.zip` + `PROVENIENCIA.json` |
| **3. Qt GPL-corrigida (pré-integrações)** | `v0.4.4`, `v0.4.10`, `v0.5.0`, `v0.5.1`, `v0.5.2`, `v0.5.3`, `v0.5.4`, `v0.5.5`, `v0.5.6` | Python `3.11.9` + Qt `6.11.3` (Windows) e Chaquopy `17.2.0` + CPython `3.13.16` + NumPy `2.3.2` (Android a partir da `v0.4.10`) | **Correções de avisos prioritárias** | Corrigiu código e artes para `GPL-3.0-or-later`; porém manteve ausência de avisos de `OpenSSL 3.0.13`, `Mesa 11.2.2/LLVM 3.6.2` e `QtSvg` no Windows, título congelado em `Bolha 0.4.4`, ausência de tela completa de avisos legais e perda do `Bolha-*-fonte.zip` a partir da `v0.5.0` |
| **4. Qt + Integrações Windows** | `v0.5.7`, `v0.5.8`, `v0.5.9`, `v0.5.9.0`, `v0.5.9.1`, `v0.5.9.2` | Mesma base + `BatteryHub 1.1.0`, `headsetcontrol 4.3.0`, `PyWinRT 3.2.1` (+ Android na `v0.5.9.0`) | **Correções de avisos prioritárias** | Anexa fontes `BatteryHub-1.1.0-source.tar.gz` e `headsetcontrol-4.3.0.tar.gz` e `PYWINRT-MIT.txt`, mas mantém título `Bolha 0.4.4` em `THIRD-PARTY-NOTICES.txt`, omite OpenSSL/Mesa/QtSvg, inclui `LicenseRef-Qt-Commercial.txt`, omite `Bolha-*-fonte.zip` e mantém `Nekos.best` + `ReactionGIFs` ativos em `bolha/reactions.py` |
| **5. Branch pós-release** | `origin/feat/bolha-support-0594` (`ce28e6e`) | Não publicado em release | **Em preparação** | Integra cliente privado de relatos (`https://api.kuky.solutions/bolha/v1/reports`) em `bolha/reports.py` e `ReportActivity.java` e notas de primeiros passos |

---

## Dependências npm nos instaladores Electron

Os arquivos `app.asar` das três releases Electron (`0.1.0`, `0.1.1` e `0.2.1`) contêm o mesmo inventário de 52 combinações únicas de pacote e versão. As licenças abaixo são as declarações dos próprios pacotes empacotados. A quarta coluna indica o arquivo de aviso encontrado na raiz de cada pacote. Para eventual redistribuição histórica, confira o aviso integral e o titular no registro oficial e distingua o runtime Node/Chromium, o FFmpeg e o worker Python, que são componentes do instalador fora deste inventário npm.

| Pacote | Versão | Licença declarada | Arquivo no pacote |
|---|---|---|---|
| [ajv](https://www.npmjs.com/package/ajv/v/8.20.0) | `8.20.0` | `MIT` | LICENSE |
| [ajv-formats](https://www.npmjs.com/package/ajv-formats/v/2.1.1) | `2.1.1` | `MIT` | LICENSE |
| [argparse](https://www.npmjs.com/package/argparse/v/2.0.1) | `2.0.1` | `Python-2.0` | LICENSE |
| [atomically](https://www.npmjs.com/package/atomically/v/1.7.0) | `1.7.0` | `MIT` | LICENSE |
| [builder-util-runtime](https://www.npmjs.com/package/builder-util-runtime/v/9.7.0) | `9.7.0` | `MIT` | LICENSE |
| [conf](https://www.npmjs.com/package/conf/v/10.2.0) | `10.2.0` | `MIT` | license |
| [debounce-fn](https://www.npmjs.com/package/debounce-fn/v/4.0.0) | `4.0.0` | `MIT` | license |
| [debug](https://www.npmjs.com/package/debug/v/4.4.3) | `4.4.3` | `MIT` | LICENSE |
| [dot-prop](https://www.npmjs.com/package/dot-prop/v/6.0.1) | `6.0.1` | `MIT` | license |
| [electron-store](https://www.npmjs.com/package/electron-store/v/8.2.0) | `8.2.0` | `MIT` | license |
| [electron-updater](https://www.npmjs.com/package/electron-updater/v/6.8.11) | `6.8.11` | `MIT` | LICENSE |
| [env-paths](https://www.npmjs.com/package/env-paths/v/2.2.1) | `2.2.1` | `MIT` | license |
| [fast-deep-equal](https://www.npmjs.com/package/fast-deep-equal/v/3.1.3) | `3.1.3` | `MIT` | LICENSE |
| [fast-uri](https://www.npmjs.com/package/fast-uri/v/3.1.9) | `3.1.9` | `BSD-3-Clause` | LICENSE |
| [find-up](https://www.npmjs.com/package/find-up/v/3.0.0) | `3.0.0` | `MIT` | license |
| [framer-motion](https://www.npmjs.com/package/framer-motion/v/11.18.2) | `11.18.2` | `MIT` | LICENSE.md |
| [fs-extra](https://www.npmjs.com/package/fs-extra/v/10.1.0) | `10.1.0` | `MIT` | LICENSE |
| [graceful-fs](https://www.npmjs.com/package/graceful-fs/v/4.2.11) | `4.2.11` | `ISC` | LICENSE |
| [is-obj](https://www.npmjs.com/package/is-obj/v/2.0.0) | `2.0.0` | `MIT` | license |
| [js-tokens](https://www.npmjs.com/package/js-tokens/v/4.0.0) | `4.0.0` | `MIT` | LICENSE |
| [js-yaml](https://www.npmjs.com/package/js-yaml/v/4.3.2) | `4.3.2` | `MIT` | LICENSE |
| [json-schema-traverse](https://www.npmjs.com/package/json-schema-traverse/v/1.0.0) | `1.0.0` | `MIT` | LICENSE |
| [json-schema-typed](https://www.npmjs.com/package/json-schema-typed/v/7.0.3) | `7.0.3` | `BSD-2-Clause` | LICENSE |
| [jsonfile](https://www.npmjs.com/package/jsonfile/v/6.2.1) | `6.2.1` | `MIT` | LICENSE |
| [lazy-val](https://www.npmjs.com/package/lazy-val/v/1.0.5) | `1.0.5` | `MIT` | Sem arquivo próprio identificado |
| [locate-path](https://www.npmjs.com/package/locate-path/v/3.0.0) | `3.0.0` | `MIT` | license |
| [lodash.escaperegexp](https://www.npmjs.com/package/lodash.escaperegexp/v/4.1.2) | `4.1.2` | `MIT` | LICENSE |
| [lodash.isequal](https://www.npmjs.com/package/lodash.isequal/v/4.5.0) | `4.5.0` | `MIT` | LICENSE |
| [loose-envify](https://www.npmjs.com/package/loose-envify/v/1.4.0) | `1.4.0` | `MIT` | LICENSE |
| [lucide-react](https://www.npmjs.com/package/lucide-react/v/0.451.0) | `0.451.0` | `ISC` | LICENSE |
| [mimic-fn](https://www.npmjs.com/package/mimic-fn/v/2.1.0) | `2.1.0` | `MIT` | license |
| [mimic-fn](https://www.npmjs.com/package/mimic-fn/v/3.1.0) | `3.1.0` | `MIT` | license |
| [motion-dom](https://www.npmjs.com/package/motion-dom/v/11.18.1) | `11.18.1` | `MIT` | LICENSE.md |
| [motion-utils](https://www.npmjs.com/package/motion-utils/v/11.18.1) | `11.18.1` | `MIT` | LICENSE.md |
| [ms](https://www.npmjs.com/package/ms/v/2.1.3) | `2.1.3` | `MIT` | license.md |
| [onetime](https://www.npmjs.com/package/onetime/v/5.1.2) | `5.1.2` | `MIT` | license |
| [p-limit](https://www.npmjs.com/package/p-limit/v/2.3.0) | `2.3.0` | `MIT` | license |
| [p-locate](https://www.npmjs.com/package/p-locate/v/3.0.0) | `3.0.0` | `MIT` | license |
| [p-try](https://www.npmjs.com/package/p-try/v/2.2.0) | `2.2.0` | `MIT` | license |
| [path-exists](https://www.npmjs.com/package/path-exists/v/3.0.0) | `3.0.0` | `MIT` | license |
| [pkg-up](https://www.npmjs.com/package/pkg-up/v/3.1.0) | `3.1.0` | `MIT` | license |
| [react](https://www.npmjs.com/package/react/v/18.3.1) | `18.3.1` | `MIT` | LICENSE |
| [react-dom](https://www.npmjs.com/package/react-dom/v/18.3.1) | `18.3.1` | `MIT` | LICENSE |
| [require-from-string](https://www.npmjs.com/package/require-from-string/v/2.0.2) | `2.0.2` | `MIT` | license |
| [sax](https://www.npmjs.com/package/sax/v/1.6.1) | `1.6.1` | `BlueOak-1.0.0` | LICENSE.md |
| [scheduler](https://www.npmjs.com/package/scheduler/v/0.23.2) | `0.23.2` | `MIT` | LICENSE |
| [semver](https://www.npmjs.com/package/semver/v/7.7.4) | `7.7.4` | `ISC` | LICENSE |
| [semver](https://www.npmjs.com/package/semver/v/7.8.6) | `7.8.6` | `ISC` | LICENSE |
| [tiny-typed-emitter](https://www.npmjs.com/package/tiny-typed-emitter/v/2.1.0) | `2.1.0` | `MIT` | LICENSE |
| [tslib](https://www.npmjs.com/package/tslib/v/2.9.1) | `2.9.1` | `0BSD` | LICENSE.txt |
| [type-fest](https://www.npmjs.com/package/type-fest/v/2.19.0) | `2.19.0` | `(MIT OR CC0-1.0)` | Sem arquivo próprio identificado |
| [universalify](https://www.npmjs.com/package/universalify/v/2.0.1) | `2.0.1` | `MIT` | LICENSE |

Dois pacotes exigem conferência dos avisos no material publicado: `lazy-val` e `type-fest`. A busca por nomes de arquivos não determina se há crédito dentro de um README ou de outros avisos entregues com o instalador.

## Mapeamento Detalhado das 24 Releases

### `v0.5.9.2` — Bolha 0.5.9.2

- **Tag → Commit:** `v0.5.9.2` → `9b8aa78497e0cbbfc674ea8e6186e876ba7eee16` (Testar a ativação da bandeja sem disputar o foco do Windows)
- **Data (GitHub):** `2026-11-22T22:10:25Z`
- **Workflows no commit:** `.github/workflows/android.yml`, `.github/workflows/windows.yml`
- **Manifestos / Avisos:** `installed-files.json` (interno), `PYWINRT-MIT.txt` (interno) | Cabeçalho `THIRD-PARTY-NOTICES.txt`: `Bolha 0.4.4 — componentes redistribuídos`
- **Fontes anexas na release:** `BatteryHub-1.1.0-source.tar.gz`, `headsetcontrol-4.3.0.tar.gz`
- **Estado de conformidade:** **Correções de avisos prioritárias** — Inclui fontes `BatteryHub`/`headsetcontrol` e `PYWINRT-MIT.txt`, mas `THIRD-PARTY-NOTICES.txt` mantém cabeçalho `Bolha 0.4.4`, omite OpenSSL 3.0.13 / Mesa 11.2.2 / QtSvg, inclui `LicenseRef-Qt-Commercial.txt`, omite `Bolha-*-fonte.zip`, sem tela completa de avisos legais e mantém `ReactionGIFs`/`Nekos.best`.
- **Assets e SHA-256:**
  - `BatteryHub-1.1.0-source.tar.gz` (517409 bytes) — `sha256:2737323731e53ab8d936b2fa5c95ab84f2cb7c6abb3d05d3bf150af8c637f108`
  - `Bolha-Setup-0.5.9.2-x64.exe` (36618835 bytes) — `sha256:f75f6c9886214ac747ddeb8fb6f8d256e8d453e3d73c11b9b7b02e2756be35f6`
  - `headsetcontrol-4.3.0.tar.gz` (610215 bytes) — `sha256:918dcacf8aef347744b36b2d259d76880fa64b3869f0f8ef26b6576b873d28a7`
  - `latest.yml` (368 bytes) — `sha256:95ce722931a2c3d9641da218279aab40d5368f692fae25ab24ff39829cd20e39`
  - `SHA256SUMS.txt` (457 bytes) — `sha256:383d441407e6641b323382a4bcb8dc053410ad16fa41da04dd8ee916c350f056`
  - `THIRD-PARTY-NOTICES.txt` (2543 bytes) — `sha256:7b159e60c85441b23aa069b4fbe0b57f89bffed0f4b76484ba60439c2f6b3b5e`

### `v0.5.9.1` — Bolha 0.5.9.1

- **Tag → Commit:** `v0.5.9.1` → `075ac6111f088d977c9ed830eea64b70a3287e97` (Arquivar fontes e pacote verificado do BatteryHub)
- **Data (GitHub):** `2026-11-22T18:46:43Z`
- **Workflows no commit:** `.github/workflows/android.yml`, `.github/workflows/windows.yml`
- **Manifestos / Avisos:** `installed-files.json` (interno), `PYWINRT-MIT.txt` (interno) | Cabeçalho `THIRD-PARTY-NOTICES.txt`: `Bolha 0.4.4 — componentes redistribuídos`
- **Fontes anexas na release:** `BatteryHub-1.1.0-source.tar.gz`, `headsetcontrol-4.3.0.tar.gz`
- **Estado de conformidade:** **Correções de avisos prioritárias** — Inclui fontes `BatteryHub`/`headsetcontrol` e `PYWINRT-MIT.txt`, mas `THIRD-PARTY-NOTICES.txt` mantém cabeçalho `Bolha 0.4.4`, omite OpenSSL 3.0.13 / Mesa 11.2.2 / QtSvg, inclui `LicenseRef-Qt-Commercial.txt`, omite `Bolha-*-fonte.zip`, sem tela completa de avisos legais e mantém `ReactionGIFs`/`Nekos.best`.
- **Assets e SHA-256:**
  - `BatteryHub-1.1.0-source.tar.gz` (517409 bytes) — `sha256:2737323731e53ab8d936b2fa5c95ab84f2cb7c6abb3d05d3bf150af8c637f108`
  - `Bolha-Setup-0.5.9.1-x64.exe` (36620153 bytes) — `sha256:2f45a19f0d4995dfd1bf91ce7ef4abcd205464821cb6a1260e767412f5a0e5cc`
  - `headsetcontrol-4.3.0.tar.gz` (610215 bytes) — `sha256:918dcacf8aef347744b36b2d259d76880fa64b3869f0f8ef26b6576b873d28a7`
  - `latest.yml` (368 bytes) — `sha256:a60db3834c8e174f1fe2942be5954a5efdec624301570870a003825e609a8c1c`
  - `SHA256SUMS.txt` (457 bytes) — `sha256:00e5ed3f7caaf71d722f0736b276b31bb9a975a6dc4369395e1014b243f499c4`
  - `THIRD-PARTY-NOTICES.txt` (2543 bytes) — `sha256:7b159e60c85441b23aa069b4fbe0b57f89bffed0f4b76484ba60439c2f6b3b5e`

### `v0.5.9.0` — Bolha 0.5.9.0

- **Tag → Commit:** `v0.5.9.0` → `82b96f27e98d27f35ce062caaf229718b9b737e2` (Keep the update receipt until recovery cleanup finishes)
- **Data (GitHub):** `2026-11-21T17:33:13Z`
- **Workflows no commit:** `.github/workflows/android.yml`, `.github/workflows/windows.yml`
- **Manifestos / Avisos:** `installed-files.json` (interno), `PYWINRT-MIT.txt` (interno), `assets/chaquopy/build.json` + `.imy`, `assets/licenses/android/NOTICE.md` | Cabeçalho `THIRD-PARTY-NOTICES.txt`: `Bolha 0.4.4 — componentes redistribuídos`
- **Fontes anexas na release:** `BatteryHub-1.1.0-source.tar.gz`, `headsetcontrol-4.3.0.tar.gz`
- **Estado de conformidade:** **Correções de avisos prioritárias** — Inclui fontes `BatteryHub`/`headsetcontrol` e `PYWINRT-MIT.txt`, mas `THIRD-PARTY-NOTICES.txt` mantém cabeçalho `Bolha 0.4.4`, omite OpenSSL 3.0.13 / Mesa 11.2.2 / QtSvg, inclui `LicenseRef-Qt-Commercial.txt`, omite `Bolha-*-fonte.zip`, sem tela completa de avisos legais e mantém `ReactionGIFs`/`Nekos.best`.
- **Assets e SHA-256:**
  - `ANDROID-SHA256SUMS.txt` (92 bytes) — `sha256:f8ea3832d8e2117134ac91ae0b1018de067f5447a95b7534a8eb130e06a099b7`
  - `BatteryHub-1.1.0-source.tar.gz` (517409 bytes) — `sha256:2737323731e53ab8d936b2fa5c95ab84f2cb7c6abb3d05d3bf150af8c637f108`
  - `Bolha-0.5.9.0-Android.apk` (60281489 bytes) — `sha256:adf270cdda8e847579d11f6dd0e7eb60470737be800b0d2e252ec79e4cb4a2ba`
  - `Bolha-Setup-0.5.9.0-x64.exe` (36615932 bytes) — `sha256:6c75bb23dc30975cf2211adc40eb0f1f09f60121bbafe43c5a972c8f2b431603`
  - `headsetcontrol-4.3.0.tar.gz` (610215 bytes) — `sha256:918dcacf8aef347744b36b2d259d76880fa64b3869f0f8ef26b6576b873d28a7`
  - `latest.yml` (368 bytes) — `sha256:0779182b6c06180013b0c02c249bced41d145ec1e804b7e098e8645c1099c4b2`
  - `SHA256SUMS.txt` (457 bytes) — `sha256:3792e795cfda80b79977c5844db596c77dcfa805146a842034827b316dbd3fa7`
  - `THIRD-PARTY-NOTICES.txt` (2543 bytes) — `sha256:7b159e60c85441b23aa069b4fbe0b57f89bffed0f4b76484ba60439c2f6b3b5e`

### `v0.5.9` — Bolha 0.5.9

- **Tag → Commit:** `v0.5.9` → `fe3d8de68705c3ee0f360e8e20f6952de53e5dd9` (Merge Bolha 0.5.9 e sincronização do fork [skip ci])
- **Data (GitHub):** `2026-11-21T16:46:54Z`
- **Workflows no commit:** `.github/workflows/android.yml`, `.github/workflows/windows.yml`
- **Manifestos / Avisos:** `installed-files.json` (interno), `PYWINRT-MIT.txt` (interno) | Cabeçalho `THIRD-PARTY-NOTICES.txt`: `Bolha 0.4.4 — componentes redistribuídos`
- **Fontes anexas na release:** `BatteryHub-1.1.0-source.tar.gz`, `headsetcontrol-4.3.0.tar.gz`
- **Estado de conformidade:** **Correções de avisos prioritárias** — Inclui fontes `BatteryHub`/`headsetcontrol` e `PYWINRT-MIT.txt`, mas `THIRD-PARTY-NOTICES.txt` mantém cabeçalho `Bolha 0.4.4`, omite OpenSSL 3.0.13 / Mesa 11.2.2 / QtSvg, inclui `LicenseRef-Qt-Commercial.txt`, omite `Bolha-*-fonte.zip`, sem tela completa de avisos legais e mantém `ReactionGIFs`/`Nekos.best`.
- **Assets e SHA-256:**
  - `BatteryHub-1.1.0-source.tar.gz` (517409 bytes) — `sha256:2737323731e53ab8d936b2fa5c95ab84f2cb7c6abb3d05d3bf150af8c637f108`
  - `Bolha-Setup-0.5.9-x64.exe` (36606588 bytes) — `sha256:82a8eaece5d64c57c8ed4758fda6a8d057d3ccd89537be223a234fc74868176b`
  - `headsetcontrol-4.3.0.tar.gz` (610215 bytes) — `sha256:918dcacf8aef347744b36b2d259d76880fa64b3869f0f8ef26b6576b873d28a7`
  - `latest.yml` (362 bytes) — `sha256:33c89f1daf34a81594b4a41ed9a318ccc4fca5a0e162eca20e9b3ad77fa4c345`
  - `SHA256SUMS.txt` (455 bytes) — `sha256:a7f737f1b13db5d6d25443a0ebcc0f1362585f8b3f69c6c52cfdb51913058f8f`
  - `THIRD-PARTY-NOTICES.txt` (2543 bytes) — `sha256:7b159e60c85441b23aa069b4fbe0b57f89bffed0f4b76484ba60439c2f6b3b5e`

### `v0.5.8` — Bolha 0.5.8

- **Tag → Commit:** `v0.5.8` → `50ccfe63b770baa64ece635f2f702b4f91129c1e` (Merge Bolha 0.5.8 para Windows [skip ci])
- **Data (GitHub):** `2026-11-21T16:20:19Z`
- **Workflows no commit:** `.github/workflows/android.yml`, `.github/workflows/windows.yml`
- **Manifestos / Avisos:** `installed-files.json` (interno), `PYWINRT-MIT.txt` (interno) | Cabeçalho `THIRD-PARTY-NOTICES.txt`: `Bolha 0.4.4 — componentes redistribuídos`
- **Fontes anexas na release:** `BatteryHub-1.1.0-source.tar.gz`, `headsetcontrol-4.3.0.tar.gz`
- **Estado de conformidade:** **Correções de avisos prioritárias** — Inclui fontes `BatteryHub`/`headsetcontrol` e `PYWINRT-MIT.txt`, mas `THIRD-PARTY-NOTICES.txt` mantém cabeçalho `Bolha 0.4.4`, omite OpenSSL 3.0.13 / Mesa 11.2.2 / QtSvg, inclui `LicenseRef-Qt-Commercial.txt`, omite `Bolha-*-fonte.zip`, sem tela completa de avisos legais e mantém `ReactionGIFs`/`Nekos.best`.
- **Assets e SHA-256:**
  - `BatteryHub-1.1.0-source.tar.gz` (517409 bytes) — `sha256:2737323731e53ab8d936b2fa5c95ab84f2cb7c6abb3d05d3bf150af8c637f108`
  - `Bolha-Setup-0.5.8-x64.exe` (36602094 bytes) — `sha256:a714ec7d38dd9036970c945945edac4f5b315a443051b84f2767ed63f759d087`
  - `headsetcontrol-4.3.0.tar.gz` (610215 bytes) — `sha256:918dcacf8aef347744b36b2d259d76880fa64b3869f0f8ef26b6576b873d28a7`
  - `latest.yml` (362 bytes) — `sha256:025ae03fa3a199a0e9812c0889d307ef01c90001a1cd7f9c03f622d8e08fda33`
  - `SHA256SUMS.txt` (455 bytes) — `sha256:8acfe0ab21131998dc085389de1cb7703cf34ec8ebb1cf73af292f42da7b62d6`
  - `THIRD-PARTY-NOTICES.txt` (2543 bytes) — `sha256:7b159e60c85441b23aa069b4fbe0b57f89bffed0f4b76484ba60439c2f6b3b5e`

### `v0.5.7` — Bolha 0.5.7

- **Tag → Commit:** `v0.5.7` → `9a6ab73f4da8ca9e2b808022fb39c998c5daf074` (Merge Bolha 0.5.7: integrações Windows [skip ci])
- **Data (GitHub):** `2026-11-21T15:23:20Z`
- **Workflows no commit:** `.github/workflows/android.yml`, `.github/workflows/windows.yml`
- **Manifestos / Avisos:** `installed-files.json` (interno), `PYWINRT-MIT.txt` (interno) | Cabeçalho `THIRD-PARTY-NOTICES.txt`: `Bolha 0.4.4 — componentes redistribuídos`
- **Fontes anexas na release:** `BatteryHub-1.1.0-source.tar.gz`, `headsetcontrol-4.3.0.tar.gz`
- **Estado de conformidade:** **Correções de avisos prioritárias** — Inclui fontes `BatteryHub`/`headsetcontrol` e `PYWINRT-MIT.txt`, mas `THIRD-PARTY-NOTICES.txt` mantém cabeçalho `Bolha 0.4.4`, omite OpenSSL 3.0.13 / Mesa 11.2.2 / QtSvg, inclui `LicenseRef-Qt-Commercial.txt`, omite `Bolha-*-fonte.zip`, sem tela completa de avisos legais e mantém `ReactionGIFs`/`Nekos.best`.
- **Assets e SHA-256:**
  - `BatteryHub-1.1.0-source.tar.gz` (517409 bytes) — `sha256:2737323731e53ab8d936b2fa5c95ab84f2cb7c6abb3d05d3bf150af8c637f108`
  - `Bolha-Setup-0.5.7-x64.exe` (36589202 bytes) — `sha256:05456b93f7c499a9a14b5ffed6ea470ad2aaf975dce7597f6d2931056f5ee9a3`
  - `headsetcontrol-4.3.0.tar.gz` (610215 bytes) — `sha256:918dcacf8aef347744b36b2d259d76880fa64b3869f0f8ef26b6576b873d28a7`
  - `latest.yml` (362 bytes) — `sha256:7589af5fb5c5e0d1d76c454290b39fe13184ce54f810513c8657ff1396e462b4`
  - `SHA256SUMS.txt` (455 bytes) — `sha256:058b0d48cf7596f1a149c73279178b5ce80b94a8dd1aaa783d3dabc4ccd15b7a`
  - `THIRD-PARTY-NOTICES.txt` (2543 bytes) — `sha256:7b159e60c85441b23aa069b4fbe0b57f89bffed0f4b76484ba60439c2f6b3b5e`

### `v0.5.6` — Bolha 0.5.6

- **Tag → Commit:** `v0.5.6` → `58623f183430e52e38220d4543781db74d639533` (Merge pull request #12: Bolha 0.5.6)
- **Data (GitHub):** `2026-11-20T15:14:21Z`
- **Workflows no commit:** `.github/workflows/android.yml`, `.github/workflows/windows.yml`
- **Manifestos / Avisos:** `installed-files.json` (interno), `assets/chaquopy/build.json` + `.imy`, `assets/licenses/android/NOTICE.md` | Cabeçalho `THIRD-PARTY-NOTICES.txt`: `Bolha 0.4.4 — componentes redistribuídos`
- **Fontes anexas na release:** Nenhum arquivo-fonte anexado (apenas código no tag Git)
- **Estado de conformidade:** **Correções de avisos prioritárias** — Corrigido para `GPL-3.0-or-later`, porém omite avisos de OpenSSL 3.0.13, Mesa/LLVM e QtSvg, inclui `LicenseRef-Qt-Commercial.txt`, sem tela completa de avisos legais e (a partir de `v0.5.0`) sem `*-fonte.zip`; `v0.5.0`+ mantém `ReactionGIFs`/`Nekos.best`.
- **Assets e SHA-256:**
  - `ANDROID-SHA256SUMS.txt` (90 bytes) — `sha256:e221007e96e5ae9dac374414a068e29860946e75d8daad35ecbb2369da3d37ca`
  - `Bolha-0.5.6-Android.apk` (60232221 bytes) — `sha256:3fd444a00294959160a90e607a82e895b2e2e44f65138fdbb0f3f73fb35662f3`
  - `Bolha-Setup-0.5.6-x64.exe` (34998943 bytes) — `sha256:52129bd4e4bbf8a92d6584bfd6828ee8d14ae7218705069cf059ae84e85215d5`
  - `latest.yml` (362 bytes) — `sha256:1facbef1a7c96aba7e086d32443b933878efd08b78c4413026115e346f76454c`
  - `SHA256SUMS.txt` (262 bytes) — `sha256:61f9e8b6c012b4c627896dccf431f0e606d30ea71766e19ba9ed2cb2678c8f65`
  - `THIRD-PARTY-NOTICES.txt` (1702 bytes) — `sha256:c3d433e7b1ca78be44ea2829b57122fa8e1cf9af2425662e3d69f64c7e9a122d`

### `v0.5.5` — Bolha 0.5.5

- **Tag → Commit:** `v0.5.5` → `d07b1db07df6604b335dfa9bbf7cc67cdbb08147` (Merge pull request #10 from kuky13/fix/brain-system-polish)
- **Data (GitHub):** `2026-11-19T18:29:53Z`
- **Workflows no commit:** `.github/workflows/android.yml`, `.github/workflows/windows.yml`
- **Manifestos / Avisos:** `installed-files.json` (interno), `assets/chaquopy/build.json` + `.imy`, `assets/licenses/android/NOTICE.md` | Cabeçalho `THIRD-PARTY-NOTICES.txt`: `Bolha 0.4.4 — componentes redistribuídos`
- **Fontes anexas na release:** Nenhum arquivo-fonte anexado (apenas código no tag Git)
- **Estado de conformidade:** **Correções de avisos prioritárias** — Corrigido para `GPL-3.0-or-later`, porém omite avisos de OpenSSL 3.0.13, Mesa/LLVM e QtSvg, inclui `LicenseRef-Qt-Commercial.txt`, sem tela completa de avisos legais e (a partir de `v0.5.0`) sem `*-fonte.zip`; `v0.5.0`+ mantém `ReactionGIFs`/`Nekos.best`.
- **Assets e SHA-256:**
  - `ANDROID-SHA256SUMS.txt` (90 bytes) — `sha256:021ee708375c319f1052faebbe00fcf554b322c4307e5e2bab5c2deaa6fbd2d6`
  - `Bolha-0.5.5-Android.apk` (60216349 bytes) — `sha256:76c218371ff4672f2a9e3b12880179e05e768560c45a9aea779c6d77ecfa0738`
  - `Bolha-Setup-0.5.5-x64.exe` (35014732 bytes) — `sha256:0b09d36804a5e53b197e98fa46e8003be8fa68bd0927bf5729fdb181b57d9b1c`
  - `latest.yml` (362 bytes) — `sha256:5d1b1a898fea6997bb061339c656c1acac70a84b70ba890657cd129e1627f3c7`
  - `SHA256SUMS.txt` (262 bytes) — `sha256:41ff4d5184215d03664e96461fa5b90288f0a1ffbf9cb20c5c940d6ca7a3ddd2`
  - `THIRD-PARTY-NOTICES.txt` (1702 bytes) — `sha256:c3d433e7b1ca78be44ea2829b57122fa8e1cf9af2425662e3d69f64c7e9a122d`

### `v0.5.4` — Bolha 0.5.4

- **Tag → Commit:** `v0.5.4` → `3b3f60ad40c674b640674655b28e011518b41194` (Merge pull request #9 from kuky13/feat/bolha-0.5.4-revolucao-e-testes)
- **Data (GitHub):** `2026-11-19T17:15:54Z`
- **Workflows no commit:** `.github/workflows/android.yml`, `.github/workflows/windows.yml`
- **Manifestos / Avisos:** `installed-files.json` (interno), `assets/chaquopy/build.json` + `.imy`, `assets/licenses/android/NOTICE.md` | Cabeçalho `THIRD-PARTY-NOTICES.txt`: `Bolha 0.4.4 — componentes redistribuídos`
- **Fontes anexas na release:** Nenhum arquivo-fonte anexado (apenas código no tag Git)
- **Estado de conformidade:** **Correções de avisos prioritárias** — Corrigido para `GPL-3.0-or-later`, porém omite avisos de OpenSSL 3.0.13, Mesa/LLVM e QtSvg, inclui `LicenseRef-Qt-Commercial.txt`, sem tela completa de avisos legais e (a partir de `v0.5.0`) sem `*-fonte.zip`; `v0.5.0`+ mantém `ReactionGIFs`/`Nekos.best`.
- **Assets e SHA-256:**
  - `ANDROID-SHA256SUMS.txt` (90 bytes) — `sha256:24946041cd80bf6b1190611073ee855c7e37057fcdc932bdb3c1cc3aeda09786`
  - `Bolha-0.5.4-Android.apk` (60216645 bytes) — `sha256:7fbb35ea8cac66ae563330d4cecd496dc79eac5b37fd3b92857f38658528f025`
  - `Bolha-Setup-0.5.4-x64.exe` (34993790 bytes) — `sha256:9c9d170135fef587878500369005071b6f62a5dc9bf1fd120c5d56255a0d9007`
  - `latest.yml` (362 bytes) — `sha256:35895f761ad2afee1e5e7a193782bc8e95ef194813230126a14f905d534de8f8`
  - `SHA256SUMS.txt` (262 bytes) — `sha256:76482aca7b0bfce34a15c5177f9e1dc9f4cda2fdb4f971cae10ae75ae209009d`
  - `THIRD-PARTY-NOTICES.txt` (1702 bytes) — `sha256:c3d433e7b1ca78be44ea2829b57122fa8e1cf9af2425662e3d69f64c7e9a122d`

### `v0.5.3` — Bolha 0.5.3

- **Tag → Commit:** `v0.5.3` → `adf065e290eba26c2bd1c3c4574750bda33733cb` (Prepare Bolha 0.5.3 for Windows and Android)
- **Data (GitHub):** `2026-11-15T23:21:35Z`
- **Workflows no commit:** `.github/workflows/android.yml`, `.github/workflows/windows.yml`
- **Manifestos / Avisos:** `installed-files.json` (interno), `assets/chaquopy/build.json` + `.imy`, `assets/licenses/android/NOTICE.md` | Cabeçalho `THIRD-PARTY-NOTICES.txt`: `Bolha 0.4.4 — componentes redistribuídos`
- **Fontes anexas na release:** Nenhum arquivo-fonte anexado (apenas código no tag Git)
- **Estado de conformidade:** **Correções de avisos prioritárias** — Corrigido para `GPL-3.0-or-later`, porém omite avisos de OpenSSL 3.0.13, Mesa/LLVM e QtSvg, inclui `LicenseRef-Qt-Commercial.txt`, sem tela completa de avisos legais e (a partir de `v0.5.0`) sem `*-fonte.zip`; `v0.5.0`+ mantém `ReactionGIFs`/`Nekos.best`.
- **Assets e SHA-256:**
  - `ANDROID-SHA256SUMS.txt` (90 bytes) — `sha256:5d17be712acebd05120e0bed53ed47b62ae6740656037347a231ed3248990097`
  - `Bolha-0.5.3-Android.apk` (60200253 bytes) — `sha256:07a0c43b817a0685e3426f33c09fe34f902984e55273129c4675268e10143b4c`
  - `Bolha-Setup-0.5.3-x64.exe` (34980983 bytes) — `sha256:70e81a3b55374c8dbf9746babef68805cead132653971c79d6c386121128d01f`
  - `latest.yml` (362 bytes) — `sha256:ce2a8e255f8ddb13b3b0d5eb7b4029cbeef2445fc111c9bf74dc32d0db4303cc`
  - `SHA256SUMS.txt` (262 bytes) — `sha256:491b01cef217f594f26599178284e7db7136de20fcfd922b445d21d4cda4a964`
  - `THIRD-PARTY-NOTICES.txt` (1702 bytes) — `sha256:c3d433e7b1ca78be44ea2829b57122fa8e1cf9af2425662e3d69f64c7e9a122d`

### `v0.5.2` — Bolha 0.5.2

- **Tag → Commit:** `v0.5.2` → `6e946a996687c730092ed1af510a32087fb57b61` (Prepare Bolha 0.5.2 Windows release)
- **Data (GitHub):** `2026-11-14T13:35:14Z`
- **Workflows no commit:** `.github/workflows/android.yml`, `.github/workflows/windows.yml`
- **Manifestos / Avisos:** `installed-files.json` (interno) | Cabeçalho `THIRD-PARTY-NOTICES.txt`: `Bolha 0.4.4 — componentes redistribuídos`
- **Fontes anexas na release:** Nenhum arquivo-fonte anexado (apenas código no tag Git)
- **Estado de conformidade:** **Correções de avisos prioritárias** — Corrigido para `GPL-3.0-or-later`, porém omite avisos de OpenSSL 3.0.13, Mesa/LLVM e QtSvg, inclui `LicenseRef-Qt-Commercial.txt`, sem tela completa de avisos legais e (a partir de `v0.5.0`) sem `*-fonte.zip`; `v0.5.0`+ mantém `ReactionGIFs`/`Nekos.best`.
- **Assets e SHA-256:**
  - `Bolha-Setup-0.5.2-x64.exe` (34970521 bytes) — `sha256:a08701b93a751d9c8987f30d97df1c8843673eab6efd2697f08ed153e493e677`
  - `latest.yml` (362 bytes) — `sha256:66ffa84804cd9373d51c2b71764c039dcf8d059eeb136e3a637eea2bc414bddd`
  - `SHA256SUMS.txt` (262 bytes) — `sha256:0fad7e360d6fc6782fc56f7b009a5eac7f8d1a380e301a72647e6f87eff80ffd`
  - `THIRD-PARTY-NOTICES.txt` (1702 bytes) — `sha256:c3d433e7b1ca78be44ea2829b57122fa8e1cf9af2425662e3d69f64c7e9a122d`

### `v0.5.1` — Bolha 0.5.1

- **Tag → Commit:** `v0.5.1` → `69e0019b371a9081635a36af307fc2ae6303485a` (Prepare Bolha 0.5.1 release)
- **Data (GitHub):** `2026-11-13T19:19:40Z`
- **Workflows no commit:** `.github/workflows/android.yml`, `.github/workflows/windows.yml`
- **Manifestos / Avisos:** `installed-files.json` (interno), `assets/chaquopy/build.json` + `.imy`, `assets/licenses/android/NOTICE.md` | Cabeçalho `THIRD-PARTY-NOTICES.txt`: `Bolha 0.4.4 — componentes redistribuídos`
- **Fontes anexas na release:** Nenhum arquivo-fonte anexado (apenas código no tag Git)
- **Estado de conformidade:** **Correções de avisos prioritárias** — Corrigido para `GPL-3.0-or-later`, porém omite avisos de OpenSSL 3.0.13, Mesa/LLVM e QtSvg, inclui `LicenseRef-Qt-Commercial.txt`, sem tela completa de avisos legais e (a partir de `v0.5.0`) sem `*-fonte.zip`; `v0.5.0`+ mantém `ReactionGIFs`/`Nekos.best`.
- **Assets e SHA-256:**
  - `ANDROID-SHA256SUMS.txt` (90 bytes) — `sha256:a11cb53e84190f63d57cac62a335cbc4ea2ba68219757ff201d52242eef7012b`
  - `Bolha-0.5.1-Android.apk` (60183293 bytes) — `sha256:4bc7773c50d79d00e0cb35428d3f230ae57ea4d582bb5b92ce06730bf6915997`
  - `Bolha-Setup-0.5.1-x64.exe` (34971642 bytes) — `sha256:7077eb325677d8c6fe3df2d55af165c0f829778e362cb33627b2ea8ca1c04712`
  - `latest.yml` (362 bytes) — `sha256:4aaeb673ce2883a66885b8fe3cf991c1a9aa170ef1eb21d4539066e58a33f3f6`
  - `SHA256SUMS.txt` (262 bytes) — `sha256:f17af26e1076165e1096eb76500c7d481a84f9515584eaa9439b4e6dec0c566d`
  - `THIRD-PARTY-NOTICES.txt` (1702 bytes) — `sha256:c3d433e7b1ca78be44ea2829b57122fa8e1cf9af2425662e3d69f64c7e9a122d`

### `v0.5.0` — Bolha 0.5.0

- **Tag → Commit:** `v0.5.0` → `5140599ad270e9b33ef4cdc76b4618e92d40b5c3` (Record local validation for refined expressions)
- **Data (GitHub):** `2026-11-13T13:49:22Z`
- **Workflows no commit:** `.github/workflows/android.yml`, `.github/workflows/windows.yml`
- **Manifestos / Avisos:** `installed-files.json` (interno), `assets/chaquopy/build.json` + `.imy`, `assets/licenses/android/NOTICE.md` | Cabeçalho `THIRD-PARTY-NOTICES.txt`: `Bolha 0.4.4 — componentes redistribuídos`
- **Fontes anexas na release:** Nenhum arquivo-fonte anexado (apenas código no tag Git)
- **Estado de conformidade:** **Correções de avisos prioritárias** — Corrigido para `GPL-3.0-or-later`, porém omite avisos de OpenSSL 3.0.13, Mesa/LLVM e QtSvg, inclui `LicenseRef-Qt-Commercial.txt`, sem tela completa de avisos legais e (a partir de `v0.5.0`) sem `*-fonte.zip`; `v0.5.0`+ mantém `ReactionGIFs`/`Nekos.best`.
- **Assets e SHA-256:**
  - `ANDROID-SHA256SUMS.txt` (90 bytes) — `sha256:d4984dffd5ca452d4eee37b70aa847dcb995453b0460979762c4fb7b90975b5e`
  - `Bolha-0.5.0-Android.apk` (60183385 bytes) — `sha256:7449311cdf9042373e80060e4a5bc2d3434bb5b5f5f66e333c8975901aa68f99`
  - `Bolha-Setup-0.5.0-x64.exe` (34962425 bytes) — `sha256:abead79b8c5f44686766a400cc71129b00aa435b0b4261abb45e0688369caa97`
  - `latest.yml` (362 bytes) — `sha256:073eb69a31d6b461eecc4209c15b331afef5bca605c26f5caa19e33396fca3a0`
  - `SHA256SUMS.txt` (262 bytes) — `sha256:bd3b0315ac144935d7ca9cfb4c898f1fa2462242344032894d4ba7d9d3c784a0`
  - `THIRD-PARTY-NOTICES.txt` (1702 bytes) — `sha256:c3d433e7b1ca78be44ea2829b57122fa8e1cf9af2425662e3d69f64c7e9a122d`

### `v0.4.10` — Bolha 0.4.10

- **Tag → Commit:** `v0.4.10` → `0f08aedb7ad6ae566b5790c42429234ffb4dfca4` (Validate Android overlay, memory and haptics in an emulator)
- **Data (GitHub):** `2026-11-13T03:02:40Z`
- **Workflows no commit:** `.github/workflows/android.yml`, `.github/workflows/windows.yml`
- **Manifestos / Avisos:** `installed-files.json` (interno), `assets/chaquopy/build.json` + `.imy`, `assets/licenses/android/NOTICE.md` | Cabeçalho `THIRD-PARTY-NOTICES.txt`: `Bolha 0.4.4 — componentes redistribuídos`
- **Fontes anexas na release:** `Bolha-0.4.10-Android-Source.zip`
- **Estado de conformidade:** **Correções de avisos prioritárias** — Corrigido para `GPL-3.0-or-later`, porém omite avisos de OpenSSL 3.0.13, Mesa/LLVM e QtSvg, inclui `LicenseRef-Qt-Commercial.txt`, sem tela completa de avisos legais e (a partir de `v0.5.0`) sem `*-fonte.zip`; `v0.5.0`+ mantém `ReactionGIFs`/`Nekos.best`.
- **Assets e SHA-256:**
  - `ANDROID-SHA256SUMS.txt` (189 bytes) — `sha256:5b4d256f92bf29045893f023e8efd7cdbf8c99548b67d8d775ddfb2fb2dfd61c`
  - `Bolha-0.4.10-Android-Source.zip` (1573928 bytes) — `sha256:5af83d77dc897d2322146b61827ef81f0c620317113fe23296d52e1788e19e98`
  - `Bolha-0.4.10-Android.apk` (59888629 bytes) — `sha256:a5910eab7da3eff1dcc486fc5afbe8e59e323e8faf1025398d6f5fd6ec17b017`
  - `Bolha-Setup-0.4.10-x64.exe` (34941127 bytes) — `sha256:3e2a011fd92f16faee98a914bae9b0018452a13fb7460b5bfaa8e73503c223cc`
  - `latest.yml` (365 bytes) — `sha256:37b9d251f02e6be0630fb883d38d36e54cc9ce5d94937b12064169fb45839011`
  - `SHA256SUMS.txt` (263 bytes) — `sha256:436c965ee34ab9d81d762fd1131c467771cbeadd1d88d5eca8eeafbbba4b60d8`
  - `THIRD-PARTY-NOTICES.txt` (1702 bytes) — `sha256:c3d433e7b1ca78be44ea2829b57122fa8e1cf9af2425662e3d69f64c7e9a122d`

### `v0.4.4` — Bolha 0.4.4

- **Tag → Commit:** `v0.4.4` → `3dc42682d38017a4f97e298bf4e16a74f80c0aa1` (Merge pull request #2 from kuky13/bolha/gpl-art)
- **Data (GitHub):** `2026-11-06T14:08:57Z`
- **Workflows no commit:** `.github/workflows/windows.yml`
- **Manifestos / Avisos:** `installed-files.json` (interno) | Cabeçalho `THIRD-PARTY-NOTICES.txt`: `Bolha 0.4.4 — componentes redistribuídos`
- **Fontes anexas na release:** Nenhum arquivo-fonte anexado (apenas código no tag Git)
- **Estado de conformidade:** **Correções de avisos prioritárias** — Corrigido para `GPL-3.0-or-later`, porém omite avisos de OpenSSL 3.0.13, Mesa/LLVM e QtSvg, inclui `LicenseRef-Qt-Commercial.txt`, sem tela completa de avisos legais e (a partir de `v0.5.0`) sem `*-fonte.zip`; `v0.5.0`+ mantém `ReactionGIFs`/`Nekos.best`.
- **Assets e SHA-256:**
  - `Bolha-Setup-0.4.4-x64.exe` (34917701 bytes) — `sha256:4ebb9a7b39fc7766605f4e30aad23f21bd4d65a58f225a08df6eee81778f0049`
  - `latest.yml` (362 bytes) — `sha256:522f71349e389b7a878aacbbc56dc0b27da4327d4185b5faabad227f1502d019`
  - `SHA256SUMS.txt` (262 bytes) — `sha256:27a0c1213e5c756d5ed8233c62ea8353fcc1b7a0dff1361824e1ab3371f05521`
  - `THIRD-PARTY-NOTICES.txt` (1702 bytes) — `sha256:c3d433e7b1ca78be44ea2829b57122fa8e1cf9af2425662e3d69f64c7e9a122d`

### `v0.4.3` — Bolha 0.4.3

- **Tag → Commit:** `v0.4.3` → `fc469d23af6755e4b0e999500a7e1aa52dc4411a` (Compare only the Bolha entry in the shared startup registry key)
- **Data (GitHub):** `2026-11-06T01:14:40Z`
- **Workflows no commit:** `.github/workflows/windows.yml`
- **Manifestos / Avisos:** `installed-files.json` (interno), `CC-BY-NC-4.0.txt` (interno) | Cabeçalho `THIRD-PARTY-NOTICES.txt`: `Bolha 0.3 — componentes redistribuídos`
- **Fontes anexas na release:** Nenhum arquivo-fonte anexado (apenas código no tag Git)
- **Estado de conformidade:** **Revisão histórica** — `THIRD-PARTY-NOTICES.txt` declara `GPL-3.0-only` + artes `CC BY-NC 4.0` (`CC-BY-NC-4.0.txt` no `.exe`); sem avisos de OpenSSL 3.0.13 / Mesa 11.2.2 / QtSvg.
- **Assets e SHA-256:**
  - `Bolha-Setup-0.4.3-x64.exe` (34920611 bytes) — `sha256:8c51cad35d822debb06e4d6db1f381358d3cbba463d7d1433529fc1aadeadbcb`
  - `latest.yml` (362 bytes) — `sha256:0c140892d3820be72e451a0669aa462c4eb6610b4086cc47207c3a87fea45a4e`
  - `public-feed-validation.json` (338 bytes) — `sha256:efb4627ede4fa77c76b511c95c468113605cdc8b20cd24ad86f6f457f4e35e4c`
  - `SHA256SUMS.txt` (262 bytes) — `sha256:b8db4196d1945d65be239283223a3cf62a568a556b5d85e593875ed3284d6725`
  - `THIRD-PARTY-NOTICES.txt` (1661 bytes) — `sha256:7925a0bb5df9b59347a4c753af020f037465854ff474659f181c36cfb69de166`
  - `VALIDACAO-WINDOWS-0.1.0-para-0.4.3.json` (1856 bytes) — `sha256:6ca6661261c572336f4a72ddab4744d9625210695cb6211f1a4560e19d00b2fc`
  - `VALIDACAO-WINDOWS-0.2.1-para-0.4.3.json` (1853 bytes) — `sha256:50058e77049aa14df4086698cd9e4397c6082cb2d7a8a367739e2942cc624842`
  - `VALIDACAO-WINDOWS-0.4.2-para-0.4.3.json` (5213 bytes) — `sha256:3b383bfeb956043c7c510396a7bf2abcf3eddba4c9b9128a9b9be6a7646f0386`

### `v0.4.2` — Bolha 0.4.2

- **Tag → Commit:** `v0.4.2` → `7890791701d32b0c6c0e19517500758b90b70467` (Keep the simulated fullscreen state through the ping-pong tick)
- **Data (GitHub):** `2026-11-05T23:37:07Z`
- **Workflows no commit:** `.github/workflows/windows.yml`
- **Manifestos / Avisos:** `PROVENIENCIA.json`, `installed-files.json` (interno), `CC-BY-NC-4.0.txt` (interno) | Cabeçalho `THIRD-PARTY-NOTICES.txt`: `Bolha 0.3 — componentes redistribuídos`
- **Fontes anexas na release:** `Bolha-0.4.2-fonte.zip`
- **Estado de conformidade:** **Revisão histórica** — `THIRD-PARTY-NOTICES.txt` declara `GPL-3.0-only` + artes `CC BY-NC 4.0` (`CC-BY-NC-4.0.txt` no `.exe`); sem avisos de OpenSSL 3.0.13 / Mesa 11.2.2 / QtSvg.
- **Assets e SHA-256:**
  - `Bolha-0.4.2-fonte.zip` (822963 bytes) — `sha256:511f198fc992b71bcf2e7ea565723a6463e9e7969ae30bb8e1917725c186ee18`
  - `Bolha-Setup-0.4.2-x64.exe` (34910449 bytes) — `sha256:39147b47480f0e0fba6006b359e2c353de07f9b900131341581a937ac6249caf`
  - `FONTE-SHA256SUMS.txt` (88 bytes) — `sha256:85ca12ecf177da3daff3100a37e2fd95d8812d4c74fc3708c3b71b4db1bde628`
  - `latest.yml` (362 bytes) — `sha256:3b1ce9cb00abfcf19f2662ccbe04a19fc6e45f16a1b9a4ac242126520d0ad62a`
  - `PROVENIENCIA.json` (970 bytes) — `sha256:a3a48dd77a65f355c00a00befc552cc43bfc4907f4cefc4468821541fa40184b`
  - `public-feed-validation.json` (235 bytes) — `sha256:6b2d689106c43f086d971f678956102cfa1452eeb5e80b4fc893ab7e4e5a0d4a`
  - `SHA256SUMS.txt` (262 bytes) — `sha256:e299d7dab635af47b1f904c74d92e67d3a70d4de98e341580863a6fd75335fb7`
  - `THIRD-PARTY-NOTICES.txt` (1661 bytes) — `sha256:7925a0bb5df9b59347a4c753af020f037465854ff474659f181c36cfb69de166`
  - `VALIDACAO.md` (1700 bytes) — `sha256:cd4b8217d44b2d1c3eea7eb89650eb211842eb6dc881b627f65039f0c8683fd4`
  - `windows-native-report.json` (5217 bytes) — `sha256:39361cf961cabfd6e4b33d822e94ac1f3afef9764244baf08b00a2d4f1f75920`

### `v0.4.1` — Bolha 0.4.1

- **Tag → Commit:** `v0.4.1` → `ddbe8d47da6aadde9b16efe1b3c2ecd44b1d86c1` (Animate clearer anger marks and sparks)
- **Data (GitHub):** `2026-11-05T19:56:32Z`
- **Workflows no commit:** `.github/workflows/windows.yml`
- **Manifestos / Avisos:** `PROVENIENCIA.json`, `installed-files.json` (interno), `CC-BY-NC-4.0.txt` (interno) | Cabeçalho `THIRD-PARTY-NOTICES.txt`: `Bolha 0.3 — componentes redistribuídos`
- **Fontes anexas na release:** `Bolha-0.4.1-fonte.zip`
- **Estado de conformidade:** **Revisão histórica** — `THIRD-PARTY-NOTICES.txt` declara `GPL-3.0-only` + artes `CC BY-NC 4.0` (`CC-BY-NC-4.0.txt` no `.exe`); sem avisos de OpenSSL 3.0.13 / Mesa 11.2.2 / QtSvg.
- **Assets e SHA-256:**
  - `Bolha-0.4.1-fonte.zip` (805114 bytes) — `sha256:af34039576f6568437173d4a20e8060f69e1f5b4bc459fd8707268d19f8e73ad`
  - `Bolha-Setup-0.4.1-x64.exe` (34876901 bytes) — `sha256:f5fa8b5bbbd0d66190bb6199d956f9878d6bac0e0148b136faf18766e5fd7cad`
  - `FONTE-SHA256SUMS.txt` (88 bytes) — `sha256:ad3a31501a903f4a2d048780b98aa46f1a3ba9b10ff0f7169a8782b3699097e8`
  - `latest.yml` (362 bytes) — `sha256:662d7959eaeeab52d8e9810a381dd4750399ffbd57cfc2e0677312f7cdf7c3df`
  - `PROVENIENCIA.json` (1138 bytes) — `sha256:23ee21388f60a6951e4201535bb5a0bdc3d8012c5ae09350621be374b98866da`
  - `SHA256SUMS.txt` (262 bytes) — `sha256:263042f2eec047dc024d3bf977cc4f6b248cef7de8f38100df169492d6ea56c9`
  - `THIRD-PARTY-NOTICES.txt` (1661 bytes) — `sha256:7925a0bb5df9b59347a4c753af020f037465854ff474659f181c36cfb69de166`
  - `VALIDACAO.md` (1530 bytes) — `sha256:9b2635a80673fedae48848779ec317e3bc7e5fcd8d42ebd8fb46b0e1b9081f48`

### `v0.4.0` — Bolha 0.4.0

- **Tag → Commit:** `v0.4.0` → `fb64b2f4660749a483e84a1952eb1f1f47c6b68f` (Fix scene import in the packaged Windows app)
- **Data (GitHub):** `2026-11-05T19:04:56Z`
- **Workflows no commit:** `.github/workflows/windows.yml`
- **Manifestos / Avisos:** `PROVENIENCIA.json`, `installed-files.json` (interno), `CC-BY-NC-4.0.txt` (interno) | Cabeçalho `THIRD-PARTY-NOTICES.txt`: `Bolha 0.3 — componentes redistribuídos`
- **Fontes anexas na release:** `Bolha-0.4.0-fonte.zip`
- **Estado de conformidade:** **Revisão histórica** — `THIRD-PARTY-NOTICES.txt` declara `GPL-3.0-only` + artes `CC BY-NC 4.0` (`CC-BY-NC-4.0.txt` no `.exe`); sem avisos de OpenSSL 3.0.13 / Mesa 11.2.2 / QtSvg.
- **Assets e SHA-256:**
  - `Bolha-0.4.0-fonte.zip` (800171 bytes) — `sha256:a3fa47a481818bd2233c6908bc9ed34577ff41f9d81347aaa3f788ccf6ee372a`
  - `Bolha-Setup-0.4.0-x64.exe` (34866758 bytes) — `sha256:784cc68dc40ca22a7e2dfb7f359fb7ec6f8ce56befe48402f8fa8bf6314b3763`
  - `FONTE-SHA256SUMS.txt` (88 bytes) — `sha256:d1bb034056d02fa21195626c85952e19982d42f27d2bf2e7cba2911e2e27c346`
  - `latest.yml` (362 bytes) — `sha256:b69776038cc7cfe175845b6f3f94b1e1293affc7c6ee206be35d7ef5f59435a7`
  - `PROVENIENCIA.json` (1113 bytes) — `sha256:8196be20a0d134baa2e6b03f8a47887cab2689aa3a5b168d45fba2a569150e39`
  - `SHA256SUMS.txt` (262 bytes) — `sha256:80e40f3aa11c56d4634e272e515cc25bf6ac4283723453e2d1f89c90ba114e46`
  - `THIRD-PARTY-NOTICES.txt` (1661 bytes) — `sha256:7925a0bb5df9b59347a4c753af020f037465854ff474659f181c36cfb69de166`
  - `VALIDACAO.md` (4189 bytes) — `sha256:6d75e73d849fffa79f07bd1422d3729f82aee9d9a1df2ee534cc6a28f6e794e8`

### `v0.3.3` — Bolha 0.3.3

- **Tag → Commit:** `v0.3.3` → `37a8fcabb98919314e1259c9720493d261dff238` (feat: add red anger, attached effects, toy cursor push, and RAM online reactions (0.3.3))
- **Data (GitHub):** `2026-11-04T16:54:31Z`
- **Workflows no commit:** `.github/workflows/windows.yml`
- **Manifestos / Avisos:** `PROVENIENCIA.json`, `installed-files.json` (interno), `CC-BY-NC-4.0.txt` (interno) | Cabeçalho `THIRD-PARTY-NOTICES.txt`: `Bolha 0.3 — componentes redistribuídos`
- **Fontes anexas na release:** `Bolha-0.3.3-fonte.zip`
- **Estado de conformidade:** **Revisão histórica** — `THIRD-PARTY-NOTICES.txt` declara `GPL-3.0-only` + artes `CC BY-NC 4.0` (`CC-BY-NC-4.0.txt` no `.exe`); sem avisos de OpenSSL 3.0.13 / Mesa 11.2.2 / QtSvg.
- **Assets e SHA-256:**
  - `Bolha-0.3.3-fonte.zip` (776805 bytes) — `sha256:dcf7845bc5e0a02d098c69939f273c15938ba2b4eae9ba8704fc156f8f566b05`
  - `Bolha-Setup-0.3.3-x64.exe` (34821370 bytes) — `sha256:4d79acc0542ae92ce8a29fd1cf0449a76d978a5e24fbbe53004a3606ef7bb94d`
  - `FONTE-SHA256SUMS.txt` (88 bytes) — `sha256:3eeb017695377cd8704e22df5a34bb27207d7eeeb6d4e775fea834e14535e879`
  - `latest.yml` (362 bytes) — `sha256:490b80497d21d7c754efe8b8c1b47c8ff77cabfcc362ff7d580b15766f5ba18c`
  - `PROVENIENCIA.json` (801 bytes) — `sha256:62ea521910cc48e2e968cf5e5f99a7551dd8b5fef70629916879bd15288fa52b`
  - `SHA256SUMS.txt` (262 bytes) — `sha256:0f72dd49e556cd9940a31df021f0b4563cdc0a2fc4f80606a5432cbd4cc0ab15`
  - `THIRD-PARTY-NOTICES.txt` (1661 bytes) — `sha256:7925a0bb5df9b59347a4c753af020f037465854ff474659f181c36cfb69de166`
  - `VALIDACAO.md` (12581 bytes) — `sha256:cda1bc0c3b768e2ae30f0fe34f553f820041d24ecf9617a876cb009cad459c9c`

### `v0.3.0` — Bolha 0.3.0

- **Tag → Commit:** `v0.3.0` → `dba6e185a562eebf13226b0d618b54017b29c88d` (fix: preserve legacy learning and require active runtime before update confirmation)
- **Data (GitHub):** `2026-11-04T01:38:36Z`
- **Workflows no commit:** `.github/workflows/windows.yml`
- **Manifestos / Avisos:** `installed-files.json` (interno), `CC-BY-NC-4.0.txt` (interno) | Cabeçalho `THIRD-PARTY-NOTICES.txt`: `Bolha 0.3 — componentes redistribuídos`
- **Fontes anexas na release:** Nenhum arquivo-fonte anexado (apenas código no tag Git)
- **Estado de conformidade:** **Revisão histórica** — `THIRD-PARTY-NOTICES.txt` declara `GPL-3.0-only` + artes `CC BY-NC 4.0` (`CC-BY-NC-4.0.txt` no `.exe`); sem avisos de OpenSSL 3.0.13 / Mesa 11.2.2 / QtSvg.
- **Assets e SHA-256:**
  - `Bolha-Setup-0.3.0-x64.exe` (34757375 bytes) — `sha256:ec875b94f1c750028b7c221307930acc1b4f3bd83445442ca203a37948e3d96c`
  - `latest.yml` (362 bytes) — `sha256:639f60038bed7285ecb4e07f464f88468266b8d7b87f6f2ded01063f30f7175e`
  - `SHA256SUMS.txt` (262 bytes) — `sha256:47ca617e40b4309b5e0312b5c2416f0ba7688c378301636c046a6a6c8dd3de69`
  - `THIRD-PARTY-NOTICES.txt` (1661 bytes) — `sha256:7925a0bb5df9b59347a4c753af020f037465854ff474659f181c36cfb69de166`

### `v0.2.1` — Bolha v0.2.1

- **Tag → Commit:** `v0.2.1` → `8d6708574ebe636b9ecce58e50dc89342a7ea4a4` (Avoid repeating neural payloads between animation frames [skip ci])
- **Data (GitHub):** `2026-11-03T22:54:58Z`
- **Workflows no commit:** `.github/workflows/windows.yml`
- **Manifestos / Avisos:** Nenhum | Cabeçalho `THIRD-PARTY-NOTICES.txt`: `Ausente na release`
- **Fontes anexas na release:** Nenhum arquivo-fonte anexado (apenas código no tag Git)
- **Estado de conformidade:** **Revisão histórica** — `CC-BY-NC-4.0` (`BOLHA-ASSETS.md`) e `GPL-3.0-only` no `package.json`; sem fonte anexa.
- **Assets e SHA-256:**
  - `ATUALIZACAO-BOLHA-0.2.1.md` (4359 bytes) — `sha256:44c4e45c84419929ec6dd2f1dca3053c8e232219315ebf28f7c26b8c646678c9`
  - `Bolha-Setup-0.2.1-x64.exe` (152983319 bytes) — `sha256:20078a4cda5d563b6ebac461103cf8a2a2f1b26589cb36dea41b26a8243d16a4`
  - `Bolha-Setup-0.2.1-x64.exe.blockmap` (160958 bytes) — `sha256:d6e36fa6e552a43936327dd5d124cf7dfd939672b6e3ea55d5724b71ae9b95a0`
  - `latest.yml` (347 bytes) — `sha256:a5477d637bf79fbb0c80c1744bbfae67beab7fe9bc30ed10ab1a76ce420c8b3f`
  - `SHA256SUMS.txt` (273 bytes) — `sha256:0c720b2992fe61bac005b861195e746e47ae1143b7c4736de55f3f8942bd0d61`

### `v0.1.1` — Bolha v0.1.1

- **Tag → Commit:** `v0.1.1` → `48f5da2d6baebee71179deb1322f5b8ada591288` (Fix frozen brain Unicode output on Windows and verify caress regression)
- **Data (GitHub):** `2026-11-03T21:23:23Z`
- **Workflows no commit:** `.github/workflows/windows.yml`
- **Manifestos / Avisos:** Nenhum | Cabeçalho `THIRD-PARTY-NOTICES.txt`: `Ausente na release`
- **Fontes anexas na release:** Nenhum arquivo-fonte anexado (apenas código no tag Git)
- **Estado de conformidade:** **Revisão histórica** — `DRIPPY-ASSETS.md`, 412 ocorrências `drippy` no `app.asar`, `CC-BY-NC-4.0` e `GPL-3.0-only`.
- **Assets e SHA-256:**
  - `Bolha-Setup-0.1.1-x64.exe` (152980208 bytes) — `sha256:f33ce74273e4d5619644f061952df9793740e214425966bba7055f321b7b014c`
  - `Bolha-Setup-0.1.1-x64.exe.blockmap` (160899 bytes) — `sha256:995eaea968bfcf23e89ed33e9473ad06d926a6af6619556f397a5de0e98296dd`
  - `CORRECAO-BOLHA-0.1.1.md` (2180 bytes) — `sha256:e7c35399d2d632c74b0a931f0e7adbb6342c03c0a5deab8f53b880f052f9fe05`
  - `latest.yml` (347 bytes) — `sha256:f29a52a45b928cbc1e7db8488d76732146f334b605572fbde662782d349794dc`
  - `SHA256SUMS.txt` (273 bytes) — `sha256:67821f94153f2648d9e4af284a0e16e66501d98071309dfe401a6a72c0d1fc99`

### `v0.1.0` — Bolha v0.1.0

- **Tag → Commit:** `v0.1.0` → `9f71e54d7c5acf4abef76b3e4ab319de4f0a978f` (Document measured resource use and validation boundaries)
- **Data (GitHub):** `2026-11-03T20:42:38Z`
- **Workflows no commit:** `.github/workflows/windows.yml`
- **Manifestos / Avisos:** `AUDITORIA-PACOTE.json` | Cabeçalho `THIRD-PARTY-NOTICES.txt`: `Ausente na release`
- **Fontes anexas na release:** Nenhum arquivo-fonte anexado (apenas código no tag Git)
- **Estado de conformidade:** **Revisão histórica** — `DRIPPY-ASSETS.md`, 412 ocorrências `drippy` no `app.asar`, `CC-BY-NC-4.0` e `GPL-3.0-only`.
- **Assets e SHA-256:**
  - `AUDITORIA-PACOTE.json` (164 bytes) — `sha256:082bccfa7f5ee702eb65d642dde4ca2c517041ace1fc2aaae1368cbde11151c2`
  - `Bolha-Setup-0.1.0-x64.exe` (152982014 bytes) — `sha256:f7cbd370555ed81d9bcc3fb949c1a7091e61433299c65c0958ca97cf09dc8599`
  - `Bolha-Setup-0.1.0-x64.exe.blockmap` (160795 bytes) — `sha256:a928d69df82c2a11a61c55aa1ed57fa1484266dc351f9529582c2e2afaf64855`
  - `DESEMPENHO-LINUX.json` (2175 bytes) — `sha256:da5838bbcbd3497d1380a7f8b469938fe1a465548607b7176092b5fad620e1bf`
  - `DESEMPENHO-WINDOWS.json` (2125 bytes) — `sha256:d953333a1182f4a9f3a278326a3e4feaafe41d608d9bf72c70d81a7bf2948dca`
  - `INTELIGENCIA-BOLHA.md` (5343 bytes) — `sha256:c7e46164c3219e61d9380be461f4ce1ae7a7d235724f1f44d7b86b9fe7e2aecc`
  - `latest.yml` (347 bytes) — `sha256:a2dc44e16917fb270776b7703dc1244fa6a335c03af87c1d9f1718e977a4c2d6`
  - `RELATORIO-BOLHA.md` (5174 bytes) — `sha256:3a369aed02d7839c37f4e7873ddf1bb892b7b2413339c0ec5313fa6345f15011`
  - `SHA256SUMS.txt` (273 bytes) — `sha256:88b8f815306da89bd5ca6241bc20ea4be80287b79f4a5d47872b171120a665e4`

---

## Branch Não Publicado: `origin/feat/bolha-support-0594` (`ce28e6e`)

- **Commit:** `ce28e6e1b2ffd3429384a4b4155666b7b95b8436` (2026-11-23T01:21:16Z)
- **Escopo observado (`git show ce28e6e`):** 8 arquivos (`bolha/reports.py`, `android/app/src/main/java/solutions/kuky/bolha/mobile/ReportActivity.java`, `service/Dockerfile`, `service/README.md`, `service/compose.yml`, `service/compose.proxy.yml`, `service/report_gateway.py`, `service/test_report_gateway.py`), atualizando o endpoint de relatos para `https://api.kuky.solutions/bolha/v1/reports`.
- **Commits adicionais sobre `main` nesse branch (`main..origin/feat/bolha-support-0594`):** 10 commits (`17b163e` até `ce28e6e`), incluindo primeiros passos, melhorias no instalador e painel de bateria ao vivo, formulário de relatos e detecção de atualização no Android.
- **Escopo da candidata de conformidade:** a referência `ce28e6e` é histórica. A situação da próxima candidata depende do conteúdo do commit e de seus artefatos finais. Veja [o procedimento de publicação](RELEASE-COMPLIANCE.md).

## Antes de alterar uma release antiga

1. De v0.1.0 a v0.4.3, esclarecer direitos comerciais das artes e conservar os avisos herdados enquanto se revisa a procedência de cada recurso. A opção GPLv3 permite combinar material GPL-3.0-or-later com GPL-3.0-only, observadas as condições da licença. Confirmar se os avisos históricos refletiam corretamente os arquivos sob CC BY-NC e se as artes formam agregado ou parte do trabalho combinado.
2. Os instaladores v0.1.0 e v0.1.1 incluem um aviso com nomenclatura antiga da personagem. As ocorrências de texto no ASAR não demonstram inclusão de guias privados. Conferir nomes, arquivos, hashes e origem antes de propor medida de retirada. Veja o [inventário de procedência](INVENTARIO-PROCEDENCIA.md).
3. Para v0.4.4 e posteriores, priorizar um suplemento versionado dos avisos, das licenças e da fonte correspondente onde houver lacunas verificáveis. Os builds de regressão do atualizador usam SHA-256 fixo de binários legados. Conservar tags e binários, e submeter qualquer alteração na publicação à aprovação específica do mantenedor. [GNU GPLv3](https://www.gnu.org/licenses/gpl-3.0.html).
