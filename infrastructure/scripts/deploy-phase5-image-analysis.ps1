param(
    [Parameter(Mandatory = $true)][string]$ImagesBucketName,
    [Parameter(Mandatory = $true)][string]$CodeBucketName,
    [Parameter(Mandatory = $true)][string]$GeminiSecretArn,
    [string]$Region = "ap-south-1",
    [string]$StackName = "krishimitra-dev-phase5-image-analysis"
)

$ErrorActionPreference = "Stop"
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$lambdaSource = Join-Path $repoRoot "infrastructure\lambda\image_foundation\handler.py"
$template = Join-Path $repoRoot "infrastructure\cloudformation\phase5-image-analysis.yml"
$buildRoot = Join-Path $repoRoot ".build"
$workDir = Join-Path $buildRoot ("krishimitra-phase5-" + [guid]::NewGuid())
$zipPath = Join-Path $workDir "phase5-image-analysis.zip"
$notificationPath = Join-Path $workDir "notification.json"
$codeKey = "deployments/phase5/image-analysis-" + (Get-Date -Format "yyyyMMddHHmmss") + ".zip"

try {
    New-Item -ItemType Directory -Path $buildRoot -Force | Out-Null
    New-Item -ItemType Directory -Path $workDir | Out-Null
    Copy-Item -LiteralPath $lambdaSource -Destination (Join-Path $workDir "handler.py")
    Compress-Archive -LiteralPath (Join-Path $workDir "handler.py") -DestinationPath $zipPath
    aws s3 cp $zipPath "s3://$CodeBucketName/$codeKey" --region $Region --only-show-errors
    if ($LASTEXITCODE -ne 0) { throw "Lambda package upload failed" }

    aws cloudformation deploy `
        --template-file $template `
        --stack-name $StackName `
        --capabilities CAPABILITY_NAMED_IAM `
        --region $Region `
        --parameter-overrides `
            "ImagesBucketName=$ImagesBucketName" `
            "CodeBucketName=$CodeBucketName" `
            "CodeObjectKey=$codeKey" `
            "GeminiSecretArn=$GeminiSecretArn" `
        --no-fail-on-empty-changeset
    if ($LASTEXITCODE -ne 0) { throw "Phase 5 CloudFormation deployment failed" }

    $functionArn = aws cloudformation describe-stacks `
        --stack-name $StackName `
        --region $Region `
        --query "Stacks[0].Outputs[?OutputKey=='FunctionArn'].OutputValue | [0]" `
        --output text
    if ($LASTEXITCODE -ne 0 -or -not $functionArn) { throw "Function ARN lookup failed" }

    $currentJson = aws s3api get-bucket-notification-configuration `
        --bucket $ImagesBucketName `
        --region $Region `
        --output json
    if ($LASTEXITCODE -ne 0) { throw "Existing S3 notification lookup failed" }
    $current = $currentJson | ConvertFrom-Json
    $existing = @()
    if ($null -ne $current.LambdaFunctionConfigurations) {
        $existing = @($current.LambdaFunctionConfigurations | Where-Object {
            $null -ne $_ -and $_.Id -notlike "krishimitra-phase5-*"
        })
    }
    $phase5 = foreach ($suffix in @(".jpg", ".jpeg", ".png", ".webp")) {
        [pscustomobject]@{
            Id = "krishimitra-phase5-" + $suffix.TrimStart(".")
            LambdaFunctionArn = $functionArn
            Events = @("s3:ObjectCreated:*")
            Filter = [pscustomobject]@{
                Key = [pscustomobject]@{
                    FilterRules = @(
                        [pscustomobject]@{ Name = "prefix"; Value = "farmer-uploads/" },
                        [pscustomobject]@{ Name = "suffix"; Value = $suffix }
                    )
                }
            }
        }
    }
    $allLambdaConfigurations = @($phase5)
    if ($existing.Count -gt 0) {
        $allLambdaConfigurations = @($existing) + @($phase5)
    }
    $notification = [ordered]@{
        LambdaFunctionConfigurations = $allLambdaConfigurations
    }
    if ($current.TopicConfigurations) {
        $notification.TopicConfigurations = @($current.TopicConfigurations)
    }
    if ($current.QueueConfigurations) {
        $notification.QueueConfigurations = @($current.QueueConfigurations)
    }
    if ($current.EventBridgeConfiguration) {
        $notification.EventBridgeConfiguration = $current.EventBridgeConfiguration
    }
    $notification | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $notificationPath -Encoding utf8
    aws s3api put-bucket-notification-configuration `
        --bucket $ImagesBucketName `
        --notification-configuration "file://$notificationPath" `
        --region $Region
    if ($LASTEXITCODE -ne 0) { throw "S3 event wiring failed" }

    Write-Host "Phase 5 image Lambda deployed and S3 events configured: $functionArn"
}
finally {
    if (Test-Path -LiteralPath $workDir) {
        $resolvedWorkDir = (Resolve-Path -LiteralPath $workDir).Path
        if (-not $resolvedWorkDir.StartsWith($buildRoot, [StringComparison]::OrdinalIgnoreCase)) {
            throw "Refusing to clean a build directory outside the repository"
        }
        Remove-Item -LiteralPath $resolvedWorkDir -Recurse -Force
    }
}
