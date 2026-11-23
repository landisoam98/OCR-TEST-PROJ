; BHP Scanner installer (Inno Setup 6). Built by .github/workflows/build-windows.yml:
;   iscc /DAppVersion=2.0.0 installer\bhp-scanner.iss   (after PyInstaller has made dist\BHP Scanner\)

#ifndef AppVersion
  #define AppVersion "0.0.0"
#endif
#define DataDir "{commonappdata}\BHP Scanner"
#define TaskName "BHP Scanner"

[Setup]
AppId={{6F1C2B7A-4E8D-4B4A-9C3E-2D7B5A1F8E40}
AppName=BHP Scanner
AppVersion={#AppVersion}
AppPublisher=BHP
DefaultDirName={autopf}\BHP Scanner
DefaultGroupName=BHP Scanner
DisableProgramGroupPage=yes
PrivilegesRequired=admin
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir=Output
OutputBaseFilename=BHP-Scanner-Setup-{#AppVersion}
Compression=lzma2
SolidCompression=yes
UninstallDisplayIcon={app}\BHP Scanner.exe
WizardStyle=modern

[Files]
Source: "..\dist\BHP Scanner\*"; DestDir: "{app}"; Flags: recursesubdirs ignoreversion
Source: "..\windows\register-task.ps1"; DestDir: "{app}"; Flags: ignoreversion

[Dirs]
Name: "{#DataDir}"

[Icons]
Name: "{group}\Open review folder"; Filename: "{code:ReviewFolder}"
Name: "{group}\Filing log (Excel)"; Filename: "{#DataDir}\data\log.csv"
Name: "{group}\Settings"; Filename: "notepad.exe"; Parameters: """{#DataDir}\config.yaml"""

[UninstallRun]
Filename: "schtasks.exe"; Parameters: "/End /TN ""{#TaskName}"""; Flags: runhidden; RunOnceId: "StopTask"
Filename: "taskkill.exe"; Parameters: "/F /IM ""BHP Scanner.exe"""; Flags: runhidden; RunOnceId: "KillApp"
Filename: "schtasks.exe"; Parameters: "/Delete /TN ""{#TaskName}"" /F"; Flags: runhidden; RunOnceId: "DeleteTask"

[Code]
var
  FolderPage: TInputDirWizardPage;

function ConfigFile: String;
begin
  Result := ExpandConstant('{#DataDir}\config.yaml');
end;

function ReviewFolder(Param: String): String;
begin
  Result := FolderPage.Values[1] + '\_Needs Review';
end;

procedure InitializeWizard;
begin
  FolderPage := CreateInputDirPage(wpSelectDir, 'Folders',
    'Where do scans arrive, and where should delivery notes be filed?',
    'Pick the folder your scanner saves PDFs to, and the folder where the Year \ Month \ Customer folders will be made.',
    False, '');
  FolderPage.Add('Scanner inbox folder:');
  FolderPage.Add('Filed delivery notes folder:');
  FolderPage.Values[0] := GetPreviousData('Inbox', ExpandConstant('{sd}\Scans\Inbox'));
  FolderPage.Values[1] := GetPreviousData('OutputRoot', ExpandConstant('{sd}\Delivery Notes'));
end;

procedure RegisterPreviousData(PreviousDataKey: Integer);
begin
  SetPreviousData(PreviousDataKey, 'Inbox', FolderPage.Values[0]);
  SetPreviousData(PreviousDataKey, 'OutputRoot', FolderPage.Values[1]);
end;

// Upgrade: settings already exist, so don't ask for the folders again.
function ShouldSkipPage(PageID: Integer): Boolean;
begin
  Result := (PageID = FolderPage.ID) and FileExists(ConfigFile);
end;

function NextButtonClick(CurPageID: Integer): Boolean;
var
  i: Integer;
begin
  Result := True;
  if CurPageID = FolderPage.ID then
    for i := 0 to 1 do
      if not (ForceDirectories(FolderPage.Values[i])
              and SaveStringToFile(FolderPage.Values[i] + '\.bhp-write-test', 'ok', False)
              and DeleteFile(FolderPage.Values[i] + '\.bhp-write-test')) then
      begin
        MsgBox('Can''t write to ' + FolderPage.Values[i] + '. Pick another folder or fix its permissions.', mbError, MB_OK);
        Result := False;
        Exit;
      end;
end;

// Windows can't replace a running program, so stop it before copying files (upgrade).
function PrepareToInstall(var NeedsRestart: Boolean): String;
var
  Code: Integer;
begin
  Exec('schtasks.exe', '/End /TN "{#TaskName}"', '', SW_HIDE, ewWaitUntilTerminated, Code);
  Exec('taskkill.exe', '/F /IM "BHP Scanner.exe"', '', SW_HIDE, ewWaitUntilTerminated, Code);
  Result := '';
end;

function YamlQuote(S: String): String;
begin
  StringChangeEx(S, '''', '''''', True);
  Result := '''' + S + '''';
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  Code: Integer;
begin
  if CurStep <> ssPostInstall then Exit;
  if not FileExists(ConfigFile) then
    SaveStringToFile(ConfigFile,
      '# BHP Scanner settings. After editing, restart the "BHP Scanner" task (or the server).' + #13#10 +
      'inbox: ' + YamlQuote(FolderPage.Values[0]) + #13#10 +
      'output_root: ' + YamlQuote(FolderPage.Values[1]) + #13#10 +
      'engine: local' + #13#10, False);

  WizardForm.StatusLabel.Caption := 'Checking folders and the OCR engine...';
  if not Exec(ExpandConstant('{app}\BHP Scanner.exe'), '--config "' + ConfigFile + '" selftest', '',
              SW_HIDE, ewWaitUntilTerminated, Code) or (Code <> 0) then
    MsgBox('The self-test failed, so BHP Scanner was not started.' + #13#10 +
           'Details: ' + ExpandConstant('{#DataDir}\data\dnfiler.log'), mbError, MB_OK)
  else
  begin
    WizardForm.StatusLabel.Caption := 'Starting BHP Scanner...';
    Exec('powershell.exe', '-NoProfile -ExecutionPolicy Bypass -File "' + ExpandConstant('{app}\register-task.ps1') +
         '" -Exe "' + ExpandConstant('{app}\BHP Scanner.exe') + '" -Config "' + ConfigFile + '"', '',
         SW_HIDE, ewWaitUntilTerminated, Code);
    if Code <> 0 then
      MsgBox('Could not start the background task (code ' + IntToStr(Code) + ').', mbError, MB_OK);
  end;
end;

// Filed documents are never touched. Settings and the log are kept unless the user says otherwise.
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if (CurUninstallStep = usPostUninstall) and
     (SuppressibleMsgBox('Also delete the BHP Scanner settings and filing log?' + #13#10 +
                         '(Filed delivery notes are not affected.)',
                         mbConfirmation, MB_YESNO or MB_DEFBUTTON2, IDNO) = IDYES) then
    DelTree(ExpandConstant('{#DataDir}'), True, True, True);
end;
