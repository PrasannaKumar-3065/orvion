; ─────────────────────────────────────────────────────────────────────────────
;  Orvion  —  Windows Installer  (Inno Setup 6)
;
;  Produces:  OrvionSetup-windows-x64.exe
;
;  What it does:
;    1. Unpacks the PyInstaller dist/Orvion/ directory into Program Files
;    2. Creates a desktop shortcut and Start Menu entry
;    3. Registers an Uninstall entry in "Add or Remove Programs"
;    4. Does NOT bundle the AI model — that downloads on first app launch.
;
;  Build command (from repo root, after PyInstaller run):
;    iscc installer\windows\setup.iss
; ─────────────────────────────────────────────────────────────────────────────

#define AppName        "Orvion"
#define AppVersion     "1.0.0"
#define AppPublisher   "Orvion"
#define AppURL         "https://github.com/your-org/orvion"
#define AppExeName     "Orvion.exe"
#define DistDir        "..\..\dist\Orvion"
#define OutDir         "..\..\dist\installer"

[Setup]
; ── Identity ──────────────────────────────────────────────────────────────────
AppId               = {{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName             = {#AppName}
AppVersion          = {#AppVersion}
AppVerName          = {#AppName} {#AppVersion}
AppPublisherURL     = {#AppURL}
AppSupportURL       = {#AppURL}/issues
AppUpdatesURL       = {#AppURL}/releases

; ── Install location ──────────────────────────────────────────────────────────
DefaultDirName      = {autopf}\{#AppName}
DefaultGroupName    = {#AppName}
AllowNoIcons        = yes

; ── Output ────────────────────────────────────────────────────────────────────
OutputDir           = {#OutDir}
OutputBaseFilename  = OrvionSetup-windows-x64
SetupIconFile       = orvion.ico
WizardStyle         = modern
WizardSizePercent   = 120

; ── Compression ───────────────────────────────────────────────────────────────
Compression         = lzma2/ultra64
SolidCompression    = yes
LZMAUseSeparateProcess = yes

; ── Requirements ──────────────────────────────────────────────────────────────
PrivilegesRequired  = lowest          ; install per-user if no admin rights
PrivilegesRequiredOverridesAllowed = dialog
MinVersion          = 10.0.17763      ; Windows 10 1809+
ArchitecturesAllowed             = x64
ArchitecturesInstallIn64BitMode  = x64

; ── Misc ──────────────────────────────────────────────────────────────────────
DisableProgramGroupPage = yes
UninstallDisplayIcon    = {app}\{#AppExeName}
UninstallDisplayName    = {#AppName} {#AppVersion}


; ══════════════════════════════════════════════════════════════════════════════
[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"


; ══════════════════════════════════════════════════════════════════════════════
[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; \
      GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked


; ══════════════════════════════════════════════════════════════════════════════
[Files]
; Entire PyInstaller one-dir bundle
Source: "{#DistDir}\*"; DestDir: "{app}"; \
        Flags: ignoreversion recursesubdirs createallsubdirs


; ══════════════════════════════════════════════════════════════════════════════
[Icons]
; Start Menu
Name: "{group}\{#AppName}";         Filename: "{app}\{#AppExeName}"
Name: "{group}\Uninstall {#AppName}"; Filename: "{uninstallexe}"

; Desktop (only if task selected)
Name: "{autodesktop}\{#AppName}";   Filename: "{app}\{#AppExeName}"; \
      Tasks: desktopicon


; ══════════════════════════════════════════════════════════════════════════════
[Run]
; Launch Orvion after setup finishes (optional tick-box for user)
Filename: "{app}\{#AppExeName}"; \
          Description: "{cm:LaunchProgram,{#StringChange(AppName,'&','&&')}}"; \
          Flags: nowait postinstall skipifsilent


; ══════════════════════════════════════════════════════════════════════════════
[UninstallDelete]
; Remove user data only if user explicitly opted in via custom page (omitted
; for simplicity — model cache lives in %APPDATA%\Orvion and is left intact)
Type: filesandordirs; Name: "{app}"


; ══════════════════════════════════════════════════════════════════════════════
[Code]

{ ── Custom pages ────────────────────────────────────────────────────────── }

var
  RequirementsPage: TOutputMsgMemoWizardPage;

procedure InitializeWizard();
var
  Msg: String;
begin
  { Information page shown before installation begins }
  Msg := 'Orvion will be installed on your computer.' + #13#10 + #13#10 +
         'What happens after installation:' + #13#10 +
         '  • On first launch a one-time setup wizard will appear.' + #13#10 +
         '  • It automatically detects your GPU (NVIDIA supported).' + #13#10 +
         '  • The Orvion AI model (~6 GB) is downloaded once from' + #13#10 +
         '    Hugging Face — an internet connection is required.' + #13#10 + #13#10 +
         'Subsequent launches are fully offline.' + #13#10 + #13#10 +
         'Disk space required: ~4 GB (app) + ~6 GB (AI model)';

  RequirementsPage := CreateOutputMsgMemoWizardPage(
    wpWelcome,
    'What to Expect',
    'Please read before continuing',
    Msg
  );
end;

{ ── Validate disk space ───────────────────────────────────────────────────── }
function NextButtonClick(CurPageID: Integer): Boolean;
var
  SpaceNeeded: Int64;
  SpaceFree:   Int64;
begin
  Result := True;
  if CurPageID = wpSelectDir then
  begin
    SpaceNeeded := 4 * 1024 * 1024 * 1024;  { 4 GB for the app bundle }
    SpaceFree   := DiskSpaceFree(WizardDirValue[1]);
    if SpaceFree < SpaceNeeded then
    begin
      MsgBox(
        'Not enough disk space.' + #13#10 +
        'Orvion requires at least 4 GB free in the selected directory' + #13#10 +
        '(plus ~6 GB for the AI model in your user profile).',
        mbError, MB_OK
      );
      Result := False;
    end;
  end;
end;
