# Autor: André Mohallem Ferraz
param(
 [Parameter(Mandatory=$true)][string]$Output,
 [ValidatePattern('^\d+\.\d+$')][string]$Version='1.0'
)
$ErrorActionPreference='Stop'
[Console]::OutputEncoding=New-Object System.Text.UTF8Encoding($false)
$word=New-Object -ComObject Word.Application
$word.Visible=$false
$word.DisplayAlerts=0
try {
 foreach($name in @("Relatorio-Tecnico-Fase3-v$Version","Roteiro-Video-Fase3-v$Version")){
  $document=$null
  try {
   $document=$word.Documents.Open("$output\$name.docx",$false,$true)
   $document.ExportAsFixedFormat("$output\$name.pdf",17)
   "$name pages: "+$document.ComputeStatistics(2)
  } finally {if($document){$document.Close($false)}}
 }
} finally {if($word.Documents.Count -eq 0){$word.Quit()};[void][Runtime.InteropServices.Marshal]::ReleaseComObject($word)}
$ppt=New-Object -ComObject PowerPoint.Application
$presentation=$null
try {
 $presentation=$ppt.Presentations.Open("$output\Apresentacao-Executiva-Fase3-v$Version.pptx",$true,$false,$false)
 $presentation.SaveAs("$output\Apresentacao-Executiva-Fase3-v$Version.pdf",32)
 [void][IO.Directory]::CreateDirectory("$output\render")
 for($index=1;$index -le $presentation.Slides.Count;$index++){
  $presentation.Slides.Item($index).Export(("$output\render\slide-{0:D2}.png" -f $index),'PNG',1920,1080)
 }
 "slides: "+$presentation.Slides.Count
} finally {
 if($presentation){$presentation.Close()}
 if($ppt.Presentations.Count -eq 0){$ppt.Quit()}
 [void][Runtime.InteropServices.Marshal]::ReleaseComObject($ppt)
}
Add-Type -AssemblyName System.Speech
$voice=New-Object System.Speech.Synthesis.SpeechSynthesizer
try {
 $voice.SelectVoice('Microsoft Maria Desktop')
 $voice.Rate=2
 [void][IO.Directory]::CreateDirectory("$output\audio")
 $narrations=Get-Content -LiteralPath "$output\narracao.json" -Encoding UTF8 -Raw | ConvertFrom-Json
 foreach($entry in $narrations){
  $voice.SetOutputToWaveFile(("$output\audio\slide-{0:D2}.wav" -f [int]$entry.slide))
  $voice.Speak([string]$entry.text)
  $voice.SetOutputToNull()
 }
 "audio tracks: "+$narrations.Count
} finally {$voice.Dispose()}
