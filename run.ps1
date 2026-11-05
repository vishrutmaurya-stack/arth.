param(
    [switch]$Lan,
    [int]$Port = 8501
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

$python = Join-Path $root ".venv\Scripts\python.exe"
$streamlit = Join-Path $root ".venv\Scripts\streamlit.exe"

if (-not (Test-Path $python)) {
    Write-Host "Creating virtual environment in .venv ..."
    python -m venv .venv
    & $python -m pip install --upgrade pip
    & $python -m pip install -r requirements.txt
}

if (-not (Test-Path (Join-Path $root ".env"))) {
    Write-Warning ".env not found. Copy .env.example to .env and set GROQ_API_KEY."
}

$stArgs = @("run", "app/serve.py", "--server.port", "$Port")
if ($Lan) {
    $stArgs += @("--server.address", "0.0.0.0")
    Write-Host "LAN mode: open http://<your-lan-ip>:$Port from another device."
} else {
    Write-Host "Local mode: open http://localhost:$Port"
}

& $streamlit @stArgs
