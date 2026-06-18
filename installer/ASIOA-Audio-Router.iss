#define MyAppName "ASIOA Audio Router"
#define MyAppVersion "0.2.5"
#define MyAppPublisher "Raywonder"
#define MyAppExeName "ASIOA Audio Router.exe"
#define SourceRoot "E:\Builds\asioa-audio-router\publish"

[Setup]
AppId={{2A7C37F5-1137-4CF0-9F12-0E7E3E2AF019}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\ASIOA Audio Router
DefaultGroupName=ASIOA Audio Router
DisableProgramGroupPage=yes
LicenseFile=..\EULA.txt
OutputDir=E:\Downloads\asioa-audio-router
OutputBaseFilename=ASIOA-Audio-Router-Setup-0.2.5
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

[Files]
Source: "{#SourceRoot}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\LICENSE.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\THIRD_PARTY_NOTICES.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\RELEASE_NOTES.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\docs\*"; DestDir: "{app}\docs"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\ASIOA Audio Router"; Filename: "{app}\{#MyAppExeName}"
Name: "{commondesktop}\ASIOA Audio Router"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
Name: "{group}\Uninstall ASIOA Audio Router"; Filename: "{uninstallexe}"

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Shortcuts:"; Flags: unchecked

[Run]
Filename: "powershell.exe"; Parameters: "-ExecutionPolicy Bypass -File ""{app}\driver\install-asioa-driver.ps1"""; Description: "Register packaged ASIOA virtual ASIO driver"; Flags: skipifdoesntexist; Check: ShouldInstallDriverNow
Filename: "{app}\{#MyAppExeName}"; Description: "Launch ASIOA Audio Router"; Flags: nowait postinstall skipifsilent

[UninstallRun]
Filename: "powershell.exe"; Parameters: "-ExecutionPolicy Bypass -File ""{app}\driver\uninstall-asioa-driver.ps1"""; Flags: runhidden skipifdoesntexist; Check: ShouldRunDriverUninstall; RunOnceId: "UnregisterASIOADriver"

[Code]
var
  DriverPage: TInputOptionWizardPage;

function InitializeSetup(): Boolean;
begin
  Result := True;
end;

procedure InitializeWizard();
begin
  DriverPage := CreateInputOptionPage(
    wpSelectTasks,
    'ASIOA Audio Driver',
    'Choose how ASIOA should handle the packaged virtual ASIO driver.',
    'If this installer includes ASIOA.Driver.dll, it can register the packaged driver for local testing. Public distribution still requires a valid driver signing path. You can register it now, be reminded later, or install only the control panel.',
    True,
    False
  );
  DriverPage.Add('Install ASIOA driver now');
  DriverPage.Add('Ask me later');
  DriverPage.Add('Control panel only');
  DriverPage.SelectedValueIndex := 0;
end;

function ShouldInstallDriverNow(): Boolean;
begin
  Result :=
    Assigned(DriverPage) and
    (DriverPage.SelectedValueIndex = 0) and
    FileExists(ExpandConstant('{app}\driver\install-asioa-driver.ps1')) and
    FileExists(ExpandConstant('{app}\driver\ASIOA.Driver.dll'));
end;

function ShouldRunDriverUninstall(): Boolean;
begin
  Result := FileExists(ExpandConstant('{app}\driver\uninstall-asioa-driver.ps1'));
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  Choice: String;
  SettingsDir: String;
begin
  if CurStep = ssPostInstall then
  begin
    if Assigned(DriverPage) then
    begin
      if DriverPage.SelectedValueIndex = 0 then
        Choice := 'Install ASIOA driver now'
      else if DriverPage.SelectedValueIndex = 1 then
        Choice := 'Ask me later'
      else
        Choice := 'Control panel only';
      SettingsDir := ExpandConstant('{userappdata}\ASIOA Audio Router');
      ForceDirectories(SettingsDir);
      SaveStringToFile(
        SettingsDir + '\installer-driver-choice.json',
        '{' + #13#10 +
        '  "driver_install_option": "' + Choice + '",' + #13#10 +
        '  "selected_at_install": "' + GetDateTimeString('yyyy-mm-dd"T"hh:nn:ss', '-', ':') + '"' + #13#10 +
        '}' + #13#10,
        False
      );
    end;
  end;
end;
