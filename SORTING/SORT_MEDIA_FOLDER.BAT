@echo off
REM ========================================================================
REM SORT_MEDIA_FOLDER.BAT
REM 
REM Windows batch script to automate complete video footage organization
REM process with DaVinci Resolve workflow.
REM
REM Functions:
REM - Checks for Gyroflow installation and offers stabilization
REM - Processes video files (.mp4, .mov, .avi, .mkv, etc.) in multiple specified source folders with Gyroflow
REM - Supports comma-separated or space-separated folder lists
REM - Executes organize_footage_links.py to organize by date (prioritizes _stabilized files)
REM - Runs transfer_organized_footage.py to transfer real files  
REM - Prepares structure for create_metadata.py and DaVinci tagging
REM
REM Usage:
REM     SORT_MEDIA_FOLDER.BAT "C:\path\to\projet_example"
REM
REM Prerequisites:
REM - Project folder containing Footage_raw/ subfolder
REM - Python scripts in F:\Utils\script_triage\
REM - Python installed and accessible in PATH
REM - Gyroflow (optional) for stabilization
REM
REM Configuration:
REM - Modify TIMEZONE variable below to change timezone for drone timestamps
REM - Default: America/Montreal
REM - Use format: Continent/City (e.g., Europe/Paris, America/New_York)
REM
REM Output:
REM - Footage_metadata_sorted/ folder with placeholders
REM - Footage/ folder with files organized by date
REM ========================================================================

setlocal enabledelayedexpansion
set TARGET_PATH=%1
set TIMEZONE=America/Guatemala

REM Define supported video extensions for Gyroflow stabilization
set VIDEO_EXTENSIONS=.mp4 .mov .m4v .avi .mkv .mts .m2ts .wmv .3gp .mpg .mpeg .insv .360

if "%TARGET_PATH%"=="" (
    echo Usage: %0 "path_to_folder"
    exit /b 1
)

REM Go to the directory where the scripts are located
cd /d F:\Utils\script_triage\SORTING

echo === Starting organization process ===
echo Target project: %TARGET_PATH%
echo Timezone: %TIMEZONE%
echo.

REM Check if Gyroflow is installed
echo [0/4] Checking for Gyroflow...
where gyroflow >nul 2>&1
if %errorlevel%==0 (
    echo Gyroflow found! Stabilization option available.
    echo.
    echo Examples: 'avata' or 'avata,gopro' or 'drone gopro osmo'
    set /p STABILIZE_FOLDERS="Enter folder name(s) to stabilize (comma or space separated) or press Enter to skip: "
    if not "!STABILIZE_FOLDERS!"=="" (
        REM Replace commas with spaces for uniform processing
        set "STABILIZE_FOLDERS=!STABILIZE_FOLDERS:,= !"
        
        echo Running stabilization on folders: !STABILIZE_FOLDERS!
        echo.
        
        REM Process each folder
        for %%d in (!STABILIZE_FOLDERS!) do (
            set "FOLDER_NAME=%%d"
            REM Remove any extra spaces
            set "FOLDER_NAME=!FOLDER_NAME: =!"
            if not "!FOLDER_NAME!"=="" (
                echo === Processing folder: !FOLDER_NAME! ===
                set SOURCE_PATH=%TARGET_PATH%\Footage_raw\!FOLDER_NAME!
                
                if exist "!SOURCE_PATH!" (
                    echo Processing video files in: !SOURCE_PATH!
                    set /a TOTAL_FILES=0
                    set /a PROCESSED_FILES=0
                    
                    REM Count total video files (excluding already stabilized ones)
                    for %%f in ("!SOURCE_PATH!\*.*") do (
                        if exist "%%f" (
                            REM Check if file has supported video extension
                            call :IsVideoFile "%%f" IS_VIDEO
                            if !IS_VIDEO! EQU 1 (
                                set "TEMP_FILENAME=%%~nf"
                                echo !TEMP_FILENAME! | findstr /i "_stabilized" >nul
                                if !errorlevel! NEQ 0 (
                                    set /a TOTAL_FILES+=1
                                )
                            )
                        )
                    )
                    
                    if !TOTAL_FILES! GTR 0 (
                        echo Found !TOTAL_FILES! video files to process in !FOLDER_NAME!...
                        echo.
                        
                        REM Process each video file
                        for %%f in ("!SOURCE_PATH!\*.*") do (
                            if exist "%%f" (
                                REM Check if file has supported video extension
                                call :IsVideoFile "%%f" IS_VIDEO
                                if !IS_VIDEO! EQU 1 (
                                    REM Check if file contains _stabilized anywhere - skip it
                                    set "FILENAME=%%~nf"
                                    echo !FILENAME! | findstr /i "_stabilized" >nul
                                    if !errorlevel! EQU 0 (
                                        echo   - Skipping already stabilized file: %%~nxf
                                    ) else (
                                        set /a PROCESSED_FILES+=1
                                        echo [!PROCESSED_FILES!/!TOTAL_FILES!] Processing: %%~nxf
                                    
                                    REM Check if stabilized version already exists
                                    set "STABILIZED_FILE=%%~dpnf_stabilized%%~xf"
                                    if exist "!STABILIZED_FILE!" (
                                        echo   - Stabilized version exists, will overwrite
                                    )
                                    echo   - Running Gyroflow stabilization...
                                    gyroflow "%%f" -t "_stabilized"
                                    if !errorlevel! EQU 0 (
                                        if exist "!STABILIZED_FILE!" (
                                            echo   - ✓ Successfully stabilized
                                        ) else (
                                            echo   - ⚠ No gyro data found, skipping
                                        )
                                    ) else (
                                        echo   - ⚠ Gyroflow failed, continuing with next file
                                    )
                                )
                                echo.
                                )
                            )
                        )
                        echo Stabilization completed for folder: !FOLDER_NAME!
                    ) else (
                        echo No video files found in: !SOURCE_PATH!
                    )
                    echo.
                ) else (
                    echo Error: Folder not found: !SOURCE_PATH!
                    echo.
                )
            )
        )
        echo === All stabilization processes completed! ===
        echo === All stabilization processes completed! ===
        echo.
    ) else (
        echo Skipping stabilization.
        echo.
    )
) else (
    echo Gyroflow not found in PATH - skipping stabilization option.
    echo.
)

