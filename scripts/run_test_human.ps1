# Inicia o servidor e N clientes humanos conforme game.playerNum em config/config.yaml.
# Uso: .\scripts\run_test_human.ps1
# Feche as janelas dos clientes ou pressione Ctrl+C neste terminal para encerrar.

$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

function Get-PythonExe {
    $venvPaths = @(
        (Join-Path $Root ".venv\Scripts\python.exe"),
        (Join-Path $Root "venv\Scripts\python.exe")
    )
    foreach ($path in $venvPaths) {
        if (Test-Path $path) { return $path }
    }
    $system = Get-Command python -ErrorAction SilentlyContinue
    if ($system) { return $system.Source }
    throw "Python não encontrado. Crie o virtualenv (.venv ou venv) e instale as dependências."
}

function Get-PlayerNum {
    $query = @'
import yaml
from pathlib import Path

data = yaml.safe_load(Path("config/config.yaml").read_text(encoding="utf-8"))
print(data["game"]["playerNum"])
'@
    $value = & $Python -c $query
    if ($value -notmatch '^\d+$' -or [int]$value -lt 1) {
        throw "playerNum inválido em config/config.yaml: '$value'"
    }
    return [int]$value
}

$Python = Get-PythonExe
$PlayerNum = Get-PlayerNum
$ServerProcess = $null

try {
    Write-Host "=== Teste: $PlayerNum jogador(es) humano(s) (config/config.yaml) ==="

    Write-Host "Iniciando servidor..."
    $ServerProcess = Start-Process -FilePath $Python `
        -ArgumentList "server.py" `
        -WorkingDirectory $Root `
        -PassThru
    Start-Sleep -Seconds 3

    if ($ServerProcess.HasExited) {
        throw "Erro: servidor encerrou antes de aceitar conexões."
    }

    Write-Host "Iniciando $PlayerNum cliente(s)..."
    1..$PlayerNum | ForEach-Object {
        Start-Process -FilePath $Python `
            -ArgumentList @("client.py", "--player", "human", "--name", "Jogador $_") `
            -WorkingDirectory $Root
        Start-Sleep -Seconds 1
    }

    Write-Host ""
    Write-Host "Servidor (PID $($ServerProcess.Id)) e $PlayerNum cliente(s) em execução."
    Write-Host "Pressione Ctrl+C para encerrar."

    Wait-Process -Id $ServerProcess.Id
}
finally {
    Write-Host ""
    Write-Host "Encerrando teste..."
    if ($ServerProcess -and -not $ServerProcess.HasExited) {
        Stop-Process -Id $ServerProcess.Id -Force -ErrorAction SilentlyContinue
    }
}
