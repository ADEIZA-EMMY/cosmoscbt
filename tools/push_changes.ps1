param(
    [string]$Message = "Update: pushed changes",
    [switch]$Force
)

# Move to repo root (assumes this script lives in tools/)
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location (Join-Path $scriptDir "..")

Write-Host "Repository path: $(Get-Location)" -ForegroundColor Cyan

# Get current branch
$branch = (git rev-parse --abbrev-ref HEAD) -split "\n" | Select-Object -First 1
if (-not $branch) { Write-Error "Failed to detect git branch."; exit 1 }
Write-Host "Current branch: $branch"

# Stage changes
git add -A

# Commit if there are staged changes
$status = git status --porcelain
if ($status -eq "") {
    Write-Host "No changes to commit."
} else {
    git commit -m "$Message"
    if ($LASTEXITCODE -ne 0) {
        Write-Error "git commit failed."; exit 2
    }
}

# Push to origin
Write-Host "Pushing to origin/$branch..."
git push origin $branch
if ($LASTEXITCODE -ne 0) { Write-Error "Push to origin failed."; exit 3 }

# If a Heroku remote exists, push to Heroku (deploy)
$remotes = git remote
if ($remotes -match '\bheroku\b') {
    Write-Host "Heroku remote found — pushing to Heroku (deploying current HEAD to main)..." -ForegroundColor Yellow
    git push heroku HEAD:main
    if ($LASTEXITCODE -ne 0) { Write-Warning "Push to Heroku failed. Check remote configuration and credentials." }
} else {
    Write-Host "No Heroku remote configured. Skipping Heroku push." -ForegroundColor Gray
}

Write-Host "Done." -ForegroundColor Green
