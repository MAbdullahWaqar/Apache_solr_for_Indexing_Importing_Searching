@echo off
REM -----------------------------------------------------------------------------
REM setup_solrcloud.bat - Windows companion to setup_solrcloud.sh.
REM
REM Stands up a real SolrCloud cluster on a single Windows host:
REM   - Node 1 on port 8983 (with embedded ZooKeeper on port 9983)
REM   - Node 2 on port 7574 (joins the same ensemble)
REM   - Collection "books" with 2 shards x 2 replicas
REM
REM Usage:
REM   scripts\setup_solrcloud.bat
REM -----------------------------------------------------------------------------
setlocal ENABLEDELAYEDEXPANSION

if "%PORT_1%"==""           set PORT_1=8983
if "%PORT_2%"==""           set PORT_2=7574
if "%ZK_PORT%"==""          set ZK_PORT=9983
if "%COLLECTION%"==""       set COLLECTION=books
if "%NUM_SHARDS%"==""       set NUM_SHARDS=2
if "%REPLICATION_FACTOR%"=="" set REPLICATION_FACTOR=2
if "%ZK_HOST%"==""          set ZK_HOST=localhost:%ZK_PORT%

where solr >nul 2>nul
if errorlevel 1 (
  echo Error: 'solr' not on PATH.
  echo Install Apache Solr 9.x and add solr-X.Y\bin to PATH.
  exit /b 1
)

echo =================================================================
echo  SolrCloud setup
echo    Node 1 port      : %PORT_1%
echo    Node 2 port      : %PORT_2%
echo    Embedded ZK port : %ZK_PORT%
echo    Collection       : %COLLECTION%
echo    Shards x Replicas: %NUM_SHARDS% x %REPLICATION_FACTOR%
echo =================================================================

echo [1/4] Starting node 1 in cloud mode on port %PORT_1%...
curl -fsS http://localhost:%PORT_1%/solr/admin/info/system >nul 2>nul
if errorlevel 1 (
  call solr start -c -p %PORT_1%
) else (
  echo       Node 1 already running on %PORT_1%.
)

timeout /t 2 /nobreak >nul

echo [2/4] Starting node 2 on port %PORT_2%, joining ZK %ZK_HOST%...
curl -fsS http://localhost:%PORT_2%/solr/admin/info/system >nul 2>nul
if errorlevel 1 (
  call solr start -c -p %PORT_2% -z %ZK_HOST%
) else (
  echo       Node 2 already running on %PORT_2%.
)

echo [3/4] Creating collection '%COLLECTION%' (idempotent)...
curl -fsS "http://localhost:%PORT_1%/solr/admin/collections?action=clusterstatus&wt=json" | findstr "\"%COLLECTION%\"" >nul
if errorlevel 1 (
  call solr create_collection -c %COLLECTION% -shards %NUM_SHARDS% -replicationFactor %REPLICATION_FACTOR% -p %PORT_1%
) else (
  echo       Collection '%COLLECTION%' already exists, skipping.
)

echo [4/4] Cluster status:
curl -fsS "http://localhost:%PORT_1%/solr/admin/collections?action=clusterstatus&wt=json"

echo.
echo Done.
echo   Admin UI (node 1) : http://localhost:%PORT_1%/solr/#/~cloud?view=graph
echo   Admin UI (node 2) : http://localhost:%PORT_2%/solr/#/~cloud?view=graph
echo.
echo Next steps:
echo   scripts\install_resources.bat   ^&^& push synonyms/stopwords to ZK
echo   scripts\apply_schema.bat        ^&^& add field types ^& fields
echo   scripts\index_data.bat          ^&^& ingest dataset
endlocal
