@echo off
pushd "%~dp0.."
python -m CodeCAI %*
set EXIT_CODE=%ERRORLEVEL%
popd
exit /b %EXIT_CODE%
