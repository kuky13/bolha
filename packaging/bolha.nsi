; SPDX-License-Identifier: GPL-3.0-only
Unicode true
RequestExecutionLevel user
SetCompressor /SOLID lzma
!include "MUI2.nsh"
!include "LogicLib.nsh"
!include "FileFunc.nsh"
!include "StrFunc.nsh"
${StrStr}
!ifndef VERSION
!error "Informe VERSION, BUNDLE, OUTPUT e ICON."
!endif
!define APPGUID "efdda9e4-adbf-5481-bf79-1ee5a33cbceb"
Name "Bolha ${VERSION}"
OutFile "${OUTPUT}\Bolha-Setup-${VERSION}-x64.exe"
InstallDir "$LOCALAPPDATA\Programs\Bolha"
Icon "${ICON}"
UninstallIcon "${ICON}"
ShowInstDetails show
ShowUninstDetails show
BrandingText "Bolha — companhia local"
!define MUI_ABORTWARNING
!define MUI_FINISHPAGE_RUN
!define MUI_FINISHPAGE_RUN_FUNCTION FinishOpenBolha
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "..\LICENSE"
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_LANGUAGE "PortugueseBR"
Var TestMode
Var RegistryGuid
Var DataRoot
Var Stage
Var Backup
Var OldExists
Var ForceRun
Var ProcessHandle
Var NewPID
Var Opened
Var Transaction
Var Recognized
Var SectionSucceeded
Var PreviousVersion
Var PreviousUninstall
Var PreviousQuietUninstall
Var PreviousIcon

Function .onInit
  SetRegView 64
  SetShellVarContext current
  StrCpy $RegistryGuid "${APPGUID}"
  StrCpy $TestMode "0"
  StrCpy $Opened "0"
  StrCpy $SectionSucceeded "0"
  StrCpy $DataRoot "$APPDATA\bolha"
  ${GetParameters} $0
  ClearErrors
  ${GetOptions} $0 "/TEST" $1
  ${IfNot} ${Errors}
    ReadEnvStr $1 "BOLHA_TEST"
    ${If} $1 != "1"
      Abort "O modo isolado exige BOLHA_TEST=1."
    ${EndIf}
    ReadEnvStr $DataRoot "BOLHA_TEST_USER_DATA"
    ReadEnvStr $INSTDIR "BOLHA_TEST_INSTALL_DIR"
    ${If} $DataRoot == ""
    ${OrIf} $INSTDIR == ""
      Abort "Defina as pastas isoladas de dados e instalação."
    ${EndIf}
    StrCpy $TestMode "1"
    StrCpy $RegistryGuid "${APPGUID}-validation"
  ${Else}
    ; Mesmas chaves do electron-builder 26.18.0, incluindo instalações em pasta própria.
    ReadRegStr $1 HKCU "Software\${APPGUID}" "InstallLocation"
    ${If} $1 != ""
      StrCpy $INSTDIR $1
    ${EndIf}
  ${EndIf}
  StrCpy $ForceRun "0"
  ClearErrors
  ${GetOptions} $0 "--force-run" $1
  ${IfNot} ${Errors}
    StrCpy $ForceRun "1"
  ${EndIf}
FunctionEnd

Function CheckNativeMarker
  ; Entrada $0=pasta; saída $Recognized=1 sópara o marcador exato deste produto.
  StrCpy $Recognized "0"
  ClearErrors
  FileOpen $1 "$0\bolha-native-installation.flag" r
  ${IfNot} ${Errors}
    FileRead $1 $2
    FileClose $1
    ${If} $2 == "bolha-native:solutions.kuky.bolha"
      StrCpy $Recognized "1"
    ${EndIf}
  ${EndIf}
FunctionEnd

