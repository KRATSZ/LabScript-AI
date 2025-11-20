#!/usr/bin/env pwsh
# UV Environment Setup Script (PowerShell) - DUAL ENVIRONMENT VERSION

# --- Setup ---
$ProjectRoot = (Get-Item $PSScriptRoot).Parent.FullName
Set-Location -Path $ProjectRoot
Write-Host "Changed working directory to project root: $ProjectRoot" -ForegroundColor Cyan

Write-Host "Setting up Dual-Environment for Opentrons AI Protocol Generator..." -ForegroundColor Green

# --- Check for UV ---
if (!(Get-Command "uv" -ErrorAction SilentlyContinue)) {
    Write-Host "UV not installed, installing..." -ForegroundColor Yellow
    try {
        Invoke-RestMethod https://astral.sh/uv/install.ps1 | Invoke-Expression
        Write-Host "UV installed successfully" -ForegroundColor Green
        $env:PATH = [System.Environment]::GetEnvironmentVariable("PATH", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("PATH", "User")
    } catch {
        Write-Host "UV installation failed: $_" -ForegroundColor Red; exit 1
    }
} else {
    Write-Host "UV already installed. Version: $(uv --version)" -ForegroundColor Green
}

# --- Environment 1: Main App (.venv) ---
Write-Host "`n--- Creating Main Environment (.venv) ---" -ForegroundColor Yellow
uv venv -p 3.11 .venv --seed
if ($LASTEXITCODE -ne 0) { Write-Host "Main environment creation failed" -ForegroundColor Red; exit 1 }

Write-Host "Installing main dependencies into .venv..." -ForegroundColor Blue
# Install the project and its dependencies from pyproject.toml
uv pip install -p .venv/Scripts/python.exe -e .
if ($LASTEXITCODE -ne 0) { Write-Host "Main dependencies installation failed" -ForegroundColor Red; exit 1 }

# --- Environment 2: Opentrons Isolated (.ot_env) ---
Write-Host "`n--- Creating Isolated Opentrons Environment (.ot_env) ---" -ForegroundColor Yellow
uv venv -p 3.11 .ot_env --seed
if ($LASTEXITCODE -ne 0) { Write-Host "Isolated environment creation failed" -ForegroundColor Red; exit 1 }

# Activate and install Opentrons
Write-Host "Installing 'opentrons' into .ot_env..." -ForegroundColor Blue
# Use the python executable from the new venv to install packages
uv pip install -p .ot_env/Scripts/python.exe opentrons==8.4.1
if ($LASTEXITCODE -ne 0) { Write-Host "Opentrons installation failed" -ForegroundColor Red; exit 1 }


# --- Finalization ---
Write-Host "`n✅ Dual-Environment setup completed successfully!" -ForegroundColor Green
Write-Host "You now have two environments:"
Write-Host "  - .venv: For the main application (MCP, LangChain). Activate with '.\.venv\Scripts\Activate.ps1'"
Write-Host "  - .ot_env: For running Opentrons simulations ONLY."
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Activate the MAIN environment: .\.venv\Scripts\Activate.ps1"
Write-Host "2. Start the MCP server: python mcp_server.py"
Write-Host "   (The server will automatically use '.ot_env' for simulations)" 