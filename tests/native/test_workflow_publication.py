# SPDX-License-Identifier: GPL-3.0-or-later
# Bolha is based on Pestinha by @mille-okws and contributors; see NOTICE.md.
"""Executa o passo PowerShell real com GitHub/CLI simulados: nunca publica nada."""
import json
from pathlib import Path
import re
import shutil
import subprocess
import textwrap
import pytest

ROOT=Path(__file__).resolve().parents[2]
WORKFLOW=ROOT/'.github/workflows/windows.yml'
SHA='a'*40


def publication_code():
    final=WORKFLOW.read_text(encoding='utf-8').rsplit('      - name: Publicar a versão validada\n',1)[1]
    return textwrap.dedent(final.split('        run: |\n',1)[1])


def harness(case):
    return r'''
$case = '__CASE__' | ConvertFrom-Json
$env:BOLHA_VERSION='0.3.0'
$env:GITHUB_SHA='aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'
$env:GITHUB_REPOSITORY='kuky13/bolha'
$env:GITHUB_EVENT_NAME=$case.Event
$env:GITHUB_REF_TYPE=$case.RefType
$env:GITHUB_REF_NAME=$case.RefName
$env:BOLHA_PUBLISH_RELEASE=$case.Publish
$script:Created=$null
function python { $global:LASTEXITCODE=0; return $case.CodeVersion }
function git { $global:LASTEXITCODE=0; return $case.LocalSha }
function gh {
  $global:LASTEXITCODE=0
  if ($args[0] -eq 'api') {
    $global:LASTEXITCODE=$case.ApiExit
    if ($args -contains '--paginate') { return $case.ReleaseTags }
    if ($args[1] -like '*matching-refs*') { return $case.Refs }
    return $case.RemoteSha
  }
  if ($args[0] -eq 'release' -and $args[1] -eq 'create') {
    $script:Created=@($args)
    $global:LASTEXITCODE=$case.CreateExit
    return
  }
  throw 'Comando GitHub inesperado.'
}
$failed=$false
try { & { __PUBLISH_CODE__ } } catch { $failed=$true }
if ($failed -ne $case.MustFail) { throw "Falha esperada=$($case.MustFail), recebida=$failed" }
if (($null -ne $script:Created) -ne $case.MustCreate) { throw 'Publicação chamada indevidamente ou ausente.' }
if ($script:Created) {
  if ($script:Created[2] -ne 'v0.3.0') { throw 'Tag errada.' }
  $target=[array]::IndexOf($script:Created, '--target')
  if ($target -lt 0 -or $script:Created[$target+1] -ne $env:GITHUB_SHA) { throw 'Alvo não corresponde ao SHA compilado.' }
  if ($script:Created -contains '--clobber') { throw 'Sobrescrita proibida.' }
}
'''.replace('__CASE__',json.dumps(case).replace("'","''")).replace('__PUBLISH_CODE__',publication_code())


def cases():
    base=dict(Event='workflow_dispatch',RefType='branch',RefName='native/qt-0.3',Publish='true',
              CodeVersion='0.3.0',LocalSha=SHA,RemoteSha=SHA,ApiExit=0,CreateExit=0,Refs='[]',
              MustFail=False,MustCreate=True,ReleaseTags='')
    edits=[{},dict(Refs='[{"ref":"refs/tags/v0.3.0-next"}]'),
           dict(Refs='[{"ref":"refs/tags/v0.3.0"}]',MustFail=True,MustCreate=False),
           dict(Publish='false',MustFail=True,MustCreate=False),
           dict(LocalSha='b'*40,MustFail=True,MustCreate=False),
           dict(CodeVersion='0.3.1',MustFail=True,MustCreate=False),
           dict(ApiExit=1,MustFail=True,MustCreate=False),
           dict(Event='push',RefType='tag',RefName='v0.3.0'),
           dict(Event='push',RefType='tag',RefName='v0.3.0',RemoteSha='b'*40,MustFail=True,MustCreate=False),
           dict(ReleaseTags='v0.3.0',MustFail=True,MustCreate=False),
           dict(CreateExit=1,MustFail=True)]
    return [dict(base,**edit) for edit in edits]


def test_workflow_publication_is_opt_in_and_requires_success_and_legacy_tests():
    source=WORKFLOW.read_text(encoding='utf-8')
    assert re.search(r'publish_release:\n(?:.*\n){0,4}?\s+default: false\n',source)
    assert "if: success() && (github.ref_type == 'tag' || inputs.publish_release)" in source
    assert source.count("if: github.ref_type == 'tag' || inputs.legacy_validation || inputs.publish_release")==3
    assert 'GH_TOKEN: ${{ github.token }}' in source
    assert '--target $env:GITHUB_SHA' in publication_code()
    assert '--clobber' not in publication_code()


@pytest.mark.parametrize('case',cases())
def test_powershell_publication_guards(case,tmp_path):
    shell=shutil.which('pwsh') or (shutil.which('powershell.exe') if __import__('os').name=='nt' else None)
    if not shell:pytest.skip('O teste funcional do passo PowerShell roda no Windows CI.')
    script=tmp_path/'publication-mock.ps1';script.write_text(harness(case),encoding='utf-8-sig')
    result=subprocess.run([shell,'-NoProfile','-NonInteractive','-File',str(script)],capture_output=True,text=True,
                          encoding='utf-8',errors='replace',timeout=30)
    assert result.returncode==0,result.stdout+'\n'+result.stderr
