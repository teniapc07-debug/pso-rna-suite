; PSO_RNA_Suite.iss
; Script de Inno Setup para crear el instalador de la Suite PSO + RNA.
; Compilar con: ISCC.exe PSO_RNA_Suite.iss

[Setup]
; Un ID único para tu aplicación. NO LO CAMBIES nunca entre versiones.
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName=PSO RNA Suite
AppVersion=0.4.0
AppPublisher=Tu Nombre
AppPublisherURL=https://github.com/tu-usuario/pso-rna-suite
AppSupportURL=https://github.com/tu-usuario/pso-rna-suite/issues
AppUpdatesURL=https://github.com/tu-usuario/pso-rna-suite/releases
; Directorio de instalación por defecto. {autopf} resuelve a Program Files.
DefaultDirName={autopf}\PSO RNA Suite
; El grupo del menú inicio.
DefaultGroupName=PSO RNA Suite
; Descomentar si quieres que se instale en modo "solo para mí".
; PrivilegesRequiredOverridesAllowed=dialog
; Archivo de salida del instalador.
OutputBaseFilename=PSO_RNA_Suite_Installer
; Directorio donde Inno Setup leerá los archivos (el output de PyInstaller).
SourceDir=.
; Compresión.
Compression=lzma2
SolidCompression=yes
; Icono del instalador (opcional).
; SetupIconFile=PSO_RNA_Suite.ico
; Descomentar si quieres que el instalador no requiera permisos de admin.
; PrivilegesRequired=lowest

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
; Tarea para crear un icono en el escritorio.
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Copia recursivamente TODO el contenido de la carpeta dist\PSO_RNA_Suite\
; al directorio de instalación.
Source: "dist\PSO_RNA_Suite\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
; Crea un icono en el menú inicio.
Name: "{group}\PSO RNA Suite"; Filename: "{app}\PSO_RNA_Suite.exe"
Name: "{group}\{cm:UninstallProgram,PSO RNA Suite}"; Filename: "{uninstallexe}"
; Crea un icono en el escritorio si el usuario marcó la tarea.
Name: "{autodesktop}\PSO RNA Suite"; Filename: "{app}\PSO_RNA_Suite.exe"; Tasks: desktopicon

[Run]
; Ofrece ejecutar la aplicación después de instalar.
Filename: "{app}\PSO_RNA_Suite.exe"; Description: "{cm:LaunchProgram,PSO RNA Suite}"; Flags: nowait postinstall skipifsilent

[Code]
// Esta sección de código Pascal es muy útil para verificar dependencias.
function InitializeSetup(): Boolean;
var
  ErrorCode: Integer;
begin
  Result := True;
  // Aquí podrías añadir una comprobación para el VC++ Redistributable
  // usando la función Exec. Por ejemplo:
  // if not Exec('cmd.exe', '/c wmic product where "name like "%%Visual C++ 2015-2022 Redistributable%%" get name', '', SW_HIDE, ewWaitUntilTerminated, ErrorCode) then
  // begin
  //   if MsgBox('Es posible que falte el VC++ Redistributable. ¿Desea continuar?', mbConfirmation, MB_YESNO) = IDNO then
  //     Result := False;
  // end;
end;