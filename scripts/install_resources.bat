@echo off
REM -----------------------------------------------------------------------------
REM install_resources.bat - Windows companion to install_resources.sh.
REM
REM Pushes synonyms.txt and stopwords.txt into Solr.
REM   * Cloud mode -> uses `solr zk cp` to push into ZooKeeper
REM   * Standalone -> copies into the core's conf/ directory
REM Then reloads the collection/core.
REM
REM Required env vars (with defaults):
REM   SOLR_PORT  (default 8983)
REM   CORE_NAME  (default books)
REM   ZK_HOST    (default localhost:9983)
REM -----------------------------------------------------------------------------
setlocal ENABLEDELAYEDEXPANSION

if "%SOLR_PORT%"=="" set SOLR_PORT=8983
if "%CORE_NAME%"=="" set CORE_NAME=books
if "%ZK_HOST%"==""   set ZK_HOST=localhost:9983

set ROOT=%~dp0..
set RES_DIR=%ROOT%\solr-config
set SYN_FILE=%RES_DIR%\synonyms.txt
set STOP_FILE=%RES_DIR%\stopwords.txt
set BASE=http://localhost:%SOLR_PORT%/solr

if not exist "%SYN_FILE%" (
  echo Error: missing %SYN_FILE%
  exit /b 1
)
if not exist "%STOP_FILE%" (
  echo Error: missing %STOP_FILE%
  exit /b 1
)

REM --- Detect cloud vs standalone -----------------------------------------
set MODE=standalone
curl -fsS "%BASE%/admin/info/system" 2>nul | findstr /C:"\"mode\":\"solrcloud\"" >nul
if not errorlevel 1 set MODE=cloud
curl -fsS "%BASE%/admin/info/system" 2>nul | findstr /C:"zkHost" >nul
if not errorlevel 1 set MODE=cloud

echo Detected Solr mode: %MODE%

if /I "%MODE%"=="cloud" (
  echo Pushing resources into ZK at /configs/%CORE_NAME%/
  call solr zk cp "file:%SYN_FILE%"  "zk:/configs/%CORE_NAME%/synonyms.txt"  -z %ZK_HOST%
  call solr zk cp "file:%STOP_FILE%" "zk:/configs/%CORE_NAME%/stopwords.txt" -z %ZK_HOST%
  echo Reloading collection '%CORE_NAME%'...
  curl -fsS "%BASE%/admin/collections?action=RELOAD&name=%CORE_NAME%&wt=json"
  exit /b 0
)

REM --- Standalone: ask Solr where the core lives --------------------------
for /f "delims=" %%I in ('curl -fsS "%BASE%/admin/cores?action=STATUS^&core=%CORE_NAME%^&wt=json" ^| python -c "import json,sys; d=json.load(sys.stdin); print(d['status'].get('%CORE_NAME%',{}).get('instanceDir',''))"') do set INSTANCE_DIR=%%I

if "%INSTANCE_DIR%"=="" (
  echo Could not determine instanceDir for core '%CORE_NAME%'.
  echo Make sure Solr is running and the core exists.
  exit /b 1
)

set CONF_DIR=%INSTANCE_DIR%\conf
if not exist "%CONF_DIR%" mkdir "%CONF_DIR%"

echo Copying resources to %CONF_DIR%
copy /Y "%SYN_FILE%"  "%CONF_DIR%\synonyms.txt"
copy /Y "%STOP_FILE%" "%CONF_DIR%\stopwords.txt"

echo Reloading core '%CORE_NAME%'...
curl -fsS "%BASE%/admin/cores?action=RELOAD&core=%CORE_NAME%&wt=json"
echo Done.
endlocal
