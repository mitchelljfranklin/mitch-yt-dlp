using System.ComponentModel;
using System.Runtime.CompilerServices;
using System.Windows;
using System.Windows.Input;
using MitchYtDlp.Helpers;
using MitchYtDlp.Models;
using MitchYtDlp.Services;

namespace MitchYtDlp.ViewModels;

public class MainViewModel : INotifyPropertyChanged
{
    private readonly YtDlpService _ytDlp = new();
    private readonly YtDlpUpdateService _updateService = new();
    private readonly FfmpegResolver _ffmpegResolver = new();
    private CancellationTokenSource? _cts;

    public MainViewModel()
    {
        StartCommand = new RelayCommand(async () => await StartDownload(), () => !IsDownloading);
        StopCommand = new RelayCommand(StopDownload, () => IsDownloading);
        BrowseCommand = new RelayCommand(BrowseFolder, () => !IsDownloading);
        ExitCommand = new RelayCommand(() => Application.Current.Shutdown());
        CheckUpdateCommand = new RelayCommand(async () => await CheckForUpdate(), () => !IsDownloading);
    }

    private string _outputFolder = "";
    public string OutputFolder
    {
        get => _outputFolder;
        set { _outputFolder = value; OnPropertyChanged(); }
    }

    private string _videoUrl = "";
    public string VideoUrl
    {
        get => _videoUrl;
        set { _videoUrl = value; OnPropertyChanged(); }
    }

    private bool _isMp3Mode;
    public bool IsMp3Mode
    {
        get => _isMp3Mode;
        set { _isMp3Mode = value; OnPropertyChanged(); }
    }

    private bool _isDownloading;
    public bool IsDownloading
    {
        get => _isDownloading;
        set
        {
            _isDownloading = value;
            OnPropertyChanged();
            CommandManager.InvalidateRequerySuggested();
        }
    }

    private double _progressPercent;
    public double ProgressPercent
    {
        get => _progressPercent;
        set { _progressPercent = value; OnPropertyChanged(); }
    }

    private string _speedText = "";
    public string SpeedText
    {
        get => _speedText;
        set { _speedText = value; OnPropertyChanged(); }
    }

    private string _etaText = "";
    public string EtaText
    {
        get => _etaText;
        set { _etaText = value; OnPropertyChanged(); }
    }

    private string _playlistText = "";
    public string PlaylistText
    {
        get => _playlistText;
        set { _playlistText = value; OnPropertyChanged(); }
    }

    private string _statusMessage = "";
    public string StatusMessage
    {
        get => _statusMessage;
        set { _statusMessage = value; OnPropertyChanged(); }
    }

    private bool _isUpdateAvailable;
    public bool IsUpdateAvailable
    {
        get => _isUpdateAvailable;
        set { _isUpdateAvailable = value; OnPropertyChanged(); }
    }

    private string _updateButtonText = "Check for yt-dlp update";
    public string UpdateButtonText
    {
        get => _updateButtonText;
        set { _updateButtonText = value; OnPropertyChanged(); }
    }

    public ICommand StartCommand { get; }
    public ICommand StopCommand { get; }
    public ICommand BrowseCommand { get; }
    public ICommand ExitCommand { get; }
    public ICommand CheckUpdateCommand { get; }

    public async Task InitializeAsync()
    {
        await CheckForUpdate(silent: true);
    }

