#define MyAppName "ASIOA Audio Router"
#define MyAppVersion "0.2.2"
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
OutputBaseFilename=ASIOA-Audio-Router-Setup-0.2.2
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
Filename: "{app}\{#MyAppExeName}"; Description: "Launch ASIOA Audio Router"; Flags: nowait postinstall skipifsilent

[Code]
function InitializeSetup(): Boolean;
begin
  Result := True;
end;
