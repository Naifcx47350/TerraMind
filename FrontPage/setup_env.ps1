# Creates FrontPage/.env for product RAG (run once from FrontPage folder)
$envPath = Join-Path $PSScriptRoot ".env"
@"

USE_MOCK=false
RAG_SERVICE_URL=http://localhost:8001/query
REQUEST_TIMEOUT=90

"@ | Set-Content -Path $envPath -Encoding utf8
Write-Host "Created $envPath"
Get-Content $envPath