    private async Task StartDownload()
    {
        if (string.IsNullOrWhiteSpace(VideoUrl))
        {
            StatusMessage = "Please enter a video URL";
            return;
        }

        if (string.IsNullOrWhiteSpace(OutputFolder))
        {
            StatusMessage = "Please select an output folder";
            return;
        }

        var ytDlpPath = _updateService.YtDlpPath;
        if (string.IsNullOrEmpty(ytDlpPath) || !File.Exists(ytDlpPath))
        {
            StatusMessage = "yt-dlp.exe not found. Check for updates to download it.";
            return;
        }

        var ffmpegPath = _ffmpegResolver.Resolve();
        if (string.IsNullOrEmpty(ffmpegPath))
        {
            StatusMessage = "FFmpeg not found. MP3 conversion will not be available.";
        }

        IsDownloading = true;
        StatusMessage = "Preparing...";
        ProgressPercent = 0;
        SpeedText = "";
        EtaText = "";
        PlaylistText = "";

        _cts = new CancellationTokenSource();

        var progress = new Progress<DownloadProgress>(OnProgress);

        try
        {
            await _ytDlp.RunAsync(
                VideoUrl.Trim(),
                OutputFolder.Trim(),
                IsMp3Mode,
                ffmpegPath ?? "",
                ytDlpPath,
                _cts.Token,
                progress);

            StatusMessage = "Download complete";
            ProgressPercent = 100;
        }
        catch (OperationCanceledException)
        {
            StatusMessage = "Download cancelled";
        }
        catch (Exception ex)
        {
            StatusMessage = $"Error: {ex.Message}";
            MessageBox.Show(ex.Message, "Download Error", MessageBoxButton.OK, MessageBoxImage.Error);
        }
        finally
        {
            IsDownloading = false;
            _cts?.Dispose();
            _cts = null;
        }
    }

    private void StopDownload()
    {
        _cts?.Cancel();
    }

    private void BrowseFolder()
    {
        using var dialog = new System.Windows.Forms.FolderBrowserDialog
        {
            Description = "Select output folder for downloads",
            UseDescriptionForTitle = true,
        };

        if (!string.IsNullOrWhiteSpace(OutputFolder))
            dialog.SelectedPath = OutputFolder;

        if (dialog.ShowDialog() == System.Windows.Forms.DialogResult.OK)
            OutputFolder = dialog.SelectedPath;
    }

    private async Task CheckForUpdate(bool silent = false)
    {
        var current = _updateService.GetCurrentVersion();
        if (current == null)
        {
            if (!silent)
            {
                StatusMessage = "yt-dlp not found. Click update to download.";
                IsUpdateAvailable = true;
                UpdateButtonText = "Download yt-dlp";
            }

            return;
        }

        var latest = await _updateService.GetLatestVersionAsync();
        if (latest != null && latest != current)
        {
            IsUpdateAvailable = true;
            UpdateButtonText = $"Update yt-dlp ({current} -> {latest})";

            if (!silent)
                StatusMessage = $"yt-dlp update available: {latest}";
        }
        else
        {
            IsUpdateAvailable = false;
            UpdateButtonText = "yt-dlp is up to date";

            if (!silent)
                StatusMessage = $"yt-dlp is up to date ({current})";
        }
    }

    private void OnProgress(DownloadProgress p)
    {
        if (p.Percent.HasValue)
        {
            ProgressPercent = p.Percent.Value;

            var parts = new List<string>();

            if (!string.IsNullOrEmpty(p.Speed) && !p.Speed.StartsWith("Unknown"))
                parts.Add(p.Speed.Replace("i", ""));

            if (!string.IsNullOrEmpty(p.Eta) && p.Eta != "Unknown")
                parts.Add($"ETA {p.Eta}");

            StatusMessage = parts.Count > 0
                ? $"Downloading: {string.Join(" - ", parts)}"
                : $"Downloading: {p.Percent.Value:F1}%";
        }

        if (!string.IsNullOrEmpty(p.Speed))
            SpeedText = p.Speed.StartsWith("Unknown") ? "" : p.Speed.Replace("i", "");

        if (!string.IsNullOrEmpty(p.Eta))
            EtaText = p.Eta == "Unknown" ? "" : p.Eta;

        if (p.PlaylistIndex.HasValue && p.PlaylistCount.HasValue)
            PlaylistText = $"Video {p.PlaylistIndex} / {p.PlaylistCount}";

        if (!string.IsNullOrEmpty(p.StatusMessage))
            StatusMessage = p.StatusMessage;
    }

    public event PropertyChangedEventHandler? PropertyChanged;

    protected void OnPropertyChanged([CallerMemberName] string? name = null)
        => PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(name));
}
