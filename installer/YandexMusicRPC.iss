#define MyAppName "YandexMusicRPC"
#define MyAppVersion "0.2.2"
#define MyAppPublisher "YandexMusicRPC contributors"
#define MyAppExeName "YandexMusicRPC.exe"

[Setup]
AppId={{A6B5769B-4F91-48EF-BAD0-4F530CFCD560}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={localappdata}\Programs\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=..\dist
OutputBaseFilename=YandexMusicRPC-Setup
SetupIconFile=..\assets\icon.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
Source: "..\dist\YandexMusicRPC.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\YandexMusicRPC"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\YandexMusicRPC"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Создать значок на рабочем столе"; GroupDescription: "Дополнительно:"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Запустить YandexMusicRPC"; Flags: nowait postinstall skipifsilent