Function .onVerifyInstDir
  GetFullPathName $INSTDIR "$INSTDIR"
  ${GetRoot} "$INSTDIR" $0
  ${If} $INSTDIR == $0
  ${OrIf} $INSTDIR == "$0\"
  ${OrIf} $INSTDIR == "$PROFILE"
  ${OrIf} $INSTDIR == "$DOCUMENTS"
  ${OrIf} $INSTDIR == "$APPDATA"
  ${OrIf} $INSTDIR == "$LOCALAPPDATA"
  ${OrIf} $INSTDIR == "$DESKTOP"
  ${OrIf} $INSTDIR == "$WINDIR"
  ${OrIf} $INSTDIR == "$SYSDIR"
  ${OrIf} $INSTDIR == "$PROGRAMFILES"
  ${OrIf} $INSTDIR == "$PROGRAMFILES64"
  ${OrIf} $INSTDIR == "$COMMONFILES"
  ${OrIf} $INSTDIR == "$COMMONFILES64"
    Abort "Escolha uma pasta exclusiva para a Bolha."
  ${EndIf}
  ; Não atravessa junctions/symlinks em nenhum componente do destino.
  StrCpy $0 "$INSTDIR"
  checkParent:
    System::Call 'kernel32::GetFileAttributesW(w r0)i.r1'
    ${If} $1 != -1
      IntOp $2 $1 & 0x400
      ${If} $2 != 0
        Abort "A pasta de instalação não pode atravessar atalhos ou junctions."
      ${EndIf}
    ${EndIf}
    ${GetParent} "$0" $1
    ${If} $1 != ""
    ${AndIf} $1 != $0
      StrCpy $0 $1
      Goto checkParent
    ${EndIf}
  StrCpy $0 "$INSTDIR"
  Call CheckNativeMarker
  ${If} $TestMode != "1"
    ReadRegStr $0 HKCU "Software\${APPGUID}" "InstallLocation"
    ${If} $0 != ""
      GetFullPathName $0 "$0"
      ${If} $0 == "$INSTDIR"
      ${AndIf} ${FileExists} "$INSTDIR\Bolha.exe"
        StrCpy $Recognized "1"
      ${EndIf}
    ${EndIf}
  ${EndIf}
  ${If} $Recognized != "1"
    ; Pastas novas/vazias são aceitas. Nenhuma pasta de dados arbitrária é movida.
    FindFirst $0 $1 "$INSTDIR\*.*"
    ${DoWhile} $1 != ""
      ${If} $1 != "."
      ${AndIf} $1 != ".."
        FindClose $0
        Abort "A pasta já contém arquivos e não é uma instalação reconhecida da Bolha."
      ${EndIf}
      FindNext $0 $1
    ${Loop}
    FindClose $0
  ${EndIf}
FunctionEnd

Function RecoverInterrupted
  StrCpy $Transaction "$INSTDIR.transaction.ini"
  ReadINIStr $Backup "$Transaction" "recovery" "backup"
  ${If} $Backup == ""
    Return
  ${EndIf}
  GetFullPathName $Backup "$Backup"
  ${GetParent} "$Backup" $0
  ${GetParent} "$INSTDIR" $1
  ${StrStr} $2 $Backup "$INSTDIR.rollback-"
  ${If} $0 != $1
  ${OrIf} $2 != "$Backup"
    Abort "Registro de recuperação inválido. Nenhuma pasta foi alterada."
  ${EndIf}
  System::Call 'kernel32::GetFileAttributesW(w "$Backup")i.r0'
  IntOp $0 $0 & 0x400
  ${If} $0 != 0
    Abort "A recuperação não pode atravessar junctions."
  ${EndIf}
  ; Se houve queda entre as duas renomeações, recupera a versão anterior antes de continuar.
  ${IfNot} ${FileExists} "$INSTDIR\Bolha.exe"
    ${If} ${FileExists} "$Backup\Bolha.exe"
      StrCpy $0 "$Backup"
      Call CheckNativeMarker
      ${If} $TestMode != "1"
        ReadRegStr $0 HKCU "Software\${APPGUID}" "InstallLocation"
        ${If} $0 != ""
          GetFullPathName $0 "$0"
          ${If} $0 == "$INSTDIR"
            StrCpy $Recognized "1"
          ${EndIf}
        ${EndIf}
      ${EndIf}
      ${If} $Recognized != "1"
        Abort "A recuperação exige uma instalação anterior reconhecida."
      ${EndIf}
      RMDir "$INSTDIR"
      ClearErrors
      Rename "$Backup" "$INSTDIR"
      ${If} ${Errors}
        Abort "A instalação anterior está preservada no backup, mas não foi possível restaurá-la."
      ${EndIf}
      Delete "$Transaction"
    ${EndIf}
  ${EndIf}
