# 在 PowerShell 中查看最大的文件
git ls-tree -r -t -l --full-name HEAD | Sort-Object -Property {[int]($_ -split '\s+')[3]} -Descending | Select-Object -First 10

# 在 PowerShell 中执行
git filter-branch --force --index-filter "git rm -r --cached --ignore-unmatch whisper-core/models whisper-core/@data" --prune-empty --tag-name-filter cat -- --all