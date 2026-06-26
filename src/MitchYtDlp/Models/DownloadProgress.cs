namespace MitchYtDlp.Models;

public record DownloadProgress
{
    public double? Percent { get; init; }
    public string? Speed { get; init; }
    public string? Eta { get; init; }
    public int? PlaylistIndex { get; init; }
    public int? PlaylistCount { get; init; }
    public string? StatusMessage { get; init; }
}
