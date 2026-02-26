# PowerShell script to reset PostgreSQL postgres user password on Windows

# Stop PostgreSQL service
Write-Host "Stopping PostgreSQL service..." -ForegroundColor Cyan
Stop-Service -Name postgresql-x64-17 -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2

# Find PostgreSQL installation directory
$pgPath = "C:\Program Files\PostgreSQL\17\bin"
if (-not (Test-Path $pgPath)) {
    $pgPath = "C:\Program Files (x86)\PostgreSQL\17\bin"
}
if (-not (Test-Path $pgPath)) {
    Write-Host "PostgreSQL bin directory not found. Please enter the path:" -ForegroundColor Yellow
    $pgPath = Read-Host "Enter PostgreSQL bin path"
}

Write-Host "Using PostgreSQL path: $pgPath" -ForegroundColor Green

# Get the data directory
$dataDir = "C:\Program Files\PostgreSQL\17\data"
if (-not (Test-Path $dataDir)) {
    $dataDir = "C:\Program Files (x86)\PostgreSQL\17\data"
}

Write-Host "Using data directory: $dataDir" -ForegroundColor Green

# Start PostgreSQL in single-user mode
Write-Host "Starting PostgreSQL in single-user mode..." -ForegroundColor Cyan
& "$pgPath\postgres.exe" --single -D $dataDir postgres

# The above command will drop you into a psql-like prompt
# Run these commands:
# ALTER USER postgres WITH PASSWORD 'newpassword';
# \q

Write-Host "`nPostgreSQL single-user mode started. Enter commands above:" -ForegroundColor Yellow
Write-Host "1. ALTER USER postgres WITH PASSWORD 'postgres123';" -ForegroundColor Yellow
Write-Host "2. \q (to exit)" -ForegroundColor Yellow

# Restart PostgreSQL service normally
Write-Host "`nRestarting PostgreSQL service..." -ForegroundColor Cyan
Start-Service -Name postgresql-x64-17 -ErrorAction SilentlyContinue
Start-Sleep -Seconds 3

Write-Host "PostgreSQL service restarted." -ForegroundColor Green
Write-Host "Try connecting with: psql -U postgres -h localhost" -ForegroundColor Green
Write-Host "Password: postgres123" -ForegroundColor Green
