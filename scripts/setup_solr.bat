@echo off
REM -----------------------------------------------------------------------------
REM setup_solr.bat
REM Windows companion to setup_solr.sh.
REM
REM Usage:
REM   scripts\setup_solr.bat
REM   set SOLR_PORT=8984 && scripts\setup_solr.bat
REM -----------------------------------------------------------------------------
setlocal ENABLEDELAYEDEXPANSION

if "%SOLR_PORT%"=="" set SOLR_PORT=8983
if "%CORE_NAME%"=="" set CORE_NAME=books
set SOLR_URL=http://localhost:%SOLR_PORT%

where solr >nul 2>nul
if errorlevel 1 (
  echo Error: 'solr' not on PATH.
  echo Install Apache Solr 9.x and add solr-X.Y\bin to PATH.
  exit /b 1
)

echo [1/4] Starting Solr on port %SOLR_PORT%...
curl -fsS %SOLR_URL%/solr/admin/info/system >nul 2>nul
if errorlevel 1 (
  call solr start --user-managed -p %SOLR_PORT%
) else (
  echo       Solr already running on %SOLR_PORT%.
)

echo [2/4] Creating core '%CORE_NAME%' (idempotent)...
curl -fsS "%SOLR_URL%/solr/admin/cores?action=STATUS&core=%CORE_NAME%" | findstr "\"name\":\"%CORE_NAME%\"" >nul
if errorlevel 1 (
  call solr create -c %CORE_NAME% -p %SOLR_PORT%
) else (
  echo       Core '%CORE_NAME%' already exists, skipping.
)

echo [3/4] Installing synonyms.txt + stopwords.txt...
call "%~dp0install_resources.bat"

echo [4/4] Applying project schema via Schema API...
call "%~dp0apply_schema.bat"

echo.
echo Done. Admin UI: %SOLR_URL%/solr/#/%CORE_NAME%
echo Next: scripts\index_data.bat       ^&^& ingest the dataset
endlocal
