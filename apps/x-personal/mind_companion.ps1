$ErrorActionPreference = 'Stop'

Add-Type -AssemblyName PresentationFramework
Add-Type -AssemblyName PresentationCore
Add-Type -AssemblyName WindowsBase

$mindHome = if ($env:X_MIND_HOME) { $env:X_MIND_HOME } else {
    Join-Path ([Environment]::GetFolderPath('LocalApplicationData')) 'X-System\mind'
}
$dataRoot = Join-Path $mindHome 'runtime'
$statusPath = Join-Path $dataRoot 'status.json'
$stopPath = Join-Path $dataRoot 'stop.request'
$python = 'D:\X-System\runtime\x-personal-venv\Scripts\pythonw.exe'
$service = Join-Path $PSScriptRoot 'mind_service.py'
$dashboard = 'http://127.0.0.1:18764/'

[xml]$xaml = @'
<Window xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
        xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
        Width="272" Height="358" WindowStyle="None" ResizeMode="NoResize"
        AllowsTransparency="True" Background="Transparent" Topmost="True"
        ShowInTaskbar="False" WindowStartupLocation="Manual">
  <Border x:Name="Shell" Margin="8" Padding="13" CornerRadius="25"
          BorderThickness="1" BorderBrush="#554CE2D0">
    <Border.Background>
      <LinearGradientBrush StartPoint="0,0" EndPoint="1,1">
        <GradientStop Color="#F0182940" Offset="0"/>
        <GradientStop Color="#F0091222" Offset="1"/>
      </LinearGradientBrush>
    </Border.Background>
    <Border.Effect>
      <DropShadowEffect Color="#A0000000" BlurRadius="24" ShadowDepth="8" Opacity=".75"/>
    </Border.Effect>
    <Grid>
      <Grid.RowDefinitions>
        <RowDefinition Height="30"/>
        <RowDefinition Height="164"/>
        <RowDefinition Height="Auto"/>
        <RowDefinition Height="Auto"/>
        <RowDefinition Height="Auto"/>
      </Grid.RowDefinitions>
      <Grid x:Name="Header" Grid.Row="0">
        <TextBlock Text="X  /  وَمِيض" Foreground="#AEEDE7"
                   FontFamily="Segoe UI" FontSize="13" FontWeight="SemiBold"
                   VerticalAlignment="Center"/>
        <Button x:Name="CloseButton" Content="×" Width="28" Height="25"
                HorizontalAlignment="Right" VerticalAlignment="Center"
                Background="#20384B60" Foreground="#D8E6F3" BorderThickness="0"
                FontSize="17" Cursor="Hand" ToolTip="إغلاق الشخصية"/>
      </Grid>
      <Grid Grid.Row="1">
        <Canvas x:Name="AvatarCanvas" Width="220" Height="160"
                HorizontalAlignment="Center" VerticalAlignment="Center"
                Cursor="Hand">
          <Ellipse Canvas.Left="37" Canvas.Top="18" Width="146" Height="120"
                   Fill="Transparent" Stroke="#8060E8DC" StrokeThickness="2"
                   StrokeDashArray="1.1,2.4" Opacity=".8"/>
          <Ellipse Canvas.Left="70" Canvas.Top="136" Width="82" Height="12"
                   Fill="#57000000"/>
          <Canvas x:Name="CharacterCanvas">
            <Canvas.RenderTransform>
              <TranslateTransform x:Name="FloatTransform"/>
            </Canvas.RenderTransform>
            <Ellipse Canvas.Left="83" Canvas.Top="112" Width="58" Height="40"
                     Stroke="#FF72F0DB" StrokeThickness="1.5">
              <Ellipse.Fill>
                <LinearGradientBrush StartPoint="0,0" EndPoint="1,1">
                  <GradientStop Color="#FF35BDAF" Offset="0"/>
                  <GradientStop Color="#FF17617A" Offset="1"/>
                </LinearGradientBrush>
              </Ellipse.Fill>
            </Ellipse>
            <Ellipse Canvas.Left="50" Canvas.Top="35" Width="30" Height="38"
                     Fill="#FF187E8B" Stroke="#FF6DE6D7" StrokeThickness="2"/>
            <Ellipse Canvas.Left="144" Canvas.Top="35" Width="30" Height="38"
                     Fill="#FF187E8B" Stroke="#FF6DE6D7" StrokeThickness="2"/>
            <Ellipse Canvas.Left="59" Canvas.Top="21" Width="106" Height="105"
                     Stroke="#FF8BF5E6" StrokeThickness="2">
              <Ellipse.Fill>
                <RadialGradientBrush GradientOrigin=".28,.18" Center=".35,.35"
                                     RadiusX=".78" RadiusY=".8">
                  <GradientStop Color="#FFB6FFF0" Offset="0"/>
                  <GradientStop Color="#FF37CDBD" Offset=".35"/>
                  <GradientStop Color="#FF187F9B" Offset="1"/>
                </RadialGradientBrush>
              </Ellipse.Fill>
              <Ellipse.Effect>
                <DropShadowEffect Color="#FF42E6D0" BlurRadius="16"
                                  ShadowDepth="1" Opacity=".65"/>
              </Ellipse.Effect>
            </Ellipse>
            <Ellipse Canvas.Left="86" Canvas.Top="61" Width="17" Height="22"
                     Fill="#FF10243A" x:Name="EyeLeftOpen"/>
            <Ellipse Canvas.Left="123" Canvas.Top="61" Width="17" Height="22"
                     Fill="#FF10243A" x:Name="EyeRightOpen"/>
            <Ellipse Canvas.Left="90" Canvas.Top="64" Width="5" Height="6"
                     Fill="#FFFFFFFF"/>
            <Ellipse Canvas.Left="127" Canvas.Top="64" Width="5" Height="6"
                     Fill="#FFFFFFFF"/>
            <Path x:Name="EyeLeftSleep" Canvas.Left="84" Canvas.Top="70"
                  Data="M0,5 Q9,-2 19,5" Stroke="#FF10243A" StrokeThickness="3"
                  StrokeStartLineCap="Round" StrokeEndLineCap="Round"
                  Visibility="Collapsed"/>
            <Path x:Name="EyeRightSleep" Canvas.Left="121" Canvas.Top="70"
                  Data="M0,5 Q9,-2 19,5" Stroke="#FF10243A" StrokeThickness="3"
                  StrokeStartLineCap="Round" StrokeEndLineCap="Round"
                  Visibility="Collapsed"/>
            <Path Canvas.Left="98" Canvas.Top="88"
                  Data="M0,0 Q12,12 25,0" Stroke="#FF103448" StrokeThickness="3"
                  StrokeStartLineCap="Round" StrokeEndLineCap="Round"/>
            <Ellipse Canvas.Left="72" Canvas.Top="83" Width="12" Height="7"
                     Fill="#88FF8CBF"/>
            <Ellipse Canvas.Left="143" Canvas.Top="83" Width="12" Height="7"
                     Fill="#88FF8CBF"/>
            <Ellipse Canvas.Left="106" Canvas.Top="122" Width="13" Height="13"
                     Fill="#FFB8FFF3" Stroke="#FFFFFFFF" StrokeThickness="1"/>
            <TextBlock x:Name="SleepMark" Canvas.Left="160" Canvas.Top="14"
                       Text="zZ" FontFamily="Segoe UI" FontWeight="Bold"
                       FontSize="18" Foreground="#FFE2E9FF" Visibility="Collapsed"/>
          </Canvas>
        </Canvas>
      </Grid>
      <TextBlock x:Name="StateText" Grid.Row="2" Text="جاري الاتصال بعقل X..."
                 Foreground="#FFF1F6FC" FontFamily="Segoe UI" FontSize="15"
                 FontWeight="SemiBold" HorizontalAlignment="Center"
                 TextAlignment="Center" Margin="0,3,0,2"/>
      <TextBlock x:Name="DetailText" Grid.Row="3"
                 Text="أنا هنا، وحركتي تعكس حالة X الفعلية."
                 Foreground="#FF9FB5CC" FontFamily="Segoe UI" FontSize="11"
                 TextWrapping="Wrap" TextAlignment="Center"
                 HorizontalAlignment="Center" Margin="5,2,5,9"/>
      <StackPanel Grid.Row="4">
        <Button x:Name="MindButton" Content="إيقاظ X" Height="34"
                Margin="0,0,0,7" Background="#FF126C72" Foreground="White"
                BorderThickness="0" FontFamily="Segoe UI" FontWeight="SemiBold"
                Cursor="Hand"/>
        <Button x:Name="DashboardButton" Content="فتح لوحة العقل والتعلّم"
                Height="31" Background="#FF1C2C42" Foreground="#FFD5E5F4"
                BorderThickness="0" FontFamily="Segoe UI" Cursor="Hand"/>
      </StackPanel>
    </Grid>
  </Border>
