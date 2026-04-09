@echo off
setlocal EnableExtensions EnableDelayedExpansion
chcp 65001 >nul

set "ROOT=%~dp0"
if "%ROOT:~-1%"=="\" set "ROOT=%ROOT:~0,-1%"

set "BACKEND=%ROOT%\quizonline-server"
set "FRONTEND=%ROOT%\quizonline-frontend"
set "OPENAPI_FILE=%ROOT%\openapi.yaml"
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

echo [1/5] Tests Django...
pushd "%BACKEND%" >nul
python manage.py test --verbosity=1

if errorlevel 1 (
    echo [FAIL] Tests Django
    set /a ERRORS+=1
) else (
    echo [OK]   Tests Django
)
echo.

echo [2/5] Django system check...
python manage.py check
if errorlevel 1 (
    echo [FAIL] System check
    set /a ERRORS+=1
) else (
    echo [OK]   System check
)
echo.

echo [3/5] OpenAPI schema generation...
python manage.py spectacular --file "%OPENAPI_FILE%"
if errorlevel 1 (
    echo [FAIL] OpenAPI schema generation
    set /a ERRORS+=1
) else (
    echo [OK]   OpenAPI schema generated
)
popd >nul
echo.

echo [4/5] Angular client generation...
pushd "%FRONTEND%" >nul
call npx openapi-generator-cli generate -i "..\openapi.yaml" -g typescript-angular -o "src\app\api\generated" --additional-properties=ngVersion=21.0.0,providedIn=root,serviceSuffix=Api,modelSuffix=Dto,stringEnums=true,useSingleRequestParameter=true,fileNaming=kebab-case --inline-schema-name-mappings DomainDetail_translations_value=LocalizedNameDescriptionTranslation,QuestionAnswerOptionRead_translations_value=LocalizedAnswerOptionTranslation,QuestionInSubject_title_value=LocalizedQuestionTitleTranslation,QuestionRead_translations_value=LocalizedQuestionTranslation,SubjectDetail_translations_value=LocalizedSubjectDetailTranslation,SubjectRead_translations_value=LocalizedSubjectTranslation,SubjectRead_translations_value_domain=DomainNameSummary
if errorlevel 1 (
    echo [FAIL] Angular client generation
    set /a ERRORS+=1
) else (
    echo [OK]   Angular client generated
)
echo.

echo [5/5] Angular lint and typecheck...
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
