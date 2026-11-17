; Inno Setup script of the Windows installer of OPTiBAR: packs the PyInstaller build of dist\OPTiBAR
; into dist\installer\OPTiBAR-<version>-Setup.exe. Build it with build.ps1 of this folder, which passes
; the version of pyproject.toml:
;
;     ISCC.exe /DAppVersion=0.1.0 packaging\windows\optibar.iss

#ifndef AppVersion
  #error Pass the version: ISCC.exe /DAppVersion=x.y.z optibar.iss
#endif

#define AppName "OPTiBAR"
#define AppExe "OPTiBAR.exe"
#define AppUrl "https://github.com/OPTiBAR/OPTiBAR"
#define AccessDriver "Microsoft Access Driver (*.mdb, *.accdb)"
#define AccessDriverUrl "https://www.microsoft.com/en-us/download/details.aspx?id=54920"

[Setup]
; the AppId identifies the app for upgrades and the uninstaller, it must never change
AppId={{5A083FB8-BEC3-4C6E-9825-BE8E27D357A2}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
AppPublisher=OPTiBAR
AppPublisherURL={#AppUrl}
AppSupportURL={#AppUrl}/issues
AppUpdatesURL={#AppUrl}/releases
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
LicenseFile=..\..\LICENSE
; installs for the current user without admin rights, or for all users when the user chooses so
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
; the build is 64-bit Python, and the Access driver it reads SAFE files with must be 64-bit too
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir=..\..\dist\installer
OutputBaseFilename={#AppName}-{#AppVersion}-Setup
SetupIconFile=..\..\assets\optibar.ico
UninstallDisplayIcon={app}\{#AppExe}
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; the whole one-folder build; old files are removed first, so an upgrade leaves no stale modules
Source: "..\..\dist\OPTiBAR\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[InstallDelete]
Type: filesandordirs; Name: "{app}\_internal"

[Icons]
Name: "{autoprograms}\{#AppName}"; Filename: "{app}\{#AppExe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExe}"; Tasks: desktopicon

[Run]
Filename: "{#AccessDriverUrl}"; Description: "Download the Microsoft Access ODBC driver (64-bit), needed to read SAFE files"; Flags: postinstall shellexec skipifsilent; Check: not AccessDriverInstalled
Filename: "{app}\{#AppExe}"; Description: "{cm:LaunchProgram,{#AppName}}"; Flags: nowait postinstall skipifsilent

[Code]
// OPTiBAR reads the SAFE database through the 64-bit Access ODBC driver, which Microsoft doesn't let
// others redistribute; the installer only checks for it and offers the download
function AccessDriverInstalled: Boolean;
begin
  Result := RegValueExists(HKLM64, 'SOFTWARE\ODBC\ODBCINST.INI\ODBC Drivers', '{#AccessDriver}');
end;

procedure CurPageChanged(CurPageID: Integer);
begin
  if (CurPageID = wpFinished) and not AccessDriverInstalled then
    WizardForm.FinishedLabel.Caption := WizardForm.FinishedLabel.Caption + #13#10#13#10 +
      'The Microsoft Access ODBC driver (64-bit) was not found. OPTiBAR needs it to read the ' +
      'databases SAFE exports: install the "Microsoft Access Database Engine 2016 Redistributable", ' +
      'the x64 version, from Microsoft.';
end;
