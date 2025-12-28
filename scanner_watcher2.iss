; Inno Setup Script for Scanner-Watcher2
; This script creates a professional Windows installer that:
; - Installs the application to Program Files
; - Creates necessary AppData directories
; - Installs and configures the Windows service
; - Creates Start Menu shortcuts
; - Handles clean uninstallation

#define MyAppName "Scanner-Watcher2"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Scanner-Watcher2 Team"
#define MyAppURL "https://github.com/scanner-watcher2"
#define MyAppExeName "scanner_watcher2.exe"
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
OutputDir=dist
OutputBaseFilename=scanner-watcher2-setup-{#MyAppVersion}
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
Name: "{group}\{#MyAppName} Configuration"; Filename: "notepad.exe"; Parameters: """{userappdata}\{#MyAppName}\config.json"""; Comment: "Edit Scanner-Watcher2 configuration"
Name: "{group}\{#MyAppName} Logs"; Filename: "{userappdata}\{#MyAppName}\logs"; Comment: "View Scanner-Watcher2 logs"
Name: "{group}\Start {#MyAppName} Service"; Filename: "{app}\{#MyAppExeName}"; Parameters: "--start-service"; Comment: "Start the Scanner-Watcher2 service"
Name: "{group}\Stop {#MyAppName} Service"; Filename: "{app}\{#MyAppExeName}"; Parameters: "--stop-service"; Comment: "Stop the Scanner-Watcher2 service"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName} Configuration"; Filename: "notepad.exe"; Parameters: """{userappdata}\{#MyAppName}\config.json"""; Tasks: desktopicon; Comment: "Edit Scanner-Watcher2 configuration"

[Run]
; Create AppData directories and copy configuration
Filename: "{cmd}"; Parameters: "/c if not exist ""{userappdata}\{#MyAppName}"" mkdir ""{userappdata}\{#MyAppName}"""; Flags: runhidden
Filename: "{cmd}"; Parameters: "/c if not exist ""{userappdata}\{#MyAppName}\logs"" mkdir ""{userappdata}\{#MyAppName}\logs"""; Flags: runhidden
Filename: "{cmd}"; Parameters: "/c if not exist ""{userappdata}\{#MyAppName}\temp"" mkdir ""{userappdata}\{#MyAppName}\temp"""; Flags: runhidden
Filename: "{cmd}"; Parameters: "/c if not exist ""{userappdata}\{#MyAppName}\config.json"" copy ""{app}\config_template.json"" ""{userappdata}\{#MyAppName}\config.json"""; Flags: runhidden
; Install the Windows service
Filename: "{app}\{#MyAppExeName}"; Parameters: "--install-service"; StatusMsg: "Installing Windows service..."; Flags: runhidden
; Prompt to start service after installation
Filename: "{app}\{#MyAppExeName}"; Parameters: "--start-service"; Description: "Start the {#MyAppServiceDisplayName} now"; Flags: postinstall runhidden skipifsilent

[UninstallRun]
; Stop the service before uninstalling
Filename: "{app}\{#MyAppExeName}"; Parameters: "--stop-service"; Flags: runhidden; RunOnceId: "StopService"
; Remove the Windows service
Filename: "{app}\{#MyAppExeName}"; Parameters: "--remove-service"; Flags: runhidden; RunOnceId: "RemoveService"

[UninstallDelete]
; Clean up temporary files (but preserve logs and configuration)
Type: filesandordirs; Name: "{userappdata}\{#MyAppName}\temp"

[Code]
var
  ConfigPage: TInputQueryWizardPage;
  WatchDirPage: TInputDirWizardPage;
  ApiKeyPage: TInputQueryWizardPage;

procedure InitializeWizard;
begin
  { Create custom wizard page for watch directory }
  WatchDirPage := CreateInputDirPage(wpSelectDir,
    'Select Watch Directory', 'Where should Scanner-Watcher2 monitor for scanned documents?',
    'Select the folder where your scanner saves PDF files, then click Next.',
    False, '');
  WatchDirPage.Add('Watch Directory:');
  WatchDirPage.Values[0] := 'C:\Scans';

  { Create custom wizard page for OpenAI API key }
  ApiKeyPage := CreateInputQueryPage(WatchDirPage.ID,
    'OpenAI API Configuration', 'Enter your OpenAI API key',
    'Scanner-Watcher2 uses OpenAI GPT-4 Vision to classify documents. You need an API key from https://platform.openai.com');
  ApiKeyPage.Add('OpenAI API Key:', True);
  ApiKeyPage.Values[0] := '';
end;

function NextButtonClick(CurPageID: Integer): Boolean;
begin
  Result := True;
  
  { Validate watch directory }
  if CurPageID = WatchDirPage.ID then
  begin
    if WatchDirPage.Values[0] = '' then
    begin
      MsgBox('Please specify a watch directory.', mbError, MB_OK);
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

procedure CurStepChanged(CurStep: TSetupStep);
var
  ConfigFile: String;
  ConfigContent: TStringList;
  I: Integer;
  Line: String;
  WatchDir: String;
begin
  if CurStep = ssPostInstall then
  begin
    { Update configuration file with user-provided values }
    ConfigFile := ExpandConstant('{userappdata}\{#MyAppName}\config.json');
    
    if FileExists(ConfigFile) then
    begin
      ConfigContent := TStringList.Create;
      try
        ConfigContent.LoadFromFile(ConfigFile);
        
        { Prepare watch directory with escaped backslashes }
        WatchDir := EscapeBackslashes(WatchDirPage.Values[0]);
        
        { Update watch directory }
        for I := 0 to ConfigContent.Count - 1 do
        begin
          Line := ConfigContent[I];
          if Pos('"watch_directory"', Line) > 0 then
          begin
            ConfigContent[I] := '  "watch_directory": "' + WatchDir + '",';
          end;
          
          { Update API key if provided }
          if (ApiKeyPage.Values[0] <> '') and (Pos('"openai_api_key"', Line) > 0) then
          begin
            ConfigContent[I] := '  "openai_api_key": "' + ApiKeyPage.Values[0] + '",';
          end;
        end;
        
        ConfigContent.SaveToFile(ConfigFile);
      finally
        ConfigContent.Free;
      end;
    end;
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
    DelTree(ExpandConstant('{userappdata}\{#MyAppName}'), True, True, True);
  end;
  
  Result := True;
end;

[Messages]
WelcomeLabel2=This will install [name/ver] on your computer.%n%nScanner-Watcher2 is a Windows-native legal document processing system that automatically monitors directories for scanned documents, uses AI to classify them, and organizes files with meaningful names.%n%nYou will need an OpenAI API key to use this application.
FinishedHeadingLabel=Completing the [name] Setup Wizard
FinishedLabel=Scanner-Watcher2 has been installed on your computer.%n%nBefore starting the service:%n1. Ensure your watch directory exists%n2. Verify your OpenAI API key is correct%n3. Review the configuration at:%n   %APPDATA%\Scanner-Watcher2\config.json%n%nThe service can be started from the Start Menu or Windows Services Manager.
