@echo off
REM apply_schema.bat - Windows companion to apply_schema.sh.
REM
REM Pushes the project's field types and fields via the Schema API.
REM Requires curl (Windows 10+ ships with curl in System32).
setlocal ENABLEDELAYEDEXPANSION

if "%SOLR_PORT%"=="" set SOLR_PORT=8983
if "%CORE_NAME%"=="" set CORE_NAME=books
set BASE=http://localhost:%SOLR_PORT%/solr/%CORE_NAME%

echo Applying field type 'text_suggest'...
curl -X POST -H "Content-type: application/json" "%BASE%/schema" --data-binary "{\"add-field-type\":[{\"name\":\"text_suggest\",\"class\":\"solr.TextField\",\"positionIncrementGap\":\"100\",\"indexAnalyzer\":{\"tokenizer\":{\"class\":\"solr.StandardTokenizerFactory\"},\"filters\":[{\"class\":\"solr.LowerCaseFilterFactory\"},{\"class\":\"solr.EdgeNGramFilterFactory\",\"minGramSize\":\"2\",\"maxGramSize\":\"20\"}]},\"queryAnalyzer\":{\"tokenizer\":{\"class\":\"solr.StandardTokenizerFactory\"},\"filters\":[{\"class\":\"solr.LowerCaseFilterFactory\"}]}}]}"

echo.
echo Adding fields...
curl -X POST -H "Content-type: application/json" "%BASE%/schema" --data-binary "{\"add-field\":[{\"name\":\"title\",\"type\":\"text_general\",\"indexed\":true,\"stored\":true},{\"name\":\"title_str\",\"type\":\"string\",\"indexed\":true,\"stored\":true},{\"name\":\"title_ac\",\"type\":\"text_suggest\",\"indexed\":true,\"stored\":false},{\"name\":\"author\",\"type\":\"text_general\",\"indexed\":true,\"stored\":true},{\"name\":\"author_str\",\"type\":\"string\",\"indexed\":true,\"stored\":true},{\"name\":\"genres\",\"type\":\"strings\",\"indexed\":true,\"stored\":true},{\"name\":\"language\",\"type\":\"string\",\"indexed\":true,\"stored\":true},{\"name\":\"year\",\"type\":\"pint\",\"indexed\":true,\"stored\":true},{\"name\":\"pages\",\"type\":\"pint\",\"indexed\":true,\"stored\":true},{\"name\":\"rating\",\"type\":\"pfloat\",\"indexed\":true,\"stored\":true},{\"name\":\"price\",\"type\":\"pfloat\",\"indexed\":true,\"stored\":true},{\"name\":\"in_stock\",\"type\":\"boolean\",\"indexed\":true,\"stored\":true},{\"name\":\"stock_count\",\"type\":\"pint\",\"indexed\":true,\"stored\":true},{\"name\":\"publisher\",\"type\":\"string\",\"indexed\":true,\"stored\":true},{\"name\":\"isbn\",\"type\":\"string\",\"indexed\":true,\"stored\":true},{\"name\":\"pub_date\",\"type\":\"pdate\",\"indexed\":true,\"stored\":true},{\"name\":\"tags\",\"type\":\"strings\",\"indexed\":true,\"stored\":true},{\"name\":\"description\",\"type\":\"text_general\",\"indexed\":true,\"stored\":true}]}"

echo.
echo Adding copyFields...
curl -X POST -H "Content-type: application/json" "%BASE%/schema" --data-binary "{\"add-copy-field\":[{\"source\":\"title\",\"dest\":[\"_text_\",\"title_str\",\"title_ac\"]},{\"source\":\"author\",\"dest\":[\"_text_\",\"author_str\"]},{\"source\":\"description\",\"dest\":\"_text_\"},{\"source\":\"genres\",\"dest\":\"_text_\"},{\"source\":\"tags\",\"dest\":\"_text_\"}]}"

echo.
echo Schema applied successfully.
endlocal
