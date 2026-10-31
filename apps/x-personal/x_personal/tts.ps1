param([ValidateSet('voices','render','speak')][string]$Mode='voices')
$ErrorActionPreference='Stop'
[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false)
Add-Type -AssemblyName System.Runtime.WindowsRuntime
$null=[Windows.Media.SpeechSynthesis.SpeechSynthesizer,Windows.Media.SpeechSynthesis,ContentType=WindowsRuntime]
$null=[Windows.Media.SpeechSynthesis.SpeechSynthesisStream,Windows.Media.SpeechSynthesis,ContentType=WindowsRuntime]
function Wait-WinRT($Operation,[Type]$ResultType){
    $method=[System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object { $_.Name -eq 'AsTask' -and $_.IsGenericMethod -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1' } | Select-Object -First 1
    $task=$method.MakeGenericMethod($ResultType).Invoke($null,@($Operation))
    $task.GetAwaiter().GetResult()
}
$voices=@([Windows.Media.SpeechSynthesis.SpeechSynthesizer]::AllVoices)
if($Mode -eq 'voices'){
    ConvertTo-Json -InputObject @($voices | ForEach-Object { @{name=$_.DisplayName;language=$_.Language} }) -Compress
    exit 0
}
$payload=([Console]::In.ReadToEnd() | ConvertFrom-Json)
$text=[Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($payload.text_b64))
if([string]::IsNullOrWhiteSpace($text) -or $text.Length -gt 4000){throw 'Speech text must be 1..4000 characters.'}
$voice=$voices | Where-Object { $_.Language -like 'ar-*' } | Select-Object -First 1
if(-not $voice){throw 'No local Arabic Windows voice is installed.'}
$synth=New-Object Windows.Media.SpeechSynthesis.SpeechSynthesizer
$speech=$null;$stream=$null;$memory=$null;$player=$null
try{
    $synth.Voice=$voice
    $speech=Wait-WinRT ($synth.SynthesizeTextToStreamAsync($text)) ([Windows.Media.SpeechSynthesis.SpeechSynthesisStream])
    $stream=[System.IO.WindowsRuntimeStreamExtensions]::AsStreamForRead($speech)
    $memory=New-Object System.IO.MemoryStream
    $stream.CopyTo($memory)
    if($Mode -eq 'render'){
        @{voice=$voice.DisplayName;language=$voice.Language;wav_b64=[Convert]::ToBase64String($memory.ToArray())} | ConvertTo-Json -Compress
    }else{
        $memory.Position=0
        $player=New-Object System.Media.SoundPlayer($memory)
        $player.Load();$player.PlaySync()
        @{voice=$voice.DisplayName;language=$voice.Language;status='spoken'} | ConvertTo-Json -Compress
    }
}finally{
    if($player){$player.Dispose()};if($memory){$memory.Dispose()};if($stream){$stream.Dispose()};if($speech){$speech.Dispose()};$synth.Dispose()
}
