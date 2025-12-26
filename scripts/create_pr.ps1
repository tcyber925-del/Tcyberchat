# Create PR helper for Windows PowerShell
# Usage: set environment variable GITHUB_TOKEN (repo scope) and run this script from the repo root.

param(
    [string]$Owner = 'Codcyber101',
    [string]$Repo = 'TcyberLocalChat',
    [string]$Head = 'feat/move-shims',
    [string]$Base = 'main',
    [string]$Title = 'Move test shims into backend/tests/_shims',
    [string]$PrBodyPath = 'PR_BODY.md'
)

function Fail($msg){ Write-Error $msg; exit 1 }

$token = $env:GITHUB_TOKEN
if ([string]::IsNullOrWhiteSpace($token)) {
    $token = Read-Host -Prompt 'GITHUB_TOKEN not set. Paste your GitHub PAT (repo scope)'
}
if ([string]::IsNullOrWhiteSpace($token)) { Fail 'A GitHub token (repo scope) is required.' }

if (-Not (Test-Path $PrBodyPath)) {
    Write-Host "PR body file '$PrBodyPath' not found; using a default short body."
    $bodyText = "Move test shims into `backend/tests/_shims`\n\nLocal test results: 198 passed, 9 skipped."
} else {
    $bodyText = Get-Content -Raw -Path $PrBodyPath
}

$createBody = @{ title = $Title; head = $Head; base = $Base; body = $bodyText } | ConvertTo-Json -Depth 6

$headers = @{
    Authorization = "token $token"
    Accept = 'application/vnd.github+json'
    'User-Agent' = 'create-pr-script'
}

$createUrl = "https://api.github.com/repos/$Owner/$Repo/pulls"
try {
    $pr = Invoke-RestMethod -Uri $createUrl -Method Post -Headers $headers -Body $createBody -ContentType 'application/json'
} catch {
    Fail "Failed to create PR: $($_.Exception.Message)"
}

if (-Not $pr -or -Not $pr.number) { Fail 'Unexpected response from GitHub when creating PR.' }

$prNumber = $pr.number
Write-Host "Created PR #$prNumber -> $($pr.html_url)"

# Add labels
$labels = @('tests','ci','bugfix')
$labelsBody = @{ labels = $labels } | ConvertTo-Json
$labelsUrl = "https://api.github.com/repos/$Owner/$Repo/issues/$prNumber/labels"
try {
    Invoke-RestMethod -Uri $labelsUrl -Method Post -Headers $headers -Body $labelsBody -ContentType 'application/json' | Out-Null
    Write-Host "Added labels: $($labels -join ', ')"
} catch {
    Write-Warning "Failed to add labels: $($_.Exception.Message)"
}

# Post comment with local test results
$commentBody = @{ body = "Local test results: 198 passed, 9 skipped. Ready for CI verification." } | ConvertTo-Json
$commentUrl = "https://api.github.com/repos/$Owner/$Repo/issues/$prNumber/comments"
try {
    Invoke-RestMethod -Uri $commentUrl -Method Post -Headers $headers -Body $commentBody -ContentType 'application/json' | Out-Null
    Write-Host "Posted test-results comment to PR #$prNumber"
} catch {
    Write-Warning "Failed to post comment: $($_.Exception.Message)"
}

Write-Host "Done. Open the PR: $($pr.html_url)"
