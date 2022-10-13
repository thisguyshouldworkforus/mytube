# YouTube-DL Version
# .\youtube-dl.exe --version

# Global Variables
$DATE = (Get-Date -Format 'yyyy.MM.dd')
$YOUTUBE_DL_PATH = ("D:\MediaApps\YouTubeDL\youtube-dl.exe")
$YTDL_VERSION = ("$YOUTUBE_DL_PATH", ' --version')
$LOGDIR = ("E:\YouTubeDL")
$LOGFILE = ("$LOGDIR" + '\' + 'youtube-dl' + '.' + $DATE.Replace('.', '-') + '.log')
$CURRENT_VERSION = (Invoke-Expression -Command "$YTDL_VERSION").ToString()
$TOKEN = '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'


# Check for a log directory, create if it doesn't exist
if (!(Test-Path -LiteralPath $LOGDIR)) {
    New-Item -Path $LOGDIR -ItemType Directory | Out-Null
}

# Check for a log file, create if it doesn't exist
if (!(Test-Path -LiteralPath $LOGFILE)) {
    New-Item -Path $LOGFILE -ItemType File | Out-Null
}

$REQUEST = (Invoke-RestMethod -Method Get -Headers @{"Authorization" = "Bearer $TOKEN"} "https://api.github.com/repos/ytdl-org/youtube-dl/releases")
$RESPONSES = @($REQUEST.tag_name)

ForEach ($RESPONSE in $RESPONSES) {
    if ($RESPONSE -gt $CURRENT_VERSION) {
        $UPDATE = $true
        $NEW_VERSION = $RESPONSE
        Write-Host "Update Available! ($NEW_VERSION is greater than $CURRENT_VERSION)" | Tee-Object -FilePath $LOGFILE -Append
        break
    } elseif ($RESPONSE -eq $CURRENT_VERSION) {
        $UPDATE = $false
        Write-Host "Your version is up to date! ($RESPONSE is equal to $CURRENT_VERSION)" | Tee-Object -FilePath $LOGFILE -Append
        break
    }
}
if ("$UPDATE" -eq $true) {
    Write-Host "Downloading update..." | Tee-Object -FilePath $LOGFILE -Append
    $DOWNLOAD = (Invoke-RestMethod -Method Get -Headers @{"Authorization" = "Bearer $TOKEN"} "https://api.github.com/repos/ytdl-org/youtube-dl/releases/latest")
    $DOWNLOAD_URL = ($DOWNLOAD.assets | Where-Object {$_.name -match 'youtube-dl.exe$'} | Select-Object browser_download_url | Where-Object {$_.browser_download_url -match "$NEW_VERSION"} | Select-Object browser_download_url)
    $DOWNLOAD_FILE = ($DOWNLOAD_URL -split '/')[-1]
    $DOWNLOAD_PATH = ($YOUTUBE_DL_PATH + $DOWNLOAD_FILE)
    $DOWNLOAD_RESULT = (Invoke-Expression -Command "Start-Process -FilePath $DOWNLOAD_PATH -ArgumentList $DOWNLOAD_URL -Wait -Verb runas")
    if ($DOWNLOAD_RESULT -eq $true) {
        Write-Host "Update Downloaded!" | Tee-Object -FilePath $LOGFILE -Append
    } else {
        Write-Host "Update Download Failed!" | Tee-Object -FilePath $LOGFILE -Append
    }
} else {
    Write-Host "No Update Available!" | Tee-Object -FilePath $LOGFILE -Append
}

# Remove all PART files (partially downloaded content)
$DIRECTORIES = (Get-ChildItem "T:\youtube" -Name)
ForEach ($DIRECTORY in $DIRECTORIES) {
    $PART_FILES = (Get-ChildItem -LiteralPath "T:\youtube\$DIRECTORY" | Where-Object {$_.Name -match '.part$'})
    ForEach ($PART_FILE in $PART_FILES) {
        Remove-Item -LiteralPath "$PART_FILE" -Force
    }
}

# Download YouTube Videos
Get-Content -LiteralPath "C:\Users\alexa\GitHubCode\mytube\pending_downloads.txt" | ForEach-Object -ThrottleLimit 10 -Parallel {
    $URL = $_
    Start-Process -WindowStyle Hidden -FilePath "$using:YOUTUBE_DL_PATH" -ArgumentList "$URL"
}

