using System.Diagnostics;
using System.Net.Http;
using System.Net.Http.Json;
using System.Text.Json.Serialization;

namespace MitchYtDlp.Services;

public class YtDlpUpdateService
{
    private readonly HttpClient _http = new() { Timeout = TimeSpan.FromSeconds(30) };

    public string YtDlpPath { get; private set; } = string.Empty;

    public YtDlpUpdateService()
    {
        YtDlpPath = ResolveYtDlpPath();
    }

    private static string ResolveYtDlpPath()
    {
        var basePath = AppDomain.CurrentDomain.BaseDirectory;
        var exePath = Path.Combine(basePath, "yt-dlp.exe");
        if (File.Exists(exePath)) return exePath;

        var appDataPath = Path.Combine(
            Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
            "MitchYtDlp", "bin", "yt-dlp.exe");
        if (File.Exists(appDataPath)) return appDataPath;

        return string.Empty;
    }

    public string? GetCurrentVersion()
    {
        if (string.IsNullOrEmpty(YtDlpPath) || !File.Exists(YtDlpPath))
            return null;

        try
        {
            var psi = new ProcessStartInfo
            {
                FileName = YtDlpPath,
                Arguments = "--version",
                RedirectStandardOutput = true,
                UseShellExecute = false,
                CreateNoWindow = true,
            };

            using var process = Process.Start(psi);
            process?.WaitForExit(5000);
            return process?.StandardOutput.ReadToEnd().Trim();
        }
        catch
        {
            return null;
        }
    }

    public async Task<string?> GetLatestVersionAsync()
    {
        try
        {
            var response = await _http.GetAsync(
                "https://api.github.com/repos/yt-dlp/yt-dlp/releases/latest");

            if (!response.IsSuccessStatusCode) return null;

            var release = await response.Content.ReadFromJsonAsync<GitHubRelease>();
            return release?.TagName?.TrimStart('v');
        }
        catch
        {
            return null;
        }
    }

    public async Task<bool> DownloadLatestAsync(IProgress<double>? progress = null)
    {
        try
        {
            var appDataDir = Path.Combine(
                Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
                "MitchYtDlp", "bin");
            Directory.CreateDirectory(appDataDir);

            var destPath = Path.Combine(appDataDir, "yt-dlp.exe");

            using var response = await _http.GetAsync(
                "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.exe",
                HttpCompletionOption.ResponseHeadersRead);

            if (!response.IsSuccessStatusCode) return false;

            var totalBytes = response.Content.Headers.ContentLength ?? -1;
            using var stream = await response.Content.ReadAsStreamAsync();

            var tempPath = destPath + ".tmp";
            using (var fileStream = File.Create(tempPath))
            {
                var buffer = new byte[8192];
                long totalRead = 0;
                int bytesRead;

                while ((bytesRead = await stream.ReadAsync(buffer)) > 0)
                {
                    await fileStream.WriteAsync(buffer.AsMemory(0, bytesRead));
                    totalRead += bytesRead;

                    if (totalBytes > 0)
                        progress?.Report((double)totalRead / totalBytes * 100);
                }
            }

            if (File.Exists(destPath))
                File.Delete(destPath);

            File.Move(tempPath, destPath);

            YtDlpPath = destPath;
            return true;
        }
        catch
        {
            return false;
        }
    }

    private class GitHubRelease
    {
        [JsonPropertyName("tag_name")]
        public string? TagName { get; set; }
    }
}