</Window>
'@

$reader = New-Object System.Xml.XmlNodeReader $xaml
$window = [Windows.Markup.XamlReader]::Load($reader)
$stateText = $window.FindName('StateText')
$detailText = $window.FindName('DetailText')
$mindButton = $window.FindName('MindButton')
$dashboardButton = $window.FindName('DashboardButton')
$openEyes = @($window.FindName('EyeLeftOpen'), $window.FindName('EyeRightOpen'))
$sleepEyes = @($window.FindName('EyeLeftSleep'), $window.FindName('EyeRightSleep'))
$sleepMark = $window.FindName('SleepMark')
$floatTransform = $window.FindName('FloatTransform')
$header = $window.FindName('Header')
$avatarCanvas = $window.FindName('AvatarCanvas')
$closeButton = $window.FindName('CloseButton')
$script:mindAwake = $false
$script:requestPending = $false
$script:showHint = $false
$script:animationTick = 0

function Set-AvatarState([bool]$awake, [bool]$working, [string]$message) {
    $script:mindAwake = $awake
    foreach ($eye in $openEyes) {
        $eye.Visibility = if ($awake) { 'Visible' } else { 'Collapsed' }
    }
    foreach ($eye in $sleepEyes) {
        $eye.Visibility = if ($awake) { 'Collapsed' } else { 'Visible' }
    }
    $sleepMark.Visibility = if ($awake) { 'Collapsed' } else { 'Visible' }
    if ($working) {
        $stateText.Text = 'X بيشتغل دلوقتي'
        $detailText.Text = 'أنا بتابع مرحلة تنفيذ حقيقية من طلبك.'
        $mindButton.Content = 'اطلب نوم X بعد المهمة'
    }
    elseif ($awake) {
        $stateText.Text = 'X صاحي ومستعد'
        $detailText.Text = 'أنا هنا. اضغط عليّ للتفاعل، أو افتح لوحة التعلّم.'
        $mindButton.Content = if ($script:requestPending) { 'إلغاء طلب النوم' } else { 'نوم X مؤقتًا' }
    }
    else {
        $stateText.Text = 'X نائم حاليًا'
        $detailText.Text = $message
        $mindButton.Content = 'إيقاظ X'
    }
    $dashboardButton.IsEnabled = $awake
    if ($script:showHint) {
        $detailText.Text = 'أنا وَمِيض: أتحرك مع حالة X فقط. لا أراقب الشاشة أو الميكروفون.'
    }
}

