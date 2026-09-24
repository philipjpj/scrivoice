; Installer di ScriVoice per Windows (Inno Setup 6).
; Uso (dalla cartella del progetto, dopo PyInstaller):
;   ISCC /DAppVersion=1.0.0 packaging\windows\installer.iss
; Risultato: dist\ScriVoiceSetup-<versione>.exe
;
; Installazione per il solo utente, senza permessi di amministratore, in
; %LOCALAPPDATA%\Programs\ScriVoice. Le impostazioni stanno in %APPDATA%\ScriVoice
; e restano anche dopo la disinstallazione (una reinstallazione ritrova le impostazioni).

#ifndef AppVersion
  #define AppVersion "1.0.0"
#endif

[Setup]
AppId={{6F1B7A52-3C8E-4B8B-9A51-5C3E2D7F1A90}
AppName=ScriVoice
AppVersion={#AppVersion}
AppVerName=ScriVoice {#AppVersion}
AppPublisher=ScriVoice
AppPublisherURL=https://github.com/philipjpj/scrivoice
DefaultDirName={localappdata}\Programs\ScriVoice
DisableProgramGroupPage=yes
DisableDirPage=yes
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0
OutputDir=..\..\dist
OutputBaseFilename=ScriVoiceSetup-{#AppVersion}
SetupIconFile=..\..\build\icon.ico
UninstallDisplayIcon={app}\ScriVoice.exe
UninstallDisplayName=ScriVoice
LicenseFile=..\..\LICENSE
Compression=lzma2/max
SolidCompression=yes
LZMANumBlockThreads=4
WizardStyle=modern
ShowLanguageDialog=auto
CloseApplications=yes
RestartApplications=no

[Languages]
Name: "en"; MessagesFile: "compiler:Default.isl"
Name: "it"; MessagesFile: "compiler:Languages\Italian.isl"
Name: "es"; MessagesFile: "compiler:Languages\Spanish.isl"

[CustomMessages]
en.AutoStart=Start ScriVoice when Windows starts
it.AutoStart=Avvia ScriVoice all'accensione di Windows
es.AutoStart=Iniciar ScriVoice al encender Windows
en.Preparing=Preparing ScriVoice (this may take a minute)...
it.Preparing=Preparazione di ScriVoice (può richiedere un minuto)...
es.Preparing=Preparando ScriVoice (puede tardar un minuto)...

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"
Name: "autostart"; Description: "{cm:AutoStart}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
Source: "..\..\dist\ScriVoice\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\ScriVoice"; Filename: "{app}\ScriVoice.exe"
Name: "{autodesktop}\ScriVoice"; Filename: "{app}\ScriVoice.exe"; Tasks: desktopicon

[Registry]
; avvio automatico (stesso valore che imposta l'app dalle impostazioni, vedi autostart.py)
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "ScriVoice"; ValueData: """{app}\ScriVoice.exe"""; Tasks: autostart
; alla disinstallazione rimuovo l'avvio automatico anche se è stato attivato dall'app
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: none; ValueName: "ScriVoice"; Flags: uninsdeletevalue

[Run]
; primo avvio "a vuoto" durante l'installazione: Windows Defender controlla subito tutti i file,
; così il primo avvio vero del cliente è rapido (e verifica che il pacchetto funzioni)
Filename: "{app}\ScriVoice.exe"; Parameters: "--selftest ""{tmp}\selftest.json"""; StatusMsg: "{cm:Preparing}"; Flags: runhidden waituntilterminated
Filename: "{app}\ScriVoice.exe"; Description: "{cm:LaunchProgram,ScriVoice}"; Flags: nowait postinstall skipifsilent