REM Clean up previous organization if exists
echo Checking for existing organization folder...
if exist "%TARGET_PATH%\Footage_metadata_sorted" (
    echo Removing existing Footage_metadata_sorted folder to prevent conflicts...
    rmdir /s /q "%TARGET_PATH%\Footage_metadata_sorted"
    if exist "%TARGET_PATH%\Footage_metadata_sorted" (
        echo Warning: Could not completely remove existing folder. Some files may be in use.
        echo Please close any programs using files in this folder and try again.
        pause
        exit /b 1
    )
    echo ✓ Previous organization folder removed successfully.
) else (
    echo ✓ No existing organization folder found.
)
echo.

echo [1/4] Organizing files by date (including photos)...
python organize_footage_links.py "%TARGET_PATH%" --include-photos --tz "%TIMEZONE%"
if errorlevel 1 (
    echo Error during file organization
    exit /b %errorlevel%
)
echo [1.5/4] Verify generated structure before continuing...
echo.
set /p _CONTINUE="Press Enter to continue or type N then Enter to abort: "
if /i "%_CONTINUE%"=="N" (
    echo Aborting by user request. No transfer will be performed.
    pause
    exit /b 0
)
echo Continuing with transfer...
echo.

echo [2/4] Transferring video files...
python transfer_organized_footage.py "%TARGET_PATH%" --copy
if errorlevel 1 (
    echo Error during file transfer
    exit /b %errorlevel%
)

echo Creating music directory...
if not exist "%TARGET_PATH%\Footage\music" (
    mkdir "%TARGET_PATH%\Footage\music"
    echo Created: %TARGET_PATH%\Footage\music
) else (
    echo Music directory already exists: %TARGET_PATH%\Footage\music
)

echo [3/4] Generating metadata...
python create_metadata.py "%TARGET_PATH%"
if errorlevel 1 (
    echo Error during metadata generation
    exit /b %errorlevel%
)

echo.
echo === PROCESS COMPLETED SUCCESSFULLY ===
echo.
echo Next steps:
echo 1. Copy TagFootageByCSV.py to DaVinci Resolve/Fusion/Scripts/Utility/
echo 2. Import Footage/ folder in DaVinci Resolve
echo 3. Run TagFootageByCSV script from Workspace ^> Scripts ^> Utility
echo.
echo Created structure:
echo - %TARGET_PATH%\Footage_metadata_sorted\ : Organized placeholders
echo - %TARGET_PATH%\Footage\ : Video files + metadata.csv
echo - %TARGET_PATH%\Footage\music\ : Directory for audio files
echo.
endlocal
pause
exit /b 0

REM Function to check if file has supported video extension
REM Usage: call :IsVideoFile "filename.ext" result_var
:IsVideoFile
set "file_ext=%~x1"
set "%2=0"
for %%e in (%VIDEO_EXTENSIONS%) do (
    if /i "!file_ext!"=="%%e" set "%2=1"
)
goto :eof