function Update-MindStatus {
    $status = $null
    try {
        if (Test-Path -LiteralPath $statusPath) {
            $status = Get-Content -LiteralPath $statusPath -Raw -ErrorAction Stop |
                ConvertFrom-Json -ErrorAction Stop
        }
    }
    catch {
        Set-AvatarState $false $false 'تعذرت قراءة الحالة المحلية؛ لم أغيّر أي إعداد.'
        return
    }

    $alive = $false
    if ($null -ne $status -and $status.pid -match '^\d+$') {
        try {
            $process = Get-Process -Id ([int]$status.pid) -ErrorAction Stop
            $updated = [DateTimeOffset]::Parse([string]$status.updated_at).ToUniversalTime()
            $started = $process.StartTime.ToUniversalTime()
            $age = ([DateTimeOffset]::UtcNow - $updated).TotalSeconds
            $sameLaunch = $process.ProcessName -ieq 'pythonw' -and
                $updated -ge $started.AddSeconds(-2)
            $fresh = $age -le 12 -or
                ([string]$status.state -eq 'processing' -and $age -le 360)
            $alive = $sameLaunch -and $fresh -and [string]$status.state -ne 'stopped'
        }
        catch {
            $alive = $false
        }
    }

    $script:requestPending = Test-Path -LiteralPath $stopPath
    if (-not $alive) {
        Set-AvatarState $false $false 'الجسم شغال، لكن عقل X متوقف. اضغط إيقاظ للبدء.'
        return
    }
    if ([string]$status.state -eq 'processing') {
        Set-AvatarState $true $true ''
        if ($script:requestPending) {
            $detailText.Text = 'سينهي X المهمة الحالية ثم ينام.'
            $mindButton.Content = 'إلغاء طلب النوم'
        }
        return
    }
    if ($script:requestPending) {
        Set-AvatarState $true $false 'سيدخل X وضع النوم بعد إنهاء الطلب الجاري.'
        $mindButton.Content = 'إلغاء طلب النوم'
        return
    }
    Set-AvatarState $true $false ''
}

