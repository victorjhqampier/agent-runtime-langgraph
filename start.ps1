$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectRoot

if (Test-Path ".env") {
    Copy-Item -Force ".env" "src/.env"
}

$UvArgs = @("--from", "uv", "uv")

& uvx @UvArgs run uvicorn Presentation.app:app --app-dir src --reload --host 0.0.0.0 --port 8000
