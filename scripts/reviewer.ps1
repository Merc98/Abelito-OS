# -----------------------------------------------------
# ABEL OS+ Reviewer Agent Script
# This orchestrates the static analysis, tests, and verifications
# required by the "Reviewer / Verifier" role.
# -----------------------------------------------------

Write-Host ">>> ABEL OS+ REVIEWER / VERIFIER <<<" -ForegroundColor Cyan

# 1. Type Checking
Write-Host "`n[Reviewer] Running Static Type Analysis (Pyright)..." -ForegroundColor Yellow
npx pyright .
if ($LASTEXITCODE -ne 0) {
    Write-Host "[Reviewer]  ERROR: Pyright checks failed." -ForegroundColor Red
} else {
    Write-Host "[Reviewer]  SUCCESS: Pyright checks passed." -ForegroundColor Green
}

# 2. Testing
Write-Host "`n[Reviewer] Running Unit Tests (Pytest)..." -ForegroundColor Yellow
python -m pytest ./tests/ -v
if ($LASTEXITCODE -ne 0) {
    Write-Host "[Reviewer]  ERROR: Tests failed." -ForegroundColor Red
} else {
    Write-Host "[Reviewer]  SUCCESS: Tests passed." -ForegroundColor Green
}

# 3. Code formatting check (Optional UI check)
Write-Host "`n[Reviewer] Validating UI Code formatting..." -ForegroundColor Yellow
if (Get-Command npx -errorAction SilentlyContinue) {
    npx prettier --check "apps/desktop/**/*.{html,js,css}"
    npx markdownlint "**/*.md" --ignore "node_modules"
}

Write-Host "`n>>> REVIEW COMPLETE <<<" -ForegroundColor Cyan
