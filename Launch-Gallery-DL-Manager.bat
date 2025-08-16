@echo off
REM Launch-Gallery-DL-Manager.bat
setlocal ENABLEDELAYEDEXPANSION

set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

if not exist "logs" mkdir "logs"

where py >nul 2>nul
if %ERRORLEVEL%==0 (
  set "PY=py"
) else (
  where python >nul 2>nul
  if %ERRORLEVEL%==0 (
    set "PY=python"
  ) else (
    echo Python not found. Please install Python and ensure it's on PATH.
    pause
    exit /b 1
  )
)

set "MAIN=gallery_dl_manager_v1_0.py"
if not exist "%MAIN%" (
  echo Could not find %MAIN% in "%CD%"
  echo Make sure this .bat sits next to %MAIN%.
  pause
  exit /b 1
)

title Gallery-DL Manager v1.0
echo Starting Gallery-DL Manager...
"%PY%" "%MAIN%"
set EC=%ERRORLEVEL%

if not %EC%==0 (
  echo.
  echo The program exited with errorlevel %EC%.
  echo Check the console output above for details.
  echo.
  pause
)

endlocal