FunctionEnd

Section "Bolha" SEC_MAIN
  ReadRegStr $PreviousVersion HKCU "Software\$RegistryGuid" "InstallVersion"
  ReadRegStr $PreviousVersion HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\$RegistryGuid" "DisplayVersion"
  ReadRegStr $PreviousUninstall HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\$RegistryGuid" "UninstallString"
  ReadRegStr $PreviousQuietUninstall HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\$RegistryGuid" "QuietUninstallString"
  ReadRegStr $PreviousIcon HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\$RegistryGuid" "DisplayIcon"
  Call .onVerifyInstDir
  Call RecoverInterrupted
  Call .onVerifyInstDir
  System::Call 'kernel32::GetCurrentProcessId() i.r0'
  System::Call 'kernel32::GetTickCount() i.r1'
  StrCpy $Stage "$INSTDIR.stage-$0-$1"
  StrCpy $Backup "$INSTDIR.rollback-$0-$1"
  StrCpy $Transaction "$INSTDIR.transaction.ini"
  ; Uma instalação interrompida antes da extração não toca a versão anterior.
  ClearErrors
  SetOutPath "$Stage"
  File /r "${BUNDLE}\*.*"
  ${If} ${Errors}
    RMDir /r "$Stage"
    Abort "Não foi possível preparar os arquivos. A instalação anterior foi preservada."
  ${EndIf}
  FileOpen $0 "$Transaction" w
  FileWriteWord $0 0xFEFF
  FileClose $0
  WriteINIStr "$Transaction" "recovery" "backup" "$Backup"
  WriteINIStr "$Transaction" "recovery" "version" "${VERSION}"
  WriteINIStr "$Transaction" "recovery" "state" "active"
  StrCpy $OldExists "0"
  ${If} ${FileExists} "$INSTDIR\Bolha.exe"
    StrCpy $OldExists "1"
    ; Espera o processo que solicitou a atualização fechar, sem matar aplicativos existentes.
    StrCpy $2 0
    waitOld:
      ClearErrors
      FileOpen $3 "$INSTDIR\Bolha.exe" a
      ${If} ${Errors}
        IntOp $2 $2 + 1
        ${If} $2 < 120
          Sleep 500
          Goto waitOld
        ${EndIf}
        RMDir /r "$Stage"
        Delete "$Transaction"
        Abort "Feche a Bolha e tente novamente. A versão anterior foi preservada."
      ${EndIf}
      FileClose $3
  ${EndIf}
  SetOutPath "$TEMP"
  ; Troca no mesmo volume: o pacote anterior inteiro fica disponível para recuperação.
  ${If} ${FileExists} "$INSTDIR\*.*"
    ClearErrors
    Rename "$INSTDIR" "$Backup"
    ${If} ${Errors}
      RMDir /r "$Stage"
      Abort "Não consegui guardar a instalação anterior. Nenhum arquivo foi substituído."
    ${EndIf}
  ${EndIf}
  RMDir "$INSTDIR" ; Não recursivo: permite destino previamente vazio.
  ClearErrors
  Rename "$Stage" "$INSTDIR"
  ${If} ${Errors}
    Rename "$Backup" "$INSTDIR"
    Abort "A substituição falhou; a versão anterior foi recuperada."
  ${EndIf}
  SetOutPath "$INSTDIR"
  WriteUninstaller "$INSTDIR\Uninstall Bolha.exe"
  FileOpen $0 "$INSTDIR\bolha-native-installation.flag" w
  FileWrite $0 "bolha-native:solutions.kuky.bolha"
  FileClose $0
  ${If} $TestMode == "1"
    FileOpen $0 "$INSTDIR\bolha-test-install.flag" w
    FileWrite $0 "isolated"
    FileClose $0
  ${EndIf}
  ${If} $ForceRun == "1"
    Call OpenBolha
    ${If} $Opened != "1"
      Call Rollback
      Abort "A nova versão não confirmou a abertura. A instalação anterior foi recuperada."
    ${EndIf}
  ${EndIf}
  ; Só registra a instalação nova após a confirmação, quando ela foi solicitada.
  ${If} $TestMode != "1"
  WriteRegStr HKCU "Software\$RegistryGuid" "InstallLocation" "$INSTDIR"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\$RegistryGuid" "DisplayName" "Bolha"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\$RegistryGuid" "DisplayVersion" "${VERSION}"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\$RegistryGuid" "DisplayIcon" "$INSTDIR\Bolha.exe"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\$RegistryGuid" "UninstallString" '$\"$INSTDIR\Uninstall Bolha.exe$\"'
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\$RegistryGuid" "QuietUninstallString" '$\"$INSTDIR\Uninstall Bolha.exe$\" /S'
  WriteRegDWORD HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\$RegistryGuid" "NoModify" 1
  WriteRegDWORD HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\$RegistryGuid" "NoRepair" 1
    CreateShortcut "$SMPROGRAMS\Bolha.lnk" "$INSTDIR\Bolha.exe"
  ${EndIf}
  ; Não escreve a chave Run. Uma preferência existente continua apontando para Bolha.exe.
  StrCpy $SectionSucceeded "1"
  ${If} ${Silent}
    WriteINIStr "$Transaction" "recovery" "state" "committed"
  ${Else}
    WriteINIStr "$Transaction" "recovery" "state" "installed"
  ${EndIf}
  ; O aplicativo sólimpa backup depois do ack do instalador, nunca durante a transação.
