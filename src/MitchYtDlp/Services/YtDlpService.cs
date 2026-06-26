using System.Diagnostics;
using System.Text.RegularExpressions;
using MitchYtDlp.Models;

namespace MitchYtDlp.Services;

public partial class YtDlpService
{
    [GeneratedRegex(@"\[download\]\s+(\d+\.?\d*)%\s+of\s+\S+(?:\s+at\s+(\S+))?\s*(?:ETA\s+(\S+))?")]
    private static partial Regex ProgressRegex();

    [GeneratedRegex(@"\[download\]\s+Downloading\s+video\s+(\d+)\s+of\s+(\d+)")]
    private static partial Regex PlaylistRegex();

    [GeneratedRegex(@"ERROR:")]
    private static partial Regex ErrorRegex();

    public async Task RunAsync(
        string url,
        string outputDir,
        bool mp3,
        string ffmpegPath,
        string ytDlpPath,
        CancellationToken ct,
        IProgress<DownloadProgress> progress)
    {
        var args = BuildArgs(url, outputDir, mp3, ffmpegPath);

        var psi = new ProcessStartInfo
        {
            FileName = ytDlpPath,
            Arguments = args,
            RedirectStandardError = true,
            UseShellExecute = false,
            CreateNoWindow = true,
        };

        using var process = new Process { StartInfo = psi };

        var tcs = new TaskCompletionSource<bool>();

        process.EnableRaisingEvents = true;
        process.Exited += (_, _) => tcs.TrySetResult(true);

        process.ErrorDataReceived += (_, e) =>
        {
            if (e.Data == null) return;
            var p = ParseProgress(e.Data);
            if (p != null) progress.Report(p);
        };

        process.Start();
        process.BeginErrorReadLine();

        using (ct.Register(() =>
        {
            if (!process.HasExited)
                process.Kill();
        }))
        {
            await tcs.Task;
        }

        process.WaitForExit();

        if (process.ExitCode != 0 && !ct.IsCancellationRequested)
        {
            throw new InvalidOperationException($"yt-dlp exited with code {process.ExitCode}");
        }
    }

    private static string BuildArgs(string url, string outputDir, bool mp3, string ffmpegPath)
    {
        var template = System.IO.Path.Combine(outputDir, "%(title)s.%(ext)s");
        var args = $"--progress --newline --ffmpeg-location \"{ffmpegPath}\" -o \"{template}\" ";

        if (mp3)
            args += "--extract-audio --audio-format mp3 ";

        args += $"\"{url}\"";
        return args;
    }

    private static DownloadProgress? ParseProgress(string line)
    {
        var match = ProgressRegex().Match(line);
        if (match.Success)
        {
            var p = new DownloadProgress();

            if (double.TryParse(match.Groups[1].Value, out var percent))
                p = p with { Percent = percent };

            var speed = match.Groups[2].Value;
            if (!string.IsNullOrEmpty(speed))
                p = p with { Speed = speed };

            var eta = match.Groups[3].Value;
            if (!string.IsNullOrEmpty(eta))
                p = p with { Eta = eta };

            return p;
        }

        match = PlaylistRegex().Match(line);
        if (match.Success)
        {
            return new DownloadProgress
            {
                PlaylistIndex = int.Parse(match.Groups[1].Value),
                PlaylistCount = int.Parse(match.Groups[2].Value),
            };
        }

        if (ErrorRegex().IsMatch(line))
        {
            return new DownloadProgress { StatusMessage = line };
        }

        if (line.StartsWith("[ExtractAudio]") || line.StartsWith("[download] Destination:"))
        {
            return new DownloadProgress { StatusMessage = line };
        }

        return null;
    }
}
