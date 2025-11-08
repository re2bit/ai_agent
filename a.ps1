<#
    PowerShell port of the original `a` bash helper script.
    Usage: .\a.ps <command> [options]

    Notes:
    - This script aims to mirror the commands from the original bash script
      and acts as a thin wrapper around `docker`/`docker compose` invocations.
    - Save as `a.ps` (or `a.ps1`) and run from PowerShell: `./a.ps help` or
      `./a.ps init` etc.
#>

param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$InputArgs
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# Docker command (allow override by env var DOCKER_CMD)
$DOCKER_CMD = if ($env:DOCKER_CMD) { $env:DOCKER_CMD } else { 'docker' }

function Show-Help {
    """" | Out-Host
    Write-Host "a (PowerShell)" -ForegroundColor Cyan
    Write-Host "usage: a COMMAND [OPTIONS]"
    Write-Host ""
    Write-Host "Commands:"
    @(
        'i, init                    Initialize the docker compose or update the images.'
        'b, build                   Build a given Service'
        'bma, build-multi-arch     Build a given Service for multiple Architectures'
        'e, exec                   Execute a command in the given container.'
        's, start-service          Starts a service or all if not specified.'
        'd, stop-service           Stops a service or all if not specified.'
        'l, logs                   Shows the logs for the Service'
        'lf, log-follow            Shows and follows the logs for the Service'
        'm, migrations             Run Alembic migrations commands in the container.'
        'w, watch                  Watch services and rebuild when files change.'
        'ut, unit-test            Execute Unit Tests.'
        'ti, toggle-init          enables/disables init containers'
        'td, toggle-debug         enables/disables debugging for go'
        'dpsw, docker-ps-watch    Watches the Services'
        'rd, reset-database       Resets the Database.'
        'rc, restart-containers   Stops all local containers and starts new ones.'
        'o, open                  Open http://localhost:8080 in the default browser (if available)'
    ) | ForEach-Object { Write-Host "  $_" }
    Write-Host ""
    Write-Host "Hint: a <command> --help for command-specific help"
}

function Check-Dependencies {
    # Check docker
    try {
        & $DOCKER_CMD info > $null 2>&1
    } catch {
        Write-Warning "Docker may not be working correctly"
        $answer = Read-Host "Do you want to continue anyway? (y/N)"
        if ($answer -ne 'y' -and $answer -ne 'Y') { throw "Aborted." }
    }

    # Check git (best effort)
    try {
        & git --version > $null 2>&1
    } catch {
        Write-Warning "Git may not be working correctly"
        $answer = Read-Host "Do you want to continue anyway? (y/N)"
        if ($answer -ne 'y' -and $answer -ne 'Y') { throw "Aborted." }
    }

    # Optional banner image run if .addBanner exists
    if (Test-Path -Path '.addBanner') {
        $IMAGE_NAME = 'a-banner'
        $DOCKERFILE_PATH = './docker/a/Dockerfile'
        try {
            & $DOCKER_CMD image inspect $IMAGE_NAME > $null 2>&1
        } catch {
            Write-Host "Building Service Logo Image"
            & $DOCKER_CMD build -f $DOCKERFILE_PATH -t $IMAGE_NAME .
        }
        try { & $DOCKER_CMD run --rm -t $IMAGE_NAME 2>$null } catch {}
    }
}

function Init {
    [CmdletBinding()]
    param(
        [string]$username,
        [string]$password
    )

    if (-not (Test-Path -Path './.env')) {
        Copy-Item -Path './config/.env' -Destination './.env' -ErrorAction Stop
        Write-Host "Env file created in .env"
    } else {
        Write-Host "./.env already exists, skipping"
    }

    if (-not (Test-Path -Path './compose.override.yml')) {
        Copy-Item -Path './config/compose.override.yml' -Destination './compose.override.yml' -ErrorAction Stop
        Write-Host "Compose Overwrite file created in compose.override.yml"
    } else {
        Write-Host "./compose.override.yml already exists, skipping"
    }
}

function Build { param([string]$Service)
    if (-not $Service) { throw 'Service Name Required' }
    Write-Host "Start Building Service '$Service'"
    & $DOCKER_CMD compose build $Service
}

function Build-Multi-Arch { param([string]$Service)
    if (-not $Service) { throw 'Service Name Required' }
    Write-Host "Start Building Service '$Service' (multi-arch)"
    # Check base image via label using docker compose config
    $configJson = & $DOCKER_CMD compose --profile internal config --format json
    try {
        $j = $configJson | ConvertFrom-Json
        if (-not $j.services.$Service.labels.BaseImage) { throw 'Not base image' }
    } catch {
        Write-Error "Service '$Service' is not a Base Image or could not read compose config"
        return
    }

    # Ensure buildx builder
    $builders = & $DOCKER_CMD buildx ls --format "{{.Name}}" 2>$null
    if ($builders -notmatch 'multi_arch_builder') {
        Write-Host 'Creating multi-arch builder'
        & $DOCKER_CMD buildx create --name multi_arch_builder --use --config buildkitd.toml
    }

    try {
        # In PowerShell you cannot prefix a command with VAR=...; set env var for the command instead
        $oldBuildx = $env:BUILDX_BAKE_ENTITLEMENTS_FS
        $env:BUILDX_BAKE_ENTITLEMENTS_FS = '0'
        $buildxArgs = @('buildx','bake','--set','*.ssh=default',$Service,'--push')
        & $DOCKER_CMD @buildxArgs
    } catch {
        Write-Error "Buildx bake failed for $Service"
        return
    } finally {
        if ($null -ne $oldBuildx) { $env:BUILDX_BAKE_ENTITLEMENTS_FS = $oldBuildx } else { Remove-Item Env:BUILDX_BAKE_ENTITLEMENTS_FS -ErrorAction SilentlyContinue }
    }
    Write-Host "Done Building Service '$Service'"
}

function Exec-Command {
    param(
        [string]$Service,
        [Parameter(ValueFromRemainingArguments=$true)] [string[]]$Cmd
    )
    if (-not $Service -or -not $Cmd) { throw 'usage: a e SERVICE COMMAND' }
    Write-Host "Executing Command '$($Cmd -join ' ') ' in $Service"
    & $DOCKER_CMD compose exec $Service $Cmd
}

function Start-Service {
    param([string]$Service)
    if ($Service) { & $DOCKER_CMD compose up -d $Service } else { & $DOCKER_CMD compose up -d }
}

function Stop-Service {
    param([string]$Service)
    if ($Service) { & $DOCKER_CMD compose down $Service } else { & $DOCKER_CMD compose down }
}

function Show-Logs {
    param([string]$Service)
    if ([string]::IsNullOrEmpty($Service)) {
        # No service specified: show all logs. Suppress compose warnings about unset env vars by redirecting stderr.
        & $DOCKER_CMD compose logs 2>$null
        return
    }

    try { & $DOCKER_CMD compose logs "init-$Service" 2>$null } catch { Write-Warning 'Could not display init logs, skipping' }
    & $DOCKER_CMD compose logs $Service 2>$null
}

function Show-Logs-Follow {
    param([string]$Service)
    Write-Host "Following logs for service: $Service"
    while ($true) {
        if ([string]::IsNullOrEmpty($Service)) {
            & $DOCKER_CMD compose logs --follow 2>$null
        } else {
            & $DOCKER_CMD compose logs --follow $Service 2>$null
        }
    }
}

function Toggle-Init {
    # Toggle lines marked with '# init dependency$' in compose.override.yml
    $path = 'compose.override.yml'
    if (-not (Test-Path $path)) { Write-Warning "$path not found"; return }
    $content = Get-Content $path -Raw
    # If line is commented (# something) remove leading #, otherwise add #
    $new = $content -replace '(?m)^(\s*)#?(.+?# init dependency$)', { param($m) if ($m.Value -match '^[ \t]*#') { return $m.Groups[1].Value + $m.Groups[2].Value } else { return $m.Groups[1].Value + '#' + $m.Groups[2].Value } }
    Set-Content -Path $path -Value $new
    Write-Host 'Toggled init lines in compose.override.yml'
}

function Toggle-Debug {
    # Toggle debug lines in .env (marked with '# debug switch$')
    $path = '.env'
    if (-not (Test-Path $path)) { Write-Warning "$path not found"; return }
    $content = Get-Content $path -Raw
    $new = $content -replace '(?m)^(\s*)#?(.+?# debug switch$)', { param($m) if ($m.Value -match '^[ \t]*#') { return $m.Groups[1].Value + $m.Groups[2].Value } else { return $m.Groups[1].Value + '#' + $m.Groups[2].Value } }
    Set-Content -Path $path -Value $new
    Write-Host 'Toggled debug switch in .env'
    Build 'as'
    Start-Service 'as'
}

function Docker-Metadata {
    @{ SchemaVersion = '0.1.0'; Vendor = 'rene-gerritsen.'; Version = 'v0.0.1'; ShortDescription = 'a - the first ai system i developed' } | ConvertTo-Json
}

function Restart-Containers { & $DOCKER_CMD compose down; & $DOCKER_CMD compose up -d }

function Reset-Database {
    Write-Host 'Finding services with resetableDb label'
    $json = & $DOCKER_CMD compose config --format json
    $obj = $json | ConvertFrom-Json
    $resetable = @()
    foreach ($s in $obj.services.psobject.Properties.Name) {
        $labels = $obj.services.$s.labels
        if ($labels -and $labels.resetableDb) { $resetable += $s }
    }
    if (-not $resetable) { Write-Warning 'No services with resetableDb label found'; return }
    foreach ($service in $resetable) {
        Write-Host "Restarting service: $service"
        & $DOCKER_CMD compose down $service
        & $DOCKER_CMD compose up -d $service
    }
}

function Docker-Ps-Watch {
    Write-Host 'Watching Services'
    while ($true) {
        & $DOCKER_CMD compose ps --format "table {{.Service}}\t{{.Status}}"
        Start-Sleep -Seconds 2
        Clear-Host
    }
}

function Migrations {
    param([Parameter(ValueFromRemainingArguments=$true)] [string[]]$Args)
    Write-Host 'Running Alembic command in agent-server container'
    $running = & $DOCKER_CMD compose ps --services --filter "status=running" | Select-String 'as' -Quiet
    if (-not $running) { & $DOCKER_CMD compose up -d as }
    if ($Args.Count -eq 0) { $Args = @('upgrade','head') }
    & $DOCKER_CMD compose exec -w /app as alembic @Args
}

function Watch {
    param([Parameter(ValueFromRemainingArguments=$true)] [string[]]$Args)
    $DRY='' ; $NO_UP='' ; $NO_PRUNE='' ; $QUIET=''
    $services = @()
    for ($i=0; $i -lt $Args.Count; $i++) {
        switch ($Args[$i]) {
            '--dry-run' { $DRY='--dry-run' }
            '--no-up' { $NO_UP='--no-up' }
            '--no-prune' { $NO_PRUNE='--prune=false' }
            '--quiet' { $QUIET='--quiet' }
            default { $services += $Args[$i] }
        }
    }
    $srv = $services -join ' '
    Write-Host "Starting docker compose watch for services: $srv"
    & $DOCKER_CMD --log-level=debug compose watch $DRY $NO_UP $NO_PRUNE $QUIET $srv
}

function Unit-Test {
    param([Parameter(ValueFromRemainingArguments=$true)] [string[]]$Args)
    $ps = & $DOCKER_CMD ps -q --no-trunc 2>$null
    $composeAs = & $DOCKER_CMD compose ps -q as 2>$null
    if (-not ($ps -and ($ps -match $composeAs))) {
        Write-Host 'Service not running, going to use compose run'
        & $DOCKER_CMD compose run --rm as pytest @Args
    } else {
        Write-Host 'Found running Service, using exec'
        & $DOCKER_CMD compose exec as pytest @Args
    }
}

function Open-Localhost {
    $URL = 'http://localhost:8080'
    Write-Host "Open this URL in your browser: $URL"
    if ($IsMacOS) { & open $URL } elseif (Get-Command 'xdg-open' -ErrorAction SilentlyContinue) { & xdg-open $URL } else { Start-Process $URL }
}

# Entrypoint: parse first argument as command
# Use the script parameter $InputArgs to avoid clashes with local function params named $Args
if (-not $InputArgs -or $InputArgs.Count -eq 0) { Show-Help; exit 0 }

$cmd = $InputArgs[0]
# (no debug)
# Safely extract rest arguments without creating invalid ranges
if ($InputArgs.Count -gt 1) {
    $rest = @()
    for ($i = 1; $i -lt $InputArgs.Count; $i++) { $rest += $InputArgs[$i] }
} else {
    $rest = @()
}
# Precompute first and the rest to avoid indexing errors
$firstArg = if ($rest.Count -ge 1) { $rest[0] } else { $null }
$otherArgs = if ($rest.Count -gt 1) { $rest[1..($rest.Count-1)] } else { @() }

try {
    Check-Dependencies

    switch ($cmd) {
    'i' { Init @rest }
    'init' { Init @rest }
    'b' { Build $firstArg }
    'build' { Build $firstArg }
    'bma' { Build-Multi-Arch $firstArg }
    'build-multi-arch' { Build-Multi-Arch $firstArg }
    'e' { Exec-Command -Service $firstArg -Cmd $otherArgs }
    'exec' { Exec-Command -Service $firstArg -Cmd $otherArgs }
    's' { Start-Service $firstArg }
    'start-service' { Start-Service $firstArg }
    'd' { Stop-Service $firstArg }
    'stop-service' { Stop-Service $firstArg }
    'l' { Show-Logs $firstArg }
    'logs' { Show-Logs $firstArg }
    'lf' { Show-Logs-Follow $firstArg }
    'log-follow' { Show-Logs-Follow $firstArg }
    'm' { Migrations @rest }
    'migrations' { Migrations @rest }
    'w' { Watch @rest }
    'watch' { Watch @rest }
    'ut' { Unit-Test @rest }
    'unit-test' { Unit-Test @rest }
    'ti' { Toggle-Init }
    'toggle-init' { Toggle-Init }
    'td' { Toggle-Debug }
    'toggle-debug' { Toggle-Debug }
    'dpsw' { Docker-Ps-Watch }
    'docker-ps-watch' { Docker-Ps-Watch }
    'docker-cli-plugin-metadata' { Docker-Metadata }
    'rc' { Restart-Containers }
    'restart-containers' { Restart-Containers }
    'rd' { Reset-Database }
    'reset-database' { Reset-Database }
    'o' { Open-Localhost }
    'open' { Open-Localhost }
    '--help' { Show-Help }
    'help' { Show-Help }
    default { Write-Host "'$cmd' is not a known Command." -ForegroundColor Red; Show-Help }
    }

} catch {
    Write-Error $_.Exception.Message
    if ($_.Exception.ScriptStackTrace) { Write-Host $_.Exception.ScriptStackTrace }
    exit 1
}