$mindButton.Add_Click({
    if ($script:mindAwake) {
        try {
            if ($script:requestPending) {
                Remove-Item -LiteralPath $stopPath -Force -ErrorAction Stop
                $detailText.Text = 'تم إلغاء طلب النوم.'
            }
            else {
                New-Item -ItemType Directory -Path $dataRoot -Force | Out-Null
                Set-Content -LiteralPath $stopPath -Value 'sleep' -Encoding ASCII -ErrorAction Stop
                $detailText.Text = 'طلبت نوم X؛ سينتظر انتهاء المهمة الحالية أولًا.'
            }
        }
        catch {
            $detailText.Text = 'تعذر تغيير حالة X: ' + $_.Exception.Message
        }
    }
    else {
        try {
            if (-not (Test-Path -LiteralPath $python) -or
                -not (Test-Path -LiteralPath $service)) {
                throw 'لم أجد ملفات تشغيل X في المسارات المتوقعة.'
            }
            Start-Process -FilePath $python -ArgumentList ('"' + $service + '"') `
                -WorkingDirectory $PSScriptRoot -WindowStyle Hidden -ErrorAction Stop
            $stateText.Text = 'X بيصحى...'
            $detailText.Text = 'بدأت تشغيل عقل X داخل حساب Windows الحالي.'
        }
        catch {
            $detailText.Text = 'تعذر إيقاظ X: ' + $_.Exception.Message
        }
    }
    Update-MindStatus
})

$dashboardButton.Add_Click({
    try {
        if (-not $script:mindAwake) {
            $detailText.Text = 'أيقظ X أولًا لفتح لوحة العقل والتعلّم.'
            return
        }
        Start-Process -FilePath $dashboard -ErrorAction Stop
    }
    catch {
        $detailText.Text = 'تعذر فتح اللوحة: ' + $_.Exception.Message
    }
})

$closeButton.Add_Click({ $window.Close() })
$header.Add_MouseLeftButtonDown({
    if ($_.ChangedButton -eq [Windows.Input.MouseButton]::Left) {
        $window.DragMove()
    }
})
$avatarCanvas.Add_MouseLeftButtonDown({
    $script:showHint = -not $script:showHint
    if ($script:showHint) {
        $detailText.Text = 'أنا وَمِيض: أتحرك مع حالة X فقط. لا أراقب الشاشة أو الميكروفون.'
    }
    else {
        Update-MindStatus
    }
})

$pollTimer = New-Object Windows.Threading.DispatcherTimer
$pollTimer.Interval = [TimeSpan]::FromSeconds(2)
$pollTimer.Add_Tick({ Update-MindStatus })

$animationTimer = New-Object Windows.Threading.DispatcherTimer
$animationTimer.Interval = [TimeSpan]::FromMilliseconds(80)
$animationTimer.Add_Tick({
    $script:animationTick++
    $floatTransform.Y = [Math]::Sin($script:animationTick / 12) * 2.5
})

$window.Add_SourceInitialized({
    $area = [System.Windows.SystemParameters]::WorkArea
    $window.Left = $area.Right - $window.Width - 18
    $window.Top = $area.Bottom - $window.Height - 28
})
$window.Add_Closed({
    $pollTimer.Stop()
    $animationTimer.Stop()
})
Update-MindStatus
$pollTimer.Start()
$animationTimer.Start()
$window.ShowDialog() | Out-Null
