using System.Windows;
using System.Windows.Input;
using MitchYtDlp.ViewModels;

namespace MitchYtDlp;

public partial class MainWindow : Window
{
    private readonly MainViewModel _vm;

    public MainWindow()
    {
        _vm = new MainViewModel();
        DataContext = _vm;
        InitializeComponent();
    }

    public async Task InitializeAsync()
    {
        await _vm.InitializeAsync();
    }

    private void Window_KeyDown(object sender, KeyEventArgs e)
    {
        if (e.Key == Key.Escape && _vm.IsDownloading)
        {
            _vm.StopCommand.Execute(null);
            e.Handled = true;
        }
    }

    private void UrlTextBox_KeyDown(object sender, KeyEventArgs e)
    {
        if (e.Key == Key.Enter && !_vm.IsDownloading)
        {
            _vm.StartCommand.Execute(null);
            e.Handled = true;
        }
    }
}
