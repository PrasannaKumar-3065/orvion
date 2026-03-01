; ─────────────────────────────────────────────────────────────────────────────
;  Orvion  —  Windows Installer  (Inno Setup 6)
;
;  Produces:  OrvionSetup-windows-x64.exe
;
;  What it does:
;    1. Unpacks the PyInstaller dist/Orvion/ directory into Program Files
;    2. Bundles and silently installs the VC++ 2015-2022 runtime
;    3. Creates a desktop shortcut and Start Menu entry
;    4. Registers an Uninstall entry in "Add or Remove Programs"
;    5. Does NOT bundle the AI model — that downloads on first app launch.
;
;  The CI workflow downloads vc_redist.x64.exe into installer\windows\
;  before running ISCC, so it is available as a local file here.
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
#define VCRedist       "vc_redist.x64.exe"

[Setup]
; ── Identity ──────────────────────────────────────────────────────────────────
AppId               = {{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}}
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
PrivilegesRequired              = admin
PrivilegesRequiredOverridesAllowed = dialog
MinVersion                      = 10.0.17763
ArchitecturesAllowed            = x64
ArchitecturesInstallIn64BitMode = x64

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

; VC++ Runtime — downloaded by CI into installer\windows\ before ISCC runs.
; It is a plain local file, NOT an external URL.
Source: "{#VCRedist}"; DestDir: "{tmp}"; \
        DestName: "vc_redist.x64.exe"; \
        Flags: deleteafterinstall


; ══════════════════════════════════════════════════════════════════════════════
[Icons]
Name: "{group}\{#AppName}";           Filename: "{app}\{#AppExeName}"
Name: "{group}\Uninstall {#AppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#AppName}";     Filename: "{app}\{#AppExeName}"; \
      Tasks: desktopicon


; ══════════════════════════════════════════════════════════════════════════════
[Run]
; 1. Install VC++ runtime silently
Filename: "{tmp}\vc_redist.x64.exe"; \
    Parameters: "/install /quiet /norestart"; \
    StatusMsg: "Installing Microsoft Visual C++ Runtime..."; \
    Flags: waituntilterminated runhidden

; 2. Offer to launch Orvion after setup
Filename: "{app}\{#AppExeName}"; \
    Description: "{cm:LaunchProgram,{#StringChange(AppName,'&','&&')}}"; \
    Flags: nowait postinstall skipifsilent


; ══════════════════════════════════════════════════════════════════════════════
[UninstallDelete]
Type: filesandordirs; Name: "{app}"


; ══════════════════════════════════════════════════════════════════════════════
[Code]

var
  RequirementsPage: TOutputMsgMemoWizardPage;

procedure InitializeWizard();
var
  Msg: String;
begin
  Msg := 'Orvion will be installed on your computer.' + #13#10 + #13#10 +
         'What happens after installation:' + #13#10 +
         '  * On first launch a one-time setup wizard will appear.' + #13#10 +
         '  * It automatically detects your GPU (NVIDIA supported).' + #13#10 +
         '  * The Orvion AI model (~6 GB) is downloaded once from' + #13#10 +
         '    Hugging Face - an internet connection is required.' + #13#10 + #13#10 +
         'Subsequent launches are fully offline.' + #13#10 + #13#10 +
         'Disk space required: ~4 GB (app) + ~6 GB (AI model)';

  RequirementsPage := CreateOutputMsgMemoPage(
    wpWelcome,
    'What to Expect',
    'Please read before continuing',
    'Setup Information:',
    Msg
  );
end;

function NextButtonClick(CurPageID: Integer): Boolean;
var
  SpaceNeededMB: Cardinal;
  SpaceFreeMB:   Cardinal;
  TotalSpaceMB:  Cardinal;
  DrivePath:     String;
begin
  Result := True;
  if CurPageID = wpSelectDir then
  begin
    SpaceNeededMB := 4096;
    DrivePath := ExtractFileDrive(WizardDirValue);
    if GetSpaceOnDisk(DrivePath, True, SpaceFreeMB, TotalSpaceMB) then
    begin
      if SpaceFreeMB < SpaceNeededMB then
      begin
        MsgBox(
          'Not enough disk space.' + #13#10 +
          'Orvion requires at least 4 GB free in the selected directory.',
          mbError, MB_OK
        );
        Result := False;
      end;
    end;
  end;
end;
