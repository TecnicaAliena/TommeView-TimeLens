#define AppName "TommeView"
#define LegacyFFmpeg "_internal\tools\download\ffmpeg\ffmpeg-n8.1.2-51-g7ba069f4f1-win64-lgpl-8.1"
#define AppVersion "1.6.4"
#define AppAuthor "Marco Tommesani"
#ifdef ValidationBuild
#define ShellProgId "TommeView.Validation.Video"
#define ShellApplication "TommeView.Validation.exe"
#define ShellVerb "TommeViewValidation"
#define AssociationInstallerRoot "Software\TommeView\ValidationInstaller"
#define AssociationBackupRoot "Software\TommeView\ValidationInstaller\AssociationBackup"
#else
#define ShellProgId "TommeView.Video"
#define ShellApplication "TommeView.exe"
#define ShellVerb "TommeView"
#define AssociationInstallerRoot "Software\TommeView\Installer"
#define AssociationBackupRoot "Software\TommeView\Installer\AssociationBackup"
#endif

[Setup]
#ifdef ValidationBuild
AppId={{E0B2A21C-B50E-4597-A902-D0003EE2692A}
#else
AppId={{EE5761C8-27B1-44B7-8F10-3B77A1B52F7A}
#endif
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppAuthor}
AppCopyright=Copyright (c) 2026 {#AppAuthor}
DefaultDirName={localappdata}\Programs\TommeView
DefaultGroupName=TommeView
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0
DisableProgramGroupPage=yes
DisableWelcomePage=no
WizardStyle=modern
OutputDir=..\release
OutputBaseFilename=TommeViewSetup
Compression=lzma2
SolidCompression=yes
UninstallDisplayIcon={app}\TommeView.exe
VersionInfoCompany={#AppAuthor}
VersionInfoDescription=TommeView Setup
VersionInfoVersion=1.6.4.0
SetupIconFile=..\assets\tommeview.ico
CloseApplications=yes
RestartApplications=no
ChangesAssociations=yes

[Languages]
Name: "italian"; MessagesFile: "compiler:Languages\Italian.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[CustomMessages]
italian.DesktopIcon=Crea un collegamento sul desktop
english.DesktopIcon=Create a desktop shortcut
italian.Shortcuts=Collegamenti:
english.Shortcuts=Shortcuts:
italian.FileIntegration=Integrazione con Esplora file:
english.FileIntegration=File Explorer integration:
italian.OpenWith=Aggiungi TommeView al menu Apri con
english.OpenWith=Add TommeView to the Open with menu
italian.ContextMenu=Aggiungi Apri con TommeView al menu contestuale dei video
english.ContextMenu=Add Open with TommeView to the video context menu
italian.FileAssociation=Associa i formati video supportati a TommeView
english.FileAssociation=Associate supported video formats with TommeView
italian.OpenWithTommeView=Apri con TommeView
english.OpenWithTommeView=Open with TommeView
italian.Launch=Avvia TommeView
english.Launch=Launch TommeView
italian.Author=Autore: Marco Tommesani
english.Author=Author: Marco Tommesani
italian.Support=Se TommeView ti piace, offri un caffe o una birra al creatore del programma, Marco Tommesani. Grazie!
english.Support=If you enjoy TommeView, buy its creator, Marco Tommesani, a coffee or a beer. Thank you!
italian.Ready=TommeView e pronto.
english.Ready=TommeView is ready.

[Tasks]
Name: "desktopicon"; Description: "{cm:DesktopIcon}"; GroupDescription: "{cm:Shortcuts}"
Name: "openwith"; Description: "{cm:OpenWith}"; GroupDescription: "{cm:FileIntegration}"; Flags: checkedonce
Name: "contextmenu"; Description: "{cm:ContextMenu}"; GroupDescription: "{cm:FileIntegration}"; Flags: checkedonce
Name: "fileassoc"; Description: "{cm:FileAssociation}"; GroupDescription: "{cm:FileIntegration}"; Flags: unchecked

[Files]
Source: "..\dist\TommeView\TommeView.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\dist\TommeView\_internal\*"; DestDir: "{app}\_internal"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\README.en.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\dist\TommeView\docs\*"; DestDir: "{app}\docs"; Flags: ignoreversion recursesubdirs
Source: "..\dist\TommeView\THIRD_PARTY_LICENSES.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\dist\TommeView\LICENSE"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\dist\TommeView\NOTICE"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\dist\TommeView\TRADEMARKS.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\dist\TommeView\CONTRIBUTING.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\dist\TommeView\BUILDING.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\dist\TommeView\SOURCE_RELEASE.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\dist\TommeView\LIBRARY_REPLACEMENT.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\dist\TommeView\SOURCE_REFERENCES.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\dist\TommeView\SOURCE_DELIVERY.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\dist\TommeView\dependency-source-inventory.json"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\dist\TommeView\ffmpeg-build-config.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\dist\TommeView\download-tools.json"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\dist\TommeView\licenses\*"; DestDir: "{app}\licenses"; Flags: ignoreversion recursesubdirs

[InstallDelete]
; Remove the old demo only if its bytes still match our original fixture.
Type: files; Name: "{app}\demo\demo.avi"; Check: IsOriginalDemo
; Remove exactly the unused Qt files shipped by earlier builds.
Type: files; Name: "{app}\_internal\PySide6\Qt6VirtualKeyboard.dll"
Type: files; Name: "{app}\_internal\PySide6\plugins\platforminputcontexts\qtvirtualkeyboardplugin.dll"
Type: files; Name: "{app}\_internal\PySide6\Qt6Pdf.dll"
Type: files; Name: "{app}\_internal\PySide6\plugins\imageformats\qpdf.dll"
; Only known obsolete 1.6.0 vendor files; never recurse into user directories.
Type: files; Name: "{app}\{#LegacyFFmpeg}\bin\ffmpeg.exe"
Type: files; Name: "{app}\{#LegacyFFmpeg}\bin\ffprobe.exe"
Type: files; Name: "{app}\{#LegacyFFmpeg}\bin\ffplay.exe"
Type: files; Name: "{app}\{#LegacyFFmpeg}\doc\bootstrap.min.css"
Type: files; Name: "{app}\{#LegacyFFmpeg}\doc\community.html"
Type: files; Name: "{app}\{#LegacyFFmpeg}\doc\default.css"
Type: files; Name: "{app}\{#LegacyFFmpeg}\doc\developer.html"
Type: files; Name: "{app}\{#LegacyFFmpeg}\doc\drawvg-reference.html"
Type: files; Name: "{app}\{#LegacyFFmpeg}\doc\faq.html"
Type: files; Name: "{app}\{#LegacyFFmpeg}\doc\fate.html"
Type: files; Name: "{app}\{#LegacyFFmpeg}\doc\ffmpeg-all.html"
Type: files; Name: "{app}\{#LegacyFFmpeg}\doc\ffmpeg-bitstream-filters.html"
Type: files; Name: "{app}\{#LegacyFFmpeg}\doc\ffmpeg-codecs.html"
Type: files; Name: "{app}\{#LegacyFFmpeg}\doc\ffmpeg-devices.html"
Type: files; Name: "{app}\{#LegacyFFmpeg}\doc\ffmpeg-filters.html"
Type: files; Name: "{app}\{#LegacyFFmpeg}\doc\ffmpeg-formats.html"
Type: files; Name: "{app}\{#LegacyFFmpeg}\doc\ffmpeg-protocols.html"
Type: files; Name: "{app}\{#LegacyFFmpeg}\doc\ffmpeg-resampler.html"
Type: files; Name: "{app}\{#LegacyFFmpeg}\doc\ffmpeg-scaler.html"
Type: files; Name: "{app}\{#LegacyFFmpeg}\doc\ffmpeg-utils.html"
Type: files; Name: "{app}\{#LegacyFFmpeg}\doc\ffmpeg.html"
Type: files; Name: "{app}\{#LegacyFFmpeg}\doc\ffplay-all.html"
Type: files; Name: "{app}\{#LegacyFFmpeg}\doc\ffplay.html"
Type: files; Name: "{app}\{#LegacyFFmpeg}\doc\ffprobe-all.html"
Type: files; Name: "{app}\{#LegacyFFmpeg}\doc\ffprobe.html"
Type: files; Name: "{app}\{#LegacyFFmpeg}\doc\general.html"
Type: files; Name: "{app}\{#LegacyFFmpeg}\doc\git-howto.html"
Type: files; Name: "{app}\{#LegacyFFmpeg}\doc\libavcodec.html"
Type: files; Name: "{app}\{#LegacyFFmpeg}\doc\libavdevice.html"
Type: files; Name: "{app}\{#LegacyFFmpeg}\doc\libavfilter.html"
Type: files; Name: "{app}\{#LegacyFFmpeg}\doc\libavformat.html"
Type: files; Name: "{app}\{#LegacyFFmpeg}\doc\libavutil.html"
Type: files; Name: "{app}\{#LegacyFFmpeg}\doc\libswresample.html"
Type: files; Name: "{app}\{#LegacyFFmpeg}\doc\libswscale.html"
Type: files; Name: "{app}\{#LegacyFFmpeg}\doc\mailing-list-faq.html"
Type: files; Name: "{app}\{#LegacyFFmpeg}\doc\nut.html"
Type: files; Name: "{app}\{#LegacyFFmpeg}\doc\platform.html"
Type: files; Name: "{app}\{#LegacyFFmpeg}\doc\style.min.css"

[Icons]
Name: "{autoprograms}\TommeView"; Filename: "{app}\TommeView.exe"; WorkingDir: "{app}"
Name: "{autodesktop}\TommeView"; Filename: "{app}\TommeView.exe"; WorkingDir: "{app}"; Tasks: desktopicon

[Registry]
; Shared ProgID used by Open with and the optional default association.
Root: HKA; Subkey: "Software\Classes\{#ShellProgId}"; ValueType: string; ValueName: ""; ValueData: "TommeView video"; Tasks: openwith or fileassoc; Flags: uninsdeletekey
Root: HKA; Subkey: "Software\Classes\{#ShellProgId}\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "{app}\TommeView.exe,0"; Tasks: openwith or fileassoc
Root: HKA; Subkey: "Software\Classes\{#ShellProgId}\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\TommeView.exe"" ""%1"""; Tasks: openwith or fileassoc

; Register the application and its supported types without taking ownership of defaults.
Root: HKA; Subkey: "Software\Classes\Applications\{#ShellApplication}"; ValueType: string; ValueName: "FriendlyAppName"; ValueData: "TommeView"; Tasks: openwith; Flags: uninsdeletekey
Root: HKA; Subkey: "Software\Classes\Applications\{#ShellApplication}\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\TommeView.exe"" ""%1"""; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\Applications\{#ShellApplication}\SupportedTypes"; ValueType: string; ValueName: ".mp4"; ValueData: ""; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\Applications\{#ShellApplication}\SupportedTypes"; ValueType: string; ValueName: ".mkv"; ValueData: ""; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\Applications\{#ShellApplication}\SupportedTypes"; ValueType: string; ValueName: ".avi"; ValueData: ""; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\Applications\{#ShellApplication}\SupportedTypes"; ValueType: string; ValueName: ".mov"; ValueData: ""; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\Applications\{#ShellApplication}\SupportedTypes"; ValueType: string; ValueName: ".wmv"; ValueData: ""; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\Applications\{#ShellApplication}\SupportedTypes"; ValueType: string; ValueName: ".webm"; ValueData: ""; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\Applications\{#ShellApplication}\SupportedTypes"; ValueType: string; ValueName: ".m4v"; ValueData: ""; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\Applications\{#ShellApplication}\SupportedTypes"; ValueType: string; ValueName: ".mpg"; ValueData: ""; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\Applications\{#ShellApplication}\SupportedTypes"; ValueType: string; ValueName: ".mpeg"; ValueData: ""; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\Applications\{#ShellApplication}\SupportedTypes"; ValueType: string; ValueName: ".mts"; ValueData: ""; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\Applications\{#ShellApplication}\SupportedTypes"; ValueType: string; ValueName: ".m2ts"; ValueData: ""; Tasks: openwith

; Add TommeView to each extension's Open with candidates.
Root: HKA; Subkey: "Software\Classes\.mp4\OpenWithProgids"; ValueType: string; ValueName: "{#ShellProgId}"; ValueData: ""; Tasks: openwith; Flags: uninsdeletevalue
Root: HKA; Subkey: "Software\Classes\.mkv\OpenWithProgids"; ValueType: string; ValueName: "{#ShellProgId}"; ValueData: ""; Tasks: openwith; Flags: uninsdeletevalue
Root: HKA; Subkey: "Software\Classes\.avi\OpenWithProgids"; ValueType: string; ValueName: "{#ShellProgId}"; ValueData: ""; Tasks: openwith; Flags: uninsdeletevalue
Root: HKA; Subkey: "Software\Classes\.mov\OpenWithProgids"; ValueType: string; ValueName: "{#ShellProgId}"; ValueData: ""; Tasks: openwith; Flags: uninsdeletevalue
Root: HKA; Subkey: "Software\Classes\.wmv\OpenWithProgids"; ValueType: string; ValueName: "{#ShellProgId}"; ValueData: ""; Tasks: openwith; Flags: uninsdeletevalue
Root: HKA; Subkey: "Software\Classes\.webm\OpenWithProgids"; ValueType: string; ValueName: "{#ShellProgId}"; ValueData: ""; Tasks: openwith; Flags: uninsdeletevalue
Root: HKA; Subkey: "Software\Classes\.m4v\OpenWithProgids"; ValueType: string; ValueName: "{#ShellProgId}"; ValueData: ""; Tasks: openwith; Flags: uninsdeletevalue
Root: HKA; Subkey: "Software\Classes\.mpg\OpenWithProgids"; ValueType: string; ValueName: "{#ShellProgId}"; ValueData: ""; Tasks: openwith; Flags: uninsdeletevalue
Root: HKA; Subkey: "Software\Classes\.mpeg\OpenWithProgids"; ValueType: string; ValueName: "{#ShellProgId}"; ValueData: ""; Tasks: openwith; Flags: uninsdeletevalue
Root: HKA; Subkey: "Software\Classes\.mts\OpenWithProgids"; ValueType: string; ValueName: "{#ShellProgId}"; ValueData: ""; Tasks: openwith; Flags: uninsdeletevalue
Root: HKA; Subkey: "Software\Classes\.m2ts\OpenWithProgids"; ValueType: string; ValueName: "{#ShellProgId}"; ValueData: ""; Tasks: openwith; Flags: uninsdeletevalue

; Explicit context-menu command, scoped to the supported video extensions.
Root: HKA; Subkey: "Software\Classes\SystemFileAssociations\.mp4\shell\{#ShellVerb}"; ValueType: string; ValueName: ""; ValueData: "{cm:OpenWithTommeView}"; Tasks: contextmenu; Flags: uninsdeletekey
Root: HKA; Subkey: "Software\Classes\SystemFileAssociations\.mp4\shell\{#ShellVerb}"; ValueType: string; ValueName: "Icon"; ValueData: "{app}\TommeView.exe,0"; Tasks: contextmenu
Root: HKA; Subkey: "Software\Classes\SystemFileAssociations\.mp4\shell\{#ShellVerb}\command"; ValueType: string; ValueName: ""; ValueData: """{app}\TommeView.exe"" ""%1"""; Tasks: contextmenu
Root: HKA; Subkey: "Software\Classes\SystemFileAssociations\.mkv\shell\{#ShellVerb}"; ValueType: string; ValueName: ""; ValueData: "{cm:OpenWithTommeView}"; Tasks: contextmenu; Flags: uninsdeletekey
Root: HKA; Subkey: "Software\Classes\SystemFileAssociations\.mkv\shell\{#ShellVerb}"; ValueType: string; ValueName: "Icon"; ValueData: "{app}\TommeView.exe,0"; Tasks: contextmenu
Root: HKA; Subkey: "Software\Classes\SystemFileAssociations\.mkv\shell\{#ShellVerb}\command"; ValueType: string; ValueName: ""; ValueData: """{app}\TommeView.exe"" ""%1"""; Tasks: contextmenu
Root: HKA; Subkey: "Software\Classes\SystemFileAssociations\.avi\shell\{#ShellVerb}"; ValueType: string; ValueName: ""; ValueData: "{cm:OpenWithTommeView}"; Tasks: contextmenu; Flags: uninsdeletekey
Root: HKA; Subkey: "Software\Classes\SystemFileAssociations\.avi\shell\{#ShellVerb}"; ValueType: string; ValueName: "Icon"; ValueData: "{app}\TommeView.exe,0"; Tasks: contextmenu
Root: HKA; Subkey: "Software\Classes\SystemFileAssociations\.avi\shell\{#ShellVerb}\command"; ValueType: string; ValueName: ""; ValueData: """{app}\TommeView.exe"" ""%1"""; Tasks: contextmenu
Root: HKA; Subkey: "Software\Classes\SystemFileAssociations\.mov\shell\{#ShellVerb}"; ValueType: string; ValueName: ""; ValueData: "{cm:OpenWithTommeView}"; Tasks: contextmenu; Flags: uninsdeletekey
Root: HKA; Subkey: "Software\Classes\SystemFileAssociations\.mov\shell\{#ShellVerb}"; ValueType: string; ValueName: "Icon"; ValueData: "{app}\TommeView.exe,0"; Tasks: contextmenu
Root: HKA; Subkey: "Software\Classes\SystemFileAssociations\.mov\shell\{#ShellVerb}\command"; ValueType: string; ValueName: ""; ValueData: """{app}\TommeView.exe"" ""%1"""; Tasks: contextmenu
Root: HKA; Subkey: "Software\Classes\SystemFileAssociations\.wmv\shell\{#ShellVerb}"; ValueType: string; ValueName: ""; ValueData: "{cm:OpenWithTommeView}"; Tasks: contextmenu; Flags: uninsdeletekey
Root: HKA; Subkey: "Software\Classes\SystemFileAssociations\.wmv\shell\{#ShellVerb}"; ValueType: string; ValueName: "Icon"; ValueData: "{app}\TommeView.exe,0"; Tasks: contextmenu
Root: HKA; Subkey: "Software\Classes\SystemFileAssociations\.wmv\shell\{#ShellVerb}\command"; ValueType: string; ValueName: ""; ValueData: """{app}\TommeView.exe"" ""%1"""; Tasks: contextmenu
Root: HKA; Subkey: "Software\Classes\SystemFileAssociations\.webm\shell\{#ShellVerb}"; ValueType: string; ValueName: ""; ValueData: "{cm:OpenWithTommeView}"; Tasks: contextmenu; Flags: uninsdeletekey
Root: HKA; Subkey: "Software\Classes\SystemFileAssociations\.webm\shell\{#ShellVerb}"; ValueType: string; ValueName: "Icon"; ValueData: "{app}\TommeView.exe,0"; Tasks: contextmenu
Root: HKA; Subkey: "Software\Classes\SystemFileAssociations\.webm\shell\{#ShellVerb}\command"; ValueType: string; ValueName: ""; ValueData: """{app}\TommeView.exe"" ""%1"""; Tasks: contextmenu
Root: HKA; Subkey: "Software\Classes\SystemFileAssociations\.m4v\shell\{#ShellVerb}"; ValueType: string; ValueName: ""; ValueData: "{cm:OpenWithTommeView}"; Tasks: contextmenu; Flags: uninsdeletekey
Root: HKA; Subkey: "Software\Classes\SystemFileAssociations\.m4v\shell\{#ShellVerb}"; ValueType: string; ValueName: "Icon"; ValueData: "{app}\TommeView.exe,0"; Tasks: contextmenu
Root: HKA; Subkey: "Software\Classes\SystemFileAssociations\.m4v\shell\{#ShellVerb}\command"; ValueType: string; ValueName: ""; ValueData: """{app}\TommeView.exe"" ""%1"""; Tasks: contextmenu
Root: HKA; Subkey: "Software\Classes\SystemFileAssociations\.mpg\shell\{#ShellVerb}"; ValueType: string; ValueName: ""; ValueData: "{cm:OpenWithTommeView}"; Tasks: contextmenu; Flags: uninsdeletekey
Root: HKA; Subkey: "Software\Classes\SystemFileAssociations\.mpg\shell\{#ShellVerb}"; ValueType: string; ValueName: "Icon"; ValueData: "{app}\TommeView.exe,0"; Tasks: contextmenu
Root: HKA; Subkey: "Software\Classes\SystemFileAssociations\.mpg\shell\{#ShellVerb}\command"; ValueType: string; ValueName: ""; ValueData: """{app}\TommeView.exe"" ""%1"""; Tasks: contextmenu
Root: HKA; Subkey: "Software\Classes\SystemFileAssociations\.mpeg\shell\{#ShellVerb}"; ValueType: string; ValueName: ""; ValueData: "{cm:OpenWithTommeView}"; Tasks: contextmenu; Flags: uninsdeletekey
Root: HKA; Subkey: "Software\Classes\SystemFileAssociations\.mpeg\shell\{#ShellVerb}"; ValueType: string; ValueName: "Icon"; ValueData: "{app}\TommeView.exe,0"; Tasks: contextmenu
Root: HKA; Subkey: "Software\Classes\SystemFileAssociations\.mpeg\shell\{#ShellVerb}\command"; ValueType: string; ValueName: ""; ValueData: """{app}\TommeView.exe"" ""%1"""; Tasks: contextmenu
Root: HKA; Subkey: "Software\Classes\SystemFileAssociations\.mts\shell\{#ShellVerb}"; ValueType: string; ValueName: ""; ValueData: "{cm:OpenWithTommeView}"; Tasks: contextmenu; Flags: uninsdeletekey
Root: HKA; Subkey: "Software\Classes\SystemFileAssociations\.mts\shell\{#ShellVerb}"; ValueType: string; ValueName: "Icon"; ValueData: "{app}\TommeView.exe,0"; Tasks: contextmenu
Root: HKA; Subkey: "Software\Classes\SystemFileAssociations\.mts\shell\{#ShellVerb}\command"; ValueType: string; ValueName: ""; ValueData: """{app}\TommeView.exe"" ""%1"""; Tasks: contextmenu
Root: HKA; Subkey: "Software\Classes\SystemFileAssociations\.m2ts\shell\{#ShellVerb}"; ValueType: string; ValueName: ""; ValueData: "{cm:OpenWithTommeView}"; Tasks: contextmenu; Flags: uninsdeletekey
Root: HKA; Subkey: "Software\Classes\SystemFileAssociations\.m2ts\shell\{#ShellVerb}"; ValueType: string; ValueName: "Icon"; ValueData: "{app}\TommeView.exe,0"; Tasks: contextmenu
Root: HKA; Subkey: "Software\Classes\SystemFileAssociations\.m2ts\shell\{#ShellVerb}\command"; ValueType: string; ValueName: ""; ValueData: """{app}\TommeView.exe"" ""%1"""; Tasks: contextmenu

[Run]
Filename: "{app}\TommeView.exe"; Description: "{cm:Launch}"; Flags: nowait postinstall skipifsilent

[Code]
function IsOriginalDemo: Boolean;
var
  DemoPath: String;
begin
  DemoPath := ExpandConstant('{app}\demo\demo.avi');
  Result := False;
  if FileExists(DemoPath) then
    Result := CompareText(GetSHA256OfFile(DemoPath),
      'fdfc73a1f3520ad24fb095716a2f896bfda55a71ffabe8285b3b7f1b361599f8') = 0;
end;

procedure LoadVideoExtensions(var Extensions: TArrayOfString);
begin
  SetArrayLength(Extensions, 11);
  Extensions[0] := '.mp4';
  Extensions[1] := '.mkv';
  Extensions[2] := '.avi';
  Extensions[3] := '.mov';
  Extensions[4] := '.wmv';
  Extensions[5] := '.webm';
  Extensions[6] := '.m4v';
  Extensions[7] := '.mpg';
  Extensions[8] := '.mpeg';
  Extensions[9] := '.mts';
  Extensions[10] := '.m2ts';
end;

procedure AssociateVideoExtensions;
var
  Extensions: TArrayOfString;
  Index: Integer;
  HadPrevious: Cardinal;
  Previous, ExtensionKey, BackupKey: String;
begin
  LoadVideoExtensions(Extensions);
  for Index := 0 to GetArrayLength(Extensions) - 1 do
  begin
    ExtensionKey := 'Software\Classes\' + Extensions[Index];
    BackupKey := '{#AssociationBackupRoot}\' +
      Copy(Extensions[Index], 2, Length(Extensions[Index]));
    if not RegValueExists(HKCU, BackupKey, 'Saved') then
    begin
      if RegQueryStringValue(HKCU, ExtensionKey, '', Previous) and
         (CompareText(Previous, '{#ShellProgId}') <> 0) then
      begin
        HadPrevious := 1;
        RegWriteStringValue(HKCU, BackupKey, 'Previous', Previous);
      end
      else
        HadPrevious := 0;
      RegWriteDWordValue(HKCU, BackupKey, 'HadPrevious', HadPrevious);
      RegWriteDWordValue(HKCU, BackupKey, 'Saved', 1);
    end;
    RegWriteStringValue(HKCU, ExtensionKey, '', '{#ShellProgId}');
  end;
end;

procedure RestoreVideoExtensions;
var
  Extensions: TArrayOfString;
  Index: Integer;
  Saved, HadPrevious: Cardinal;
  Current, Previous, ExtensionKey, BackupKey: String;
begin
  LoadVideoExtensions(Extensions);
  for Index := 0 to GetArrayLength(Extensions) - 1 do
  begin
    ExtensionKey := 'Software\Classes\' + Extensions[Index];
    BackupKey := '{#AssociationBackupRoot}\' +
      Copy(Extensions[Index], 2, Length(Extensions[Index]));
    if RegQueryDWordValue(HKCU, BackupKey, 'Saved', Saved) and (Saved = 1) then
    begin
      if RegQueryStringValue(HKCU, ExtensionKey, '', Current) and
         (CompareText(Current, '{#ShellProgId}') = 0) then
      begin
        if RegQueryDWordValue(HKCU, BackupKey, 'HadPrevious', HadPrevious) and
           (HadPrevious = 1) and RegQueryStringValue(HKCU, BackupKey, 'Previous', Previous) then
          RegWriteStringValue(HKCU, ExtensionKey, '', Previous)
        else
          RegDeleteValue(HKCU, ExtensionKey, '');
      end;
      RegDeleteKeyIncludingSubkeys(HKCU, BackupKey);
    end;
  end;
  RegDeleteKeyIfEmpty(HKCU, '{#AssociationBackupRoot}');
  RegDeleteKeyIfEmpty(HKCU, '{#AssociationInstallerRoot}');
  RegDeleteKeyIfEmpty(HKCU, 'Software\TommeView');
end;

procedure InitializeWizard;
begin
  WizardForm.WelcomeLabel2.Caption :=
    'TommeView {#AppVersion}' + #13#10 +
    CustomMessage('Author') + #13#10 + #13#10 + CustomMessage('Support');
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if (CurStep = ssPostInstall) and WizardIsTaskSelected('fileassoc') then
    AssociateVideoExtensions;
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if CurUninstallStep = usUninstall then
    RestoreVideoExtensions;
end;

procedure CurPageChanged(CurPageID: Integer);
begin
  if CurPageID = wpFinished then
    WizardForm.FinishedLabel.Caption :=
    CustomMessage('Ready') + #13#10 + #13#10 + CustomMessage('Support');
end;
