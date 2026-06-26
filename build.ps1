param(
    [switch]$SkipDownload,
    [switch]$SkipPublish
)

$ErrorActionPreference = "Stop"
$BinDir = Join-Path $PSScriptRoot "bin"
$ProjectDir = Join-Path $PSScriptRoot "src\MitchYtDlp"

if (-not $SkipDownload) {
    Write-Host "=== Downloading tools ==="

    if (-not (Test-Path $BinDir)) {
        New-Item -ItemType Directory -Path $BinDir -Force | Out-Null
    }

    $YtDlpUrl = "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.exe"
    $YtDlpPath = Join-Path $BinDir "yt-dlp.exe"

    Write-Host "Downloading yt-dlp.exe..."
    Invoke-WebRequest -Uri $YtDlpUrl -OutFile $YtDlpPath -UseBasicParsing
    Write-Host "  -> $YtDlpPath"

    $FfmpegZip = Join-Path $BinDir "ffmpeg.zip"
    $FfmpegUrl = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"

    if (-not (Test-Path (Join-Path $BinDir "ffmpeg.exe")) -or -not (Test-Path (Join-Path $BinDir "ffprobe.exe"))) {
        Write-Host "Downloading FFmpeg essentials..."
        Invoke-WebRequest -Uri $FfmpegUrl -OutFile $FfmpegZip -UseBasicParsing

        Write-Host "Extracting FFmpeg..."
        Add-Type -AssemblyName System.IO.Compression.FileSystem
        $zip = [System.IO.Compression.ZipFile]::OpenRead($FfmpegZip)
        $ffmpegEntry = $zip.Entries | Where-Object { $_.Name -eq "ffmpeg.exe" } | Select-Object -First 1
        $ffprobeEntry = $zip.Entries | Where-Object { $_.Name -eq "ffprobe.exe" } | Select-Object -First 1

        if ($ffmpegEntry) {
            [System.IO.Compression.ZipFileExtensions]::ExtractToFile($ffmpegEntry, (Join-Path $BinDir "ffmpeg.exe"), $true)
        }
        if ($ffprobeEntry) {
            [System.IO.Compression.ZipFileExtensions]::ExtractToFile($ffprobeEntry, (Join-Path $BinDir "ffprobe.exe"), $true)
        }
        $zip.Dispose()
        Remove-Item $FfmpegZip -Force
        Write-Host "  -> ffmpeg.exe, ffprobe.exe extracted to $BinDir"
    } else {
        Write-Host "FFmpeg already present, skipping download."
    }
}

if (-not $SkipPublish) {
    Write-Host "`n=== Publishing .NET project ==="
    dotnet publish $ProjectDir -c Release -o "$PSScriptRoot\dist" --self-contained -r win-x64 -p:PublishSingleFile=true
    Write-Host "`nOutput: dist\MitchYtDlp.exe"
}