SectionEnd

Function FinishOpenBolha
  WriteINIStr "$Transaction" "recovery" "state" "active"
  Call OpenBolha
  ${If} $Opened == "1"
    WriteINIStr "$Transaction" "recovery" "state" "committed"
  ${Else}
    Call Rollback
    StrCpy $SectionSucceeded "0"
    MessageBox MB_OK|MB_ICONSTOP "A nova versão não confirmou a abertura. A instalação anterior foi recuperada."
  ${EndIf}
FunctionEnd

Function .onGUIEnd
  ${If} $SectionSucceeded == "1"
    WriteINIStr "$Transaction" "recovery" "state" "committed"
  ${EndIf}
FunctionEnd

Function OpenBolha
  ${If} $Opened == "1"
    Return
  ${EndIf}
  CreateDirectory "$DataRoot"
  Delete "$DataRoot\health.json"
  ; CreateProcess fornece HANDLE para encerrar SOMENTE o processo criado por este instalador.
  ; NSIS Unicode é32bits; STARTUPINFOW=68 e PROCESS_INFORMATION=16 bytes.
  System::Call '*(i68,i0,i0,i0,i0,i0,i0,i0,i0,i0,i0,i0,i0,i0,i0,i0,i0)p.r0'
  System::Call '*(p0,p0,i0,i0)p.r1'
  System::Call `kernel32::CreateProcessW(p0,w '"$INSTDIR\Bolha.exe" --updated --force-run',p0,p0,i0,i0,p0,w "$INSTDIR",p r0,p r1)i.r2`
  ${If} $2 == 0
    System::Free $0
    System::Free $1
    Return
  ${EndIf}
  System::Call '*$1(p.r2,p.r3,i.r4,i.r5)'
  StrCpy $ProcessHandle $2
  StrCpy $NewPID $4
  System::Call 'kernel32::CloseHandle(p r3)'
  System::Free $0
  System::Free $1
  StrCpy $6 0
  waitHealthy:
    System::Call 'kernel32::WaitForSingleObject(p $ProcessHandle,i0)i.r0'
    ${If} $0 == 0
      Goto unhealthy
    ${EndIf}
    ClearErrors
    FileOpen $0 "$DataRoot\health.json" r
    ${IfNot} ${Errors}
      StrCpy $2 ""
      readHealth:
        FileRead $0 $1
        ${IfNot} ${Errors}
          StrCpy $2 "$2$1"
          Goto readHealth
        ${EndIf}
      FileClose $0
      ${StrStr} $3 $2 '$\"ready$\": true'
      ${StrStr} $4 $2 '$\"version$\": $\"${VERSION}$\"'
      ${StrStr} $5 $2 '$\"pid$\": $NewPID'
      ${If} $3 != ""
      ${AndIf} $4 != ""
      ${AndIf} $5 != ""
        StrCpy $Opened "1"
        System::Call 'kernel32::CloseHandle(p $ProcessHandle)'
        Return
      ${EndIf}
    ${EndIf}
    Sleep 500
    IntOp $6 $6 + 1
    ${If} $6 < 120
      Goto waitHealthy
    ${EndIf}
  unhealthy:
    ; Nenhum processo antigo é atingido; sóo HANDLE retornado por CreateProcess acima.
    System::Call 'kernel32::TerminateProcess(p $ProcessHandle,i1)'
    System::Call 'kernel32::WaitForSingleObject(p $ProcessHandle,i5000)'
    System::Call 'kernel32::CloseHandle(p $ProcessHandle)'
