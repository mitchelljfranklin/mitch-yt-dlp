using System.Reflection;

namespace MitchYtDlp.Services;

public class FfmpegResolver
{
    private static readonly string AppDataDir = Path.Combine(
        Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
        "MitchYtDlp",
        "bin");

    public string Resolve()
    {
        var basePath = AppDomain.CurrentDomain.BaseDirectory;

        var ffmpegExe = Path.Combine(basePath, "ffmpeg.exe");
        if (File.Exists(ffmpegExe))
        {
            var ffprobeExe = Path.Combine(basePath, "ffprobe.exe");
            if (File.Exists(ffprobeExe))
                return basePath;
        }

        ffmpegExe = Path.Combine(AppDataDir, "ffmpeg.exe");
        if (File.Exists(ffmpegExe))
        {
            var ffprobeExe = Path.Combine(AppDataDir, "ffprobe.exe");
            if (File.Exists(ffprobeExe))
                return AppDataDir;
        }

        return ExtractEmbeddedFfmpeg();
    }

    private static string ExtractEmbeddedFfmpeg()
    {
        Directory.CreateDirectory(AppDataDir);

        var assembly = Assembly.GetExecutingAssembly();
        var resources = assembly.GetManifestResourceNames();

        foreach (var name in resources)
        {
            if (name.EndsWith("ffmpeg.exe") || name.EndsWith("ffprobe.exe"))
            {
                var fileName = name.EndsWith("ffmpeg.exe") ? "ffmpeg.exe" : "ffprobe.exe";
                var destPath = Path.Combine(AppDataDir, fileName);

                if (!File.Exists(destPath))
                {
                    using var stream = assembly.GetManifestResourceStream(name);
                    if (stream != null)
                    {
                        using var fileStream = File.Create(destPath);
                        stream.CopyTo(fileStream);
                    }
                }
            }
        }

        return AppDataDir;
    }
}
