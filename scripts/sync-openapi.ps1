$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$backendDir = Join-Path $repoRoot "wpref"
$frontendDir = Join-Path $repoRoot "wpref-frontend"
$venvPython = Join-Path $repoRoot ".venv\\Scripts\\python.exe"
$pythonExe = if (Test-Path $venvPython) { $venvPython } else { "python" }
$generatorArgs = @(
    "openapi-generator-cli",
    "generate",
    "-i", "openapi.yaml",
    "-g", "typescript-angular",
    "-o", "src/app/api/generated",
    "--additional-properties=ngVersion21.0.0,providedIn=root,serviceSuffix=Api,modelSuffix=Dto,stringEnums=true,useSingleRequestParameter=true,fileNaming=kebab-case"
)

Push-Location $backendDir
try {
    & $pythonExe manage.py spectacular --file openapi.yaml
    Copy-Item openapi.yaml (Join-Path $frontendDir "openapi.yaml") -Force
}
finally {
    Pop-Location
}

Push-Location $frontendDir
try {
    npx @generatorArgs
}
finally {
    Pop-Location
}
