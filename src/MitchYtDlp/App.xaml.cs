using System.Windows;
using System.Windows.Input;

namespace MitchYtDlp;

public partial class App : Application
{
    protected override async void OnStartup(StartupEventArgs e)
    {
        base.OnStartup(e);

        var window = new MainWindow();
        window.Show();

        await window.InitializeAsync();
    }
}
