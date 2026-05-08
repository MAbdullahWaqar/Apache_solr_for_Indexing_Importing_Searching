@echo off
REM index_data.bat - Windows companion to index_data.sh.
REM
REM Indexes data\books.json (default) or data\books.csv (set FORMAT=csv).
setlocal ENABLEDELAYEDEXPANSION

if "%SOLR_PORT%"=="" set SOLR_PORT=8983
if "%CORE_NAME%"=="" set CORE_NAME=books
if "%FORMAT%"=="" set FORMAT=json
set BASE=http://localhost:%SOLR_PORT%/solr/%CORE_NAME%

set ROOT=%~dp0..
set DATA=%ROOT%\data

if /I "%FORMAT%"=="json" (
  set FILE=%DATA%\books.json
  echo Indexing %%FILE%% as JSON...
  curl -X POST -H "Content-type: application/json" --data-binary "@!FILE!" "%BASE%/update/json/docs?commit=true"
) else if /I "%FORMAT%"=="csv" (
  set FILE=%DATA%\books.csv
  echo Indexing %%FILE%% as CSV...
  curl -X POST -H "Content-type: application/csv" --data-binary "@!FILE!" "%BASE%/update?commit=true&f.genres.split=true&f.genres.separator=%%3B&f.tags.split=true&f.tags.separator=%%3B"
) else (
  echo Unknown FORMAT=%FORMAT% (expected json or csv).
  exit /b 1
)

echo.
echo Verifying document count...
curl "%BASE%/select?q=*:*&rows=0"
endlocal
