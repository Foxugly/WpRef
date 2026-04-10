@echo off
setlocal EnableExtensions EnableDelayedExpansion
chcp 65001 >nul

set "ROOT=%~dp0"
if "%ROOT:~-1%"=="\" set "ROOT=%ROOT:~0,-1%"

set "BACKEND=%ROOT%\quizonline-server"
set "FRONTEND=%ROOT%\quizonline-frontend"
set "SYNC_OPENAPI=%ROOT%\scripts\sync-openapi.ps1"
set "PYTHON=%ROOT%\.venv\Scripts\python.exe"
set "ERRORS=0"

echo ============================================================
echo  QUIZONLINE - Verification complete
echo ============================================================
echo.

if not exist "%BACKEND%\manage.py" (
    echo [FAIL] Backend introuvable: "%BACKEND%\manage.py"
    set /a ERRORS+=1
    goto :summary
)

if not exist "%FRONTEND%\package.json" (
    echo [FAIL] Frontend introuvable: "%FRONTEND%\package.json"
    set /a ERRORS+=1
    goto :summary
)

if not exist "%PYTHON%" (
    echo [FAIL] Python du virtualenv introuvable: "%PYTHON%"
    set /a ERRORS+=1
    goto :summary
)

echo [1/5] Tests Django...
pushd "%BACKEND%" >nul
"%PYTHON%" manage.py test --verbosity=1

if errorlevel 1 (
    echo [FAIL] Tests Django
    set /a ERRORS+=1
) else (
    echo [OK]   Tests Django
)
echo.

echo [2/5] Django system check...
"%PYTHON%" manage.py check
if errorlevel 1 (
    echo [FAIL] System check
    set /a ERRORS+=1
) else (
    echo [OK]   System check
)
echo.

echo [3/5] OpenAPI sync and Angular client generation...
popd >nul
powershell -ExecutionPolicy Bypass -File "%SYNC_OPENAPI%"
if errorlevel 1 (
    echo [FAIL] OpenAPI sync / Angular client generation
    set /a ERRORS+=1
) else (
    echo [OK]   OpenAPI synced and Angular client generated
)
echo.

echo [4/5] Angular lint and typecheck...
pushd "%FRONTEND%" >nul
call npm run lint
if errorlevel 1 (
    echo [FAIL] Angular lint
    set /a ERRORS+=1
) else (
    echo [OK]   Lint OK
)

call npm run typecheck
if errorlevel 1 (
    echo [FAIL] Angular typecheck
    set /a ERRORS+=1
) else (
    echo [OK]   Typecheck OK
)
popd >nul
echo.

echo [5/5] Contract note...
echo [INFO] Contract sync script: powershell -ExecutionPolicy Bypass -File "%SYNC_OPENAPI%"
echo.

:summary
echo ============================================================
if !ERRORS! EQU 0 (
    echo  EVERYTHING IS OK - ready to push.
) else (
    echo  !ERRORS! error^(s^) detected - do not push.
)
echo ============================================================
echo  Full E2E: cd /d "%FRONTEND%" ^&^& npm run test:e2e:fullstack
echo.

cd /d "%ROOT%"
pause
