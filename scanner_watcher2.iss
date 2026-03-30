; Inno Setup Script for Scanner-Watcher2
; This script creates a professional Windows installer that:
; - Installs the application to Program Files
; - Creates necessary AppData directories
; - Installs and configures the Windows service
; - Creates Start Menu shortcuts
; - Handles clean uninstallation

#define MyAppName "Scanner-Watcher2"
#define MyAppDataDir "ScannerWatcher2"
#define MyAppVersion "1.4.0"
#define MyAppPublisher "Scanner-Watcher2 Team"
#define MyAppURL "https://github.com/scanner-watcher2"
#define MyAppExeName "ScannerWatcher2.exe"
#define MyAppServiceName "ScannerWatcher2"
#define MyAppServiceDisplayName "Scanner-Watcher2 Document Processing Service"

[Setup]
; NOTE: The value of AppId uniquely identifies this application.
; Do not use the same AppId value in installers for other applications.
AppId={{8F9A3B2C-1D4E-5F6A-7B8C-9D0E1F2A3B4C}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
LicenseFile=LICENSE.txt
; Uncomment the following line to run in non administrative install mode (install for current user only.)
;PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
OutputDir=Output
OutputBaseFilename=ScannerWatcher2Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
; Require Windows 10 or later
MinVersion=10.0
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64
UninstallDisplayIcon={app}\{#MyAppExeName}
; Optional: Uncomment these lines when icon files are available
; SetupIconFile=windows\icon.ico
; WizardImageFile=windows\wizard-image.bmp
; WizardSmallImageFile=windows\wizard-small-image.bmp

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Main executable
Source: "dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
; Configuration template
Source: "config_template.json"; DestDir: "{app}"; Flags: ignoreversion
; Documentation
Source: "README.txt"; DestDir: "{app}"; Flags: ignoreversion isreadme
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "LICENSE.txt"; DestDir: "{app}"; Flags: ignoreversion
; NOTE: Don't use "Flags: ignoreversion" on any shared system files

[Icons]
Name: "{group}\Start {#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Comment: "Start Scanner-Watcher2 document processing"
Name: "{group}\{#MyAppName} Configuration"; Filename: "notepad.exe"; Parameters: """{userappdata}\{#MyAppDataDir}\config.json"""; Comment: "Edit Scanner-Watcher2 configuration"
Name: "{group}\{#MyAppName} Logs"; Filename: "{userappdata}\{#MyAppDataDir}\logs"; Comment: "View Scanner-Watcher2 logs"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName} Configuration"; Filename: "notepad.exe"; Parameters: """{userappdata}\{#MyAppDataDir}\config.json"""; Tasks: desktopicon; Comment: "Edit Scanner-Watcher2 configuration"

[Run]
; Create AppData directories and copy configuration
Filename: "{cmd}"; Parameters: "/c if not exist ""{userappdata}\{#MyAppDataDir}"" mkdir ""{userappdata}\{#MyAppDataDir}"""; Flags: runhidden
Filename: "{cmd}"; Parameters: "/c if not exist ""{userappdata}\{#MyAppDataDir}\logs"" mkdir ""{userappdata}\{#MyAppDataDir}\logs"""; Flags: runhidden
Filename: "{cmd}"; Parameters: "/c if not exist ""{userappdata}\{#MyAppDataDir}\temp"" mkdir ""{userappdata}\{#MyAppDataDir}\temp"""; Flags: runhidden
Filename: "{cmd}"; Parameters: "/c if not exist ""{userappdata}\{#MyAppDataDir}\config.json"" copy ""{app}\config_template.json"" ""{userappdata}\{#MyAppDataDir}\config.json"""; Flags: runhidden
; Start the application now (optional)
Filename: "{app}\{#MyAppExeName}"; Description: "Start {#MyAppName} now"; Flags: postinstall nowait skipifsilent

[UninstallRun]
; Kill the running process
Filename: "taskkill.exe"; Parameters: "/f /im {#MyAppExeName}"; Flags: runhidden; RunOnceId: "KillProcess"
; Remove the scheduled task
Filename: "schtasks.exe"; Parameters: "/delete /tn ""{#MyAppServiceName}"" /f"; Flags: runhidden; RunOnceId: "RemoveTask"
; Also try to remove legacy Windows service if present
Filename: "sc.exe"; Parameters: "stop {#MyAppServiceName}"; Flags: runhidden; RunOnceId: "StopLegacyService"
Filename: "sc.exe"; Parameters: "delete {#MyAppServiceName}"; Flags: runhidden; RunOnceId: "RemoveLegacyService"

[UninstallDelete]
; Clean up temporary files (but preserve logs and configuration)
Type: filesandordirs; Name: "{userappdata}\{#MyAppDataDir}\temp"

[Code]
var
  WatchDirPage: TInputDirWizardPage;
  ExtraDirsPage: TInputQueryWizardPage;
  ApiKeyPage: TInputQueryWizardPage;

procedure InitializeWizard;
begin
  { Primary watch directory - uses dir picker with browse button }
  WatchDirPage := CreateInputDirPage(wpSelectDir,
    'Select Watch Directory', 'Which folder should Scanner-Watcher2 monitor for scanned documents?',
    'Select the primary folder where your scanner saves PDF files.',
    False, '');
  WatchDirPage.Add('Watch Directory:');
  WatchDirPage.Values[0] := 'C:\Scans';

  { Additional watch directories - text fields that allow empty values }
  ExtraDirsPage := CreateInputQueryPage(WatchDirPage.ID,
    'Additional Watch Directories (Optional)',
    'Add more folders to monitor',
    'Enter full paths to additional scan folders. Leave blank to skip. You can always add more later by editing the configuration file.');
  ExtraDirsPage.Add('Additional Directory:', False);
  ExtraDirsPage.Values[0] := '';
  ExtraDirsPage.Add('Additional Directory:', False);
  ExtraDirsPage.Values[1] := '';

  { OpenAI API key }
  ApiKeyPage := CreateInputQueryPage(ExtraDirsPage.ID,
    'OpenAI API Configuration', 'Enter your OpenAI API key',
    'Scanner-Watcher2 uses OpenAI GPT-4 Vision to classify documents. You need an API key from https://platform.openai.com');
  ApiKeyPage.Add('OpenAI API Key:', True);
  ApiKeyPage.Values[0] := '';
end;

function NextButtonClick(CurPageID: Integer): Boolean;
begin
  Result := True;
  
  { Validate watch directories - at least the primary is required }
  if CurPageID = WatchDirPage.ID then
  begin
    if WatchDirPage.Values[0] = '' then
    begin
      MsgBox('Please specify at least one watch directory.', mbError, MB_OK);
      Result := False;
    end;
  end;
  
  { Validate API key }
  if CurPageID = ApiKeyPage.ID then
  begin
    if ApiKeyPage.Values[0] = '' then
    begin
      if MsgBox('You have not entered an OpenAI API key. The service will not work without a valid API key. Continue anyway?', 
                mbConfirmation, MB_YESNO) = IDNO then
      begin
        Result := False;
      end;
    end
    else if (Length(ApiKeyPage.Values[0]) < 20) then
    begin
      MsgBox('The API key appears to be invalid (too short). Please check your API key.', mbError, MB_OK);
      Result := False;
    end;
  end;
end;

function EscapeBackslashes(const S: String): String;
var
  I: Integer;
begin
  Result := '';
  for I := 1 to Length(S) do
  begin
    if S[I] = '\' then
      Result := Result + '\\'
    else
      Result := Result + S[I];
  end;
end;

function BuildWatchDirsJson(): String;
var
  DirCount: Integer;
  Dir: String;
begin
  { Build JSON array from primary dir + optional extra dirs }
  Result := '  "watch_directories": [' + #13#10;
  DirCount := 0;

  { Primary directory (always present) }
  Dir := WatchDirPage.Values[0];
  if Dir <> '' then
  begin
    Result := Result + '    "' + EscapeBackslashes(Dir) + '"';
    DirCount := DirCount + 1;
  end;

  { Extra directory 1 }
  Dir := ExtraDirsPage.Values[0];
  if Dir <> '' then
  begin
    if DirCount > 0 then
      Result := Result + ',' + #13#10;
    Result := Result + '    "' + EscapeBackslashes(Dir) + '"';
    DirCount := DirCount + 1;
  end;

  { Extra directory 2 }
  Dir := ExtraDirsPage.Values[1];
  if Dir <> '' then
  begin
    if DirCount > 0 then
      Result := Result + ',' + #13#10;
    Result := Result + '    "' + EscapeBackslashes(Dir) + '"';
    DirCount := DirCount + 1;
  end;

  Result := Result + #13#10 + '  ],';
end;

procedure RegisterAutoStartTask();
var
  ScriptContent: TStringList;
  ScriptPath: String;
  ExePath: String;
  ResultCode: Integer;
begin
  ExePath := ExpandConstant('{app}\{#MyAppExeName}');
  ScriptPath := ExpandConstant('{tmp}\register_task.ps1');

  ScriptContent := TStringList.Create;
  try
    ScriptContent.Add('$exePath = "' + ExePath + '"');
    ScriptContent.Add('$taskName = "{#MyAppServiceName}"');
    ScriptContent.Add('');
    ScriptContent.Add('$action = New-ScheduledTaskAction -Execute $exePath');
    ScriptContent.Add('$trigger = New-ScheduledTaskTrigger -AtLogOn');
    ScriptContent.Add('$settings = New-ScheduledTaskSettingsSet `');
    ScriptContent.Add('    -ExecutionTimeLimit (New-TimeSpan -Days 0) `');
    ScriptContent.Add('    -RestartCount 3 `');
    ScriptContent.Add('    -RestartInterval (New-TimeSpan -Minutes 1) `');
    ScriptContent.Add('    -AllowStartIfOnBatteries `');
    ScriptContent.Add('    -DontStopIfGoingOnBatteries `');
    ScriptContent.Add('    -MultipleInstances IgnoreNew');
    ScriptContent.Add('');
    ScriptContent.Add('Register-ScheduledTask `');
    ScriptContent.Add('    -TaskName $taskName `');
    ScriptContent.Add('    -Action $action `');
    ScriptContent.Add('    -Trigger $trigger `');
    ScriptContent.Add('    -Settings $settings `');
    ScriptContent.Add('    -Description "{#MyAppServiceDisplayName}" `');
    ScriptContent.Add('    -Force');
    ScriptContent.SaveToFile(ScriptPath);
  finally
    ScriptContent.Free;
  end;

  Exec('powershell.exe',
    '-ExecutionPolicy Bypass -File "' + ScriptPath + '"',
    '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
  DeleteFile(ScriptPath);
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  ConfigFile: String;
  ConfigContent: TStringList;
  NewContent: TStringList;
  I: Integer;
  Line: String;
  SkippingArray: Boolean;
begin
  if CurStep = ssPostInstall then
  begin
    { Update configuration file with user-provided values }
    ConfigFile := ExpandConstant('{userappdata}\{#MyAppDataDir}\config.json');
    
    if FileExists(ConfigFile) then
    begin
      ConfigContent := TStringList.Create;
      NewContent := TStringList.Create;
      try
        ConfigContent.LoadFromFile(ConfigFile);
        SkippingArray := False;
        
        for I := 0 to ConfigContent.Count - 1 do
        begin
          Line := ConfigContent[I];

          { Replace the watch_directories array block }
          if Pos('"watch_directories"', Line) > 0 then
          begin
            NewContent.Add(BuildWatchDirsJson());
            if Pos('[', Line) > 0 then
              SkippingArray := True;
            Continue;
          end;

          { Skip lines inside the old watch_directories array }
          if SkippingArray then
          begin
            if Pos(']', Line) > 0 then
              SkippingArray := False;
            Continue;
          end;

          { Update API key if provided }
          if (ApiKeyPage.Values[0] <> '') and (Pos('"openai_api_key"', Line) > 0) then
          begin
            NewContent.Add('  "openai_api_key": "' + ApiKeyPage.Values[0] + '",');
            Continue;
          end;

          NewContent.Add(Line);
        end;
        
        NewContent.SaveToFile(ConfigFile);
      finally
        ConfigContent.Free;
        NewContent.Free;
      end;
    end;

    { Register auto-start scheduled task }
    RegisterAutoStartTask();
  end;
end;

function InitializeUninstall(): Boolean;
var
  Response: Integer;
begin
  Response := MsgBox('Do you want to keep your configuration and log files?', 
                     mbConfirmation, MB_YESNO);
  
  if Response = IDNO then
  begin
    { User wants to remove everything }
    DelTree(ExpandConstant('{userappdata}\{#MyAppDataDir}'), True, True, True);
  end;
  
  Result := True;
end;

[Messages]
WelcomeLabel2=This will install [name/ver] on your computer.%n%nScanner-Watcher2 is a Windows-native legal document processing system that automatically monitors directories for scanned documents, uses AI to classify them, and organizes files with meaningful names.%n%nYou will need an OpenAI API key to use this application.
FinishedHeadingLabel=Completing the [name] Setup Wizard
FinishedLabel=Scanner-Watcher2 has been installed on your computer and will start automatically when you log in.%n%nBefore first use:%n1. Ensure your watch directories exist%n2. Verify your OpenAI API key is correct%n3. Review the configuration at:%n   %APPDATA%\ScannerWatcher2\config.json%n%nYou can add more watch directories or file prefixes by editing the configuration file.%n%nThe application runs silently in the background. Use Task Manager to verify it is running.
