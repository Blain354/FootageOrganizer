@echo off
REM ============================================================================
REM SHOW_FILE_METADATA.BAT
REM 
REM Wrapper Windows pour show_file_metadata.py
REM Facilite l'affichage des métadonnées d'un fichier
REM
REM Usage:
REM   SHOW_FILE_METADATA.BAT "path\to\file.mp4"
REM   SHOW_FILE_METADATA.BAT "path\to\file.mp4" --json
REM   SHOW_FILE_METADATA.BAT "path\to\file.mp4" --save
REM   
REM Ou glisser-déposer un fichier sur ce script
REM ============================================================================

setlocal EnableDelayedExpansion

REM Obtenir le répertoire du script
set SCRIPT_DIR=%~dp0
set SCRIPT_DIR=%SCRIPT_DIR:~0,-1%

REM Chemin vers le script Python
set PYTHON_SCRIPT=%SCRIPT_DIR%\debug\show_file_metadata.py

REM Vérifier si Python est disponible
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ❌ Erreur: Python n'est pas installé ou pas dans le PATH
    echo.
    echo Veuillez installer Python 3.8+ depuis: https://www.python.org/
    echo.
    pause
    exit /b 1
)

REM Vérifier si le script Python existe
if not exist "%PYTHON_SCRIPT%" (
    echo.
    echo ❌ Erreur: Script Python introuvable: %PYTHON_SCRIPT%
    echo.
    pause
    exit /b 1
)

REM Vérifier si un fichier a été fourni
if "%~1"=="" (
    echo.
    echo ╔════════════════════════════════════════════════════════════════════════╗
    echo ║                   SHOW FILE METADATA - Afficheur de Métadonnées        ║
    echo ╚════════════════════════════════════════════════════════════════════════╝
    echo.
    echo Usage:
    echo   %~nx0 "path\to\file.mp4"
    echo   %~nx0 "path\to\file.mp4" --json
    echo   %~nx0 "path\to\file.mp4" --save
    echo.
    echo Ou glisser-déposer un fichier sur ce script
    echo.
    echo Options:
    echo   --json              Sortie en format JSON
    echo   --save              Sauvegarder dans un fichier .metadata.txt
    echo   --footage-raw PATH  Chemin vers Footage_raw pour détection de source
    echo   --tz TIMEZONE       Timezone pour conversion drone
    echo.
    echo Exemples:
    echo   %~nx0 "F:\Project\video.mp4"
    echo   %~nx0 "F:\Project\video.mp4" --json
    echo   %~nx0 "F:\Project\drone\DJI_0001.mp4" --footage-raw "F:\Project\Footage_raw"
    echo.
    pause
    exit /b 1
)

REM Construire la commande
set FILE_PATH=%~1
set EXTRA_ARGS=%2 %3 %4 %5 %6 %7 %8 %9

echo.
echo ╔════════════════════════════════════════════════════════════════════════╗
echo ║                   SHOW FILE METADATA - Analyse en cours                ║
echo ╚════════════════════════════════════════════════════════════════════════╝
echo.
echo 📁 Fichier: %~nx1
echo 📂 Chemin:  %FILE_PATH%
echo.

REM Exécuter le script Python
python "%PYTHON_SCRIPT%" "%FILE_PATH%" %EXTRA_ARGS%

set EXIT_CODE=%ERRORLEVEL%

echo.
if %EXIT_CODE% EQU 0 (
    echo ✅ Analyse terminée avec succès
) else (
    echo ❌ Erreur lors de l'analyse (code: %EXIT_CODE%^)
)
echo.
pause

exit /b %EXIT_CODE%
