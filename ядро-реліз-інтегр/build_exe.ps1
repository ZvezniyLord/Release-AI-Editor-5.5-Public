$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

$pythonCandidates = @(
  (Join-Path $root ".venv\Scripts\python.exe"),
  (Join-Path (Split-Path -Parent $root) ".venv\Scripts\python.exe"),
  (Join-Path (Split-Path -Parent (Split-Path -Parent $root)) ".venv\Scripts\python.exe")
)
$python = $pythonCandidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
if (-not $python) {
  $python = "python"
}

& $python -m PyInstaller `
  --noconfirm `
  --clean `
  --onedir `
  --windowed `
  --name ReleaseAIEditor `
  launcher.py `
  --add-data "assets;assets" `
  --add-data "core;core" `
  --add-data "dashboard_core;dashboard_core" `
  --add-data "draft_core;draft_core" `
  --add-data "shared;shared" `
  --add-data "shapka_core;shapka_core" `
  --add-data "toc_core;toc_core" `
  --add-data "resources;resources" `
  --add-data "launcher_state.json;." `
  --hidden-import pythoncom `
  --hidden-import pywintypes `
  --collect-submodules win32com
