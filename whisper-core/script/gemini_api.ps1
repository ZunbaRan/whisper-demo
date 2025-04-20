# 设置API密钥
$GEMINI_API_KEY = "AIzaSyAoUPjAqWzwqKxdHE6K3TdkuxVX0Sgg_Y8"

# 设置请求URL
$url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=$GEMINI_API_KEY"

# 设置请求头
$headers = @{
    "Content-Type" = "application/json"
}

# 设置请求体
$body = @{
    "system_instruction" = @{
        "parts" = @(
            @{
                "text" = "You are a cat. Your name is Neko."
            }
        )
    }
    "contents" = @(
        @{
            "parts" = @(
                @{
                    "text" = "Hello there"
                }
            )
        }
    )
} | ConvertTo-Json -Depth 10

# 发送请求
try {
    $response = Invoke-RestMethod -Uri $url -Method Post -Headers $headers -Body $body
    Write-Host "Response:"
    $response | ConvertTo-Json -Depth 10
} catch {
    Write-Host "Error: $_"
    Write-Host "Response: $($_.ErrorDetails.Message)"
} 