FunctionEnd

Function Rollback
  SetOutPath "$TEMP"
  Rename "$INSTDIR" "$Stage.failed"
  ${If} ${FileExists} "$Backup\Bolha.exe"
    Rename "$Backup" "$INSTDIR"
    ; Evita ciclo de reinstalação no contrato de adiamento Electron/Python (epochms).
    System::Call 'kernel32::GetSystemTimeAsFileTime(*l.r0)'
    System::Int64Op $0 / 10000
    Pop $0
    System::Int64Op $0 - 11644473600000
    Pop $0
    System::Int64Op $0 + 3600000
    Pop $0
    FileOpen $1 "$DataRoot\update-deferred.json" w
    FileWrite $1 '{$\"version$\":$\"${VERSION}$\",$\"until$\":$0}'
    FileClose $1
    Exec '$\"$INSTDIR\Bolha.exe$\"'
  ${EndIf}
  ${If} $TestMode != "1"
    ${If} $PreviousVersion != ""
      WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\$RegistryGuid" "DisplayVersion" "$PreviousVersion"
      WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\$RegistryGuid" "UninstallString" "$PreviousUninstall"
      WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\$RegistryGuid" "QuietUninstallString" "$PreviousQuietUninstall"
      WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\$RegistryGuid" "DisplayIcon" "$PreviousIcon"
    ${ElseIf} $SectionSucceeded == "1"
      DeleteRegKey HKCU "Software\$RegistryGuid"
      DeleteRegKey HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\$RegistryGuid"
      Delete "$SMPROGRAMS\Bolha.lnk"
    ${EndIf}
  ${EndIf}
  Delete "$Transaction"
FunctionEnd

Function un.onInit
  SetRegView 64
  SetShellVarContext current
  StrCpy $RegistryGuid "${APPGUID}"
  ${If} ${FileExists} "$INSTDIR\bolha-test-install.flag"
    ReadEnvStr $0 "BOLHA_TEST"
    ${If} $0 != "1"
      Abort "Esta instalação é isolada para validação."
    ${EndIf}
    StrCpy $RegistryGuid "${APPGUID}-validation"
  ${EndIf}
FunctionEnd

Section "Uninstall"
  ClearErrors
  FileOpen $0 "$INSTDIR\Bolha.exe" a
  ${If} ${Errors}
    Abort "Feche a Bolha antes de desinstalar."
  ${EndIf}
  FileClose $0
  ; Lista compilada somente com arquivos deste pacote; documentos desconhecidos não são apagados.
  !include "${FILELIST}"
  Delete "$INSTDIR\bolha-test-install.flag"
  Delete "$INSTDIR\bolha-native-installation.flag"
  Delete "$INSTDIR\Uninstall Bolha.exe"
  RMDir "$INSTDIR"
  ${If} $RegistryGuid == "${APPGUID}"
  DeleteRegKey HKCU "Software\$RegistryGuid"
  DeleteRegKey HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\$RegistryGuid"
    Delete "$SMPROGRAMS\Bolha.lnk"
    ReadRegStr $0 HKCU "Software\Microsoft\Windows\CurrentVersion\Run" "Bolha"
    ${If} $0 == '$\"$INSTDIR\Bolha.exe$\"'
      DeleteRegValue HKCU "Software\Microsoft\Windows\CurrentVersion\Run" "Bolha"
    ${EndIf}
  ${EndIf}
  ; APPDATA e os backups da instalação anterior sempre ficam preservados.
SectionEnd
