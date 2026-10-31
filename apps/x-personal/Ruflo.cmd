@echo off
setlocal
for %%I in ("%~dp0..\..") do set "WORKSPACE_ROOT=%%~fI"
set "RUFLO_CLI=%WORKSPACE_ROOT%\runtime\ruflo-3.61.1\node_modules\ruflo\bin\ruflo.js"
if not exist "%RUFLO_CLI%" (
  echo Ruflo 3.61.1 is missing. See INTEGRATIONS_AR.md.
  exit /b 1
)
where node >nul 2>nul
if errorlevel 1 (
  echo Node.js 20 or newer is required to run Ruflo.
  exit /b 1
)
pushd "%WORKSPACE_ROOT%"
if errorlevel 1 exit /b 1
node "%RUFLO_CLI%" %*
set "RUFLO_EXIT=%ERRORLEVEL%"
popd
exit /b %RUFLO_EXIT%
