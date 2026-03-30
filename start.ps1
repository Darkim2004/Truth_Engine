Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-Step {
    param([string]$Message)
    Write-Host "[START] $Message" -ForegroundColor Cyan
}

function Get-BootstrapPython {
    if (Get-Command py -ErrorAction SilentlyContinue) {
        return "py"
    }

    if (Get-Command python -ErrorAction SilentlyContinue) {
        return "python"
    }

    throw "Python launcher not found. Install Python 3.11+ and ensure 'py' or 'python' is on PATH."
}

function Read-ApiKey {
    while ($true) {
        $secure = Read-Host "Insert your Groq API key (gsk_...)" -AsSecureString
        $bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
        try {
            $plain = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr)
        }
        finally {
            if ($bstr -ne [IntPtr]::Zero) {
                [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)
            }
        }

        if (-not [string]::IsNullOrWhiteSpace($plain)) {
            return $plain.Trim()
        }

        Write-Host "The API key cannot be empty. Please try again." -ForegroundColor Yellow
    }
}

function Set-EnvVarLine {
    param(
        [string]$FilePath,
        [string]$Name,
        [string]$Value
    )

    if (-not (Test-Path $FilePath)) {
        Set-Content -Path $FilePath -Value "" -Encoding utf8
    }

    $content = Get-Content -Path $FilePath -Encoding utf8
    $pattern = "^$([Regex]::Escape($Name))="
    $updated = $false

    for ($i = 0; $i -lt $content.Count; $i++) {
        if ($content[$i] -match $pattern) {
            $content[$i] = "$Name=$Value"
            $updated = $true
            break
        }
    }

    if (-not $updated) {
        $content += "$Name=$Value"
    }

    Set-Content -Path $FilePath -Value $content -Encoding utf8
}

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

$envFile = Join-Path $root ".env"
$existingKey = ""

if (Test-Path $envFile) {
    $match = Select-String -Path $envFile -Pattern "^GROQ_API_KEY=(.*)$" -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($match) {
        $existingKey = $match.Matches[0].Groups[1].Value.Trim()
    }
}

Write-Step "Groq API key setup"
$apiKey = $existingKey
if ([string]::IsNullOrWhiteSpace($existingKey)) {
    $apiKey = Read-ApiKey
    Set-EnvVarLine -FilePath $envFile -Name "GROQ_API_KEY" -Value $apiKey
    Write-Host "Saved GROQ_API_KEY in .env" -ForegroundColor Green
}
else {
    $change = Read-Host "A GROQ_API_KEY already exists in .env. Overwrite it? (y/N)"
    if ($change -match "^(y|yes)$") {
        $apiKey = Read-ApiKey
        Set-EnvVarLine -FilePath $envFile -Name "GROQ_API_KEY" -Value $apiKey
        Write-Host "Updated GROQ_API_KEY in .env" -ForegroundColor Green
    }
    else {
        Write-Host "Keeping current GROQ_API_KEY from .env" -ForegroundColor Green
    }
}

$venvPath = Join-Path $root ".venv"
$venvPython = Join-Path $venvPath "Scripts\python.exe"
$bootstrapPython = Get-BootstrapPython

Write-Step "Virtual environment check"
if (-not (Test-Path $venvPython)) {
    Write-Host "Creating .venv..." -ForegroundColor Cyan
    & $bootstrapPython -m venv $venvPath
}
else {
    Write-Host ".venv already present" -ForegroundColor Green
}

if (-not (Test-Path $venvPython)) {
    throw "Virtual environment was not created correctly."
}

Write-Step "Upgrading pip"
& $venvPython -m pip install --upgrade pip

Write-Step "Installing dependencies from requirements.txt"
& $venvPython -m pip install -r requirements.txt

Write-Step "Installing Playwright browser"
& $venvPython -m playwright install

Write-Step "Starting app.py on http://127.0.0.1:5001"
& $venvPython app.py
