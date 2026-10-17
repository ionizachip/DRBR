# install_knight_hub.ps1
# Knight Hub installer for DELTARUNE Chapter 3 (v0.0.105).
# Windows PowerShell 5.1 compatible. ASCII only. Never downloads anything.
#
# Normal use: double-click INSTALL_KNIGHT_HUB.bat (it runs this script).
# Switches:   -Restore         put data.win.vanilla back as data.win (RESTORE_VANILLA.bat)
#             -Force           reinstall even if Knight Hub is already installed
#             -OverwriteMusic  replace existing (non kaizoknight.ogg) music files that differ
#
# Test / support hooks (environment variables, ignored when unset):
#   KH_XDELTA=<path>            use this xdelta3 executable instead of xdelta3.exe beside the script
#   KH_NOPAUSE=1                (used by the .bat files) do not pause at the end
#   KH_ASSUME_YES=1             do not ask the Y/N confirmation question
#   KH_FREE_BYTES_OVERRIDE=<n>  pretend the drive has n free bytes
#   KH_FAIL_AT=<stage>          simulate a failure at a stage: after_backup, after_join,
#                               after_patch, after_verify_output, after_prev_rename, after_move,
#                               after_final_verify, before_music, after_restore_copy
#   KH_FAIL_MODE=exit           with KH_FAIL_AT: die at once with exit code 99 and NO cleanup
#                               (simulates a crash / killed process). Default: raise an error.
#
# Exit codes:
#   0  success (installed, already installed, restored, or already vanilla)
#   1  unexpected internal error (see knight_hub_install.log)
#   2  wrong folder: data.win not found next to this script (or script run from inside a zip)
#   3  xdelta3 missing, damaged, or cannot be started
#   4  KNIGHT_HUB_MANIFEST.txt missing or invalid
#   5  patch part missing, wrong size, or wrong checksum (or joined patch wrong)
#   6  data.win is not supported (different version or different mod) - not touched
#   7  data.win.vanilla exists but is not the vanilla file - not touched
#   8  not enough free disk space (or the disk filled up)
#   9  data.win is locked / in use (close DELTARUNE) - not touched
#  10  patching failed (xdelta3 error or output checksum mismatch) - data.win untouched
#  11  replacing data.win failed - the previous data.win was put back
#  12  final data.win check failed - the previous data.win was put back
#  13  no valid data.win.vanilla available for restore / reinstall
#  14  you answered No (or no answer could be read)
#  15  no permission (read-only file or folder) - not touched
#  16  CRITICAL: could not put the previous data.win back automatically (see message)
#  17  a NEWER Knight Hub build is installed than this package (an older folder's installer) - not touched
#  99  simulated failure (KH_FAIL_AT test hook)
param(
    [switch]$Restore,
    [switch]$Force,
    [switch]$OverwriteMusic
)

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'

$script:KhVersion = '1.0'
$script:GameDir = $PSScriptRoot
if ([string]::IsNullOrEmpty($script:GameDir)) {
    $script:GameDir = [System.IO.Path]::GetDirectoryName($MyInvocation.MyCommand.Path)
}
$script:GameDir = $script:GameDir.TrimEnd([char]'\', [char]'/')
if ($script:GameDir.Length -eq 0) { $script:GameDir = [string][System.IO.Path]::DirectorySeparatorChar }

$script:NameData = 'data.win'
$script:NameBackup = 'data.win.vanilla'
$script:NamePrev = 'data.win.knighthub_prev'
$script:NameManifest = 'KNIGHT_HUB_MANIFEST.txt'
$script:NameLog = 'knight_hub_install.log'
# build 52: which Knight Hub build this data.win is (written after every install), so an older package never replaces it
$script:NameMarker = 'knight_hub_build.txt'
$script:NameExtras = 'knight_hub_extras.zip'
# build 47: the new fight songs come in a second zip (each package file stays under 30 MB)
$script:NameMusic = 'knight_hub_music.zip'
$script:NameMusic2 = 'knight_hub_music2.zip'
# build 50: the Claude Music Handoff's 20 songs come in two more zips
$script:NameMusic3 = 'knight_hub_music3.zip'
$script:NameMusic4 = 'knight_hub_music4.zip'
# build 50: the KF Song Pack's songs (kfsongs\<song_id>\...), unpacked next to data.win
$script:NameKfSongs = 'knight_hub_kfsongs.zip'
$script:TmpPrefix = '.knighthub_tmp_'
$script:ExtraTemps = New-Object System.Collections.ArrayList
$script:LogBroken = $false
$script:Manifest = $null
$script:ParentDir = ''
try { $script:ParentDir = [System.IO.Path]::GetDirectoryName($script:GameDir) } catch { $script:ParentDir = '' }
if ($null -eq $script:ParentDir) { $script:ParentDir = '' }

# ---------------------------------------------------------------- logging

function Get-Clean([string]$Text) {
    if ($null -eq $Text) { return '' }
    $t = $Text
    if ($script:GameDir.Length -gt 3) {
        $t = $t.Replace($script:GameDir, '<game folder>')
    }
    if ($script:ParentDir.Length -gt 3) {
        $t = $t.Replace($script:ParentDir, '<DELTARUNE folder>')
    }
    return $t
}

function Write-LogLine([string]$Level, [string]$Text) {
    if ($script:LogBroken) { return }
    try {
        $stamp = (Get-Date).ToString('yyyy-MM-dd HH:mm:ss')
        $line = $stamp + ' [' + $Level + '] ' + (Get-Clean $Text).Replace("`r", '').Replace("`n", ' | ') + "`r`n"
        [System.IO.File]::AppendAllText([System.IO.Path]::Combine($script:GameDir, $script:NameLog), $line)
    } catch {
        $script:LogBroken = $true
        Write-Host 'WARNING: could not write knight_hub_install.log (folder not writable?). Continuing without a log.' -ForegroundColor Yellow
    }
}

function Initialize-Log {
    try {
        $p = [System.IO.Path]::Combine($script:GameDir, $script:NameLog)
        if ([System.IO.File]::Exists($p)) {
            $len = (New-Object System.IO.FileInfo($p)).Length
            if ($len -gt 262144) { [System.IO.File]::Delete($p) }
        }
    } catch { }
}

function Say([string]$Text) {
    Write-Host (Get-Clean $Text)
    Write-LogLine 'INFO' $Text
}
function Warn([string]$Text) {
    Write-Host ('WARNING: ' + (Get-Clean $Text)) -ForegroundColor Yellow
    Write-LogLine 'WARN' $Text
}
function Say-Error([string]$Text) {
    Write-Host (Get-Clean $Text) -ForegroundColor Red
    Write-LogLine 'ERROR' $Text
}

function Stop-Kh([int]$Code, [string]$Message) {
    $ex = New-Object System.Exception($Message)
    $ex.Data['KhCode'] = $Code
    throw $ex
}

function Get-KhCode($Ex) {
    $e = $Ex
    while ($null -ne $e) {
        try {
            if ($e.Data.Contains('KhCode')) { return [int]$e.Data['KhCode'] }
        } catch { }
        $e = $e.InnerException
    }
    return 0
}

function Get-RootEx($Ex) {
    $e = $Ex
    while ($null -ne $e.InnerException) { $e = $e.InnerException }
    return $e
}

function Get-IoCode($Ex, [int]$Default) {
    $r = Get-RootEx $Ex
    if ($r -is [System.UnauthorizedAccessException]) { return 15 }
    if ($r -is [System.IO.IOException]) {
        if ($r.Message -match 'Permission denied|Access to the path|Access is denied') { return 15 }
        $hr = $r.HResult
        if ($hr -eq -2147024784 -or $hr -eq -2147024857 -or $r.Message -match 'No space left') { return 8 }
        if ($hr -eq -2147024864 -or $hr -eq -2147024863) { return 9 }
    }
    return $Default
}

function Test-FailHook([string]$Stage) {
    $v = [Environment]::GetEnvironmentVariable('KH_FAIL_AT')
    if (-not [string]::IsNullOrEmpty($v) -and $v -eq $Stage) {
        Write-LogLine 'TEST' ('KH_FAIL_AT hook fired at stage ' + $Stage)
        if ([Environment]::GetEnvironmentVariable('KH_FAIL_MODE') -eq 'exit') {
            [Environment]::Exit(99)
        }
        Stop-Kh 99 ('Simulated failure at stage ' + $Stage + ' (KH_FAIL_AT test hook).')
    }
}

function Test-EnvOn([string]$Name) {
    $v = [Environment]::GetEnvironmentVariable($Name)
    return (-not [string]::IsNullOrEmpty($v) -and $v -ne '0')
}

# ---------------------------------------------------------------- helpers

function Get-GamePath([string]$Name) {
    return [System.IO.Path]::Combine($script:GameDir, $Name)
}

function New-TempPath([string]$Kind) {
    $g = [Guid]::NewGuid().ToString('N').Substring(0, 8)
    return [System.IO.Path]::Combine($script:GameDir, ($script:TmpPrefix + $Kind + '_' + $g))
}

function Format-MB([long]$Bytes) {
    return ([Math]::Round($Bytes / 1048576.0, 1)).ToString([System.Globalization.CultureInfo]::InvariantCulture) + ' MB'
}

function Get-Sha256Hex([string]$Path, [int]$IoCode, [string]$What) {
    $fs = $null
    $sha = $null
    $err = $null
    $hex = $null
    try {
        $share = [System.IO.FileShare]::ReadWrite -bor [System.IO.FileShare]::Delete
        $fs = New-Object System.IO.FileStream($Path, [System.IO.FileMode]::Open, [System.IO.FileAccess]::Read, $share, 1048576)
        $sha = [System.Security.Cryptography.SHA256]::Create()
        $bytes = $sha.ComputeHash($fs)
        $hex = ([System.BitConverter]::ToString($bytes)).Replace('-', '').ToLowerInvariant()
    } catch {
        $err = $_.Exception
    } finally {
        if ($null -ne $fs) { $fs.Dispose() }
        if ($null -ne $sha) { $sha.Dispose() }
    }
    if ($null -ne $err) {
        $root = Get-RootEx $err
        Write-LogLine 'DEBUG' ('hash read error for ' + $What + ': ' + $root.GetType().Name + ': ' + $root.Message)
        $code = Get-IoCode $err $IoCode
        if ($code -eq 9) {
            Stop-Kh 9 ('Cannot read ' + $What + ' because another program is using it. Close DELTARUNE (and anything else using the game folder) and run this again. Nothing was changed.')
        }
        if ($code -eq 15) {
            Stop-Kh 15 ('No permission to read ' + $What + '. Check the folder permissions. Nothing was changed.')
        }
        Stop-Kh $IoCode ('Cannot read ' + $What + ': ' + $root.Message)
    }
    return $hex
}

function Get-StreamSha256Hex($Stream) {
    $sha = [System.Security.Cryptography.SHA256]::Create()
    try {
        $bytes = $sha.ComputeHash($Stream)
        return ([System.BitConverter]::ToString($bytes)).Replace('-', '').ToLowerInvariant()
    } finally {
        $sha.Dispose()
    }
}

function Get-FileLength([string]$Path) {
    return (New-Object System.IO.FileInfo($Path)).Length
}

function Quote-Arg([string]$s) {
    return '"' + $s.Replace('"', '\"') + '"'
}

function Remove-FileQuiet([string]$Path) {
    try {
        if ([System.IO.File]::Exists($Path)) { [System.IO.File]::Delete($Path) }
        return $true
    } catch {
        Write-LogLine 'WARN' ('could not delete a file: ' + (Get-RootEx $_.Exception).Message)
        return $false
    }
}

function Remove-OwnTemps {
    # Only files whose name starts with the installer-specific prefix are touched.
    try {
        $files = [System.IO.Directory]::GetFiles($script:GameDir, ($script:TmpPrefix + '*'))
        foreach ($f in $files) {
            $leaf = [System.IO.Path]::GetFileName($f)
            if ($leaf.StartsWith($script:TmpPrefix)) {
                if (Remove-FileQuiet $f) { Write-LogLine 'INFO' ('removed temp file ' + $leaf) }
            }
        }
    } catch {
        Write-LogLine 'WARN' ('temp cleanup (game folder) problem: ' + (Get-RootEx $_.Exception).Message)
    }
    foreach ($f in @($script:ExtraTemps)) {
        $leaf = [System.IO.Path]::GetFileName($f)
        if ($leaf.StartsWith($script:TmpPrefix)) { [void](Remove-FileQuiet $f) }
    }
    $script:ExtraTemps.Clear()
}

function Confirm-Action([string]$Question) {
    if (Test-EnvOn 'KH_ASSUME_YES') {
        Write-LogLine 'INFO' ('auto-confirmed (KH_ASSUME_YES): ' + $Question)
        return $true
    }
    $answer = $null
    try {
        $answer = Read-Host ($Question + ' (type Y and press Enter to continue, anything else cancels)')
    } catch {
        $answer = $null
    }
    if ($null -eq $answer) { return $false }
    return ($answer -match '^\s*[Yy]')
}

function Get-FreeBytes([string]$Dir) {
    $ov = [Environment]::GetEnvironmentVariable('KH_FREE_BYTES_OVERRIDE')
    if (-not [string]::IsNullOrEmpty($ov)) {
        $n = [long]0
        if ([long]::TryParse($ov, [ref]$n)) { return $n }
    }
    try {
        $root = [System.IO.Path]::GetPathRoot($Dir)
        $di = New-Object System.IO.DriveInfo($root)
        return [long]$di.AvailableFreeSpace
    } catch {
        return [long]-1
    }
}

function Assert-FreeSpace([long]$Needed, [string]$Why) {
    $free = Get-FreeBytes $script:GameDir
    if ($free -lt 0) {
        Warn 'Could not determine free disk space; continuing without the space check.'
        return
    }
    Say ('Disk space: need about ' + (Format-MB $Needed) + ' (' + $Why + '), have ' + (Format-MB $free) + ' free.')
    if ($free -lt $Needed) {
        Stop-Kh 8 ('Not enough free disk space on the drive that holds the game. Needed: ' + (Format-MB $Needed) + ', free: ' + (Format-MB $free) + '. Free some space (the installer needs room for temporary files and, the first time, the data.win.vanilla backup) and run it again. Nothing was changed.')
    }
}

function Assert-Writable {
    # folder: can we create a file here?
    $probe = New-TempPath 'probe'
    $err = $null
    try {
        [System.IO.File]::WriteAllBytes($probe, [byte[]](0))
    } catch {
        $err = $_.Exception
    }
    [void](Remove-FileQuiet $probe)
    if ($null -ne $err) {
        $code = Get-IoCode $err 15
        if ($code -eq 8) { Stop-Kh 8 'The disk is full; cannot create temporary files in the game folder. Nothing was changed.' }
        Stop-Kh 15 'The game folder is not writable (permission problem). For a folder under Program Files: right-click INSTALL_KNIGHT_HUB.bat > Run as administrator, or move the game to a normal folder. Nothing was changed.'
    }
}

function Assert-DataWinExclusive {
    $dw = Get-GamePath $script:NameData
    if (-not [System.IO.File]::Exists($dw)) { return }
    $ro = $false
    try { $ro = (([int][System.IO.File]::GetAttributes($dw)) -band [int][System.IO.FileAttributes]::ReadOnly) -ne 0 } catch { $ro = $false }
    if ($ro) {
        Stop-Kh 15 'data.win is marked read-only. Right-click data.win > Properties, untick Read-only, then run this again. Nothing was changed.'
    }
    $fs = $null
    $err = $null
    try {
        $fs = New-Object System.IO.FileStream($dw, [System.IO.FileMode]::Open, [System.IO.FileAccess]::ReadWrite, [System.IO.FileShare]::None)
    } catch {
        $err = $_.Exception
    } finally {
        if ($null -ne $fs) { $fs.Dispose() }
    }
    if ($null -ne $err) {
        $root = Get-RootEx $err
        Write-LogLine 'DEBUG' ('exclusive open of data.win failed: ' + $root.GetType().Name + ': ' + $root.Message)
        if ((Get-IoCode $err 9) -eq 15) {
            Stop-Kh 15 'data.win cannot be opened for writing (it is read-only or you lack permission). Right-click data.win > Properties, untick Read-only, or fix the folder permissions, then run this again. Nothing was changed.'
        }
        Stop-Kh 9 'data.win is in use by another program (DELTARUNE is probably running). Close the game completely (check Task Manager) and run this again. Nothing was changed.'
    }
}

function Test-XdeltaStartable([string]$Exe) {
    # Make sure the program can be started at all (before anything is modified). Exit code is not judged.
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $Exe
    $psi.Arguments = '-V'
    $psi.UseShellExecute = $false
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    $psi.RedirectStandardInput = $true
    $psi.CreateNoWindow = $true
    $psi.WorkingDirectory = $script:GameDir
    $proc = $null
    $err = $null
    try {
        $proc = [System.Diagnostics.Process]::Start($psi)
        $proc.StandardInput.Close()
        $so = $proc.StandardOutput.ReadToEndAsync()
        $se = $proc.StandardError.ReadToEndAsync()
        if (-not $proc.WaitForExit(20000)) {
            try { $proc.Kill() } catch { }
            $err = 'it did not finish within 20 seconds'
        }
    } catch {
        $err = (Get-RootEx $_.Exception).Message
    } finally {
        if ($null -ne $proc) { $proc.Dispose() }
    }
    if ($null -ne $err) {
        Stop-Kh 3 ('xdelta3 could not be started: ' + $err + ' (the file may be damaged or not a Windows program). Re-copy xdelta3.exe from the package. Nothing was changed.')
    }
}

# ---------------------------------------------------------------- manifest

function Test-Sha([string]$s) { return ($s -match '^[0-9a-fA-F]{64}$') }

function Parse-Long([string]$s, [string]$Key) {
    $n = [long]0
    if (-not [long]::TryParse($s, [System.Globalization.NumberStyles]::None, [System.Globalization.CultureInfo]::InvariantCulture, [ref]$n)) {
        Stop-Kh 4 ('Manifest: value for ' + $Key + ' is not a number.')
    }
    return $n
}

function Read-Manifest {
    $path = Get-GamePath $script:NameManifest
    if (-not [System.IO.File]::Exists($path)) {
        Stop-Kh 4 ($script:NameManifest + ' is missing. Put ALL files of the Knight Hub package in the same folder as this installer (the DELTARUNE chapter3_windows folder). Nothing was changed.')
    }
    $lines = $null
    try { $lines = [System.IO.File]::ReadAllLines($path) } catch { Stop-Kh 4 ('Cannot read ' + $script:NameManifest + '.') }
    $kv = @{}
    $partMap = @{}
    $music = New-Object System.Collections.ArrayList
    $steam = New-Object System.Collections.ArrayList
    $ln = 0
    foreach ($raw in $lines) {
        $ln++
        $line = $raw.Trim()
        if ($ln -eq 1 -and $line.Length -gt 0 -and [int][char]$line[0] -eq 65279) { $line = $line.Substring(1).Trim() }
        if ($line.Length -eq 0 -or $line.StartsWith('#')) { continue }
        $i = $line.IndexOf('=')
        if ($i -lt 1) { Stop-Kh 4 ('Manifest line ' + $ln + ' is not key=value.') }
        $key = $line.Substring(0, $i).Trim()
        $val = $line.Substring($i + 1).Trim()
        if ($key -eq 'music') {
            [void]$music.Add($val)
        } elseif ($key -eq 'steam') {
            [void]$steam.Add($val)
        } elseif ($key -match '^part\.(\d{1,4})$') {
            $idx = [int]$Matches[1]
            if ($partMap.ContainsKey($idx)) { Stop-Kh 4 ('Manifest: duplicate ' + $key + '.') }
            $partMap[$idx] = $val
        } else {
            if ($kv.ContainsKey($key)) { Stop-Kh 4 ('Manifest: duplicate key ' + $key + '.') }
            $kv[$key] = $val
        }
    }
    foreach ($req in @('schema', 'mod_version', 'vanilla_size', 'vanilla_sha256', 'patched_size', 'patched_sha256', 'xdelta_name', 'xdelta_size', 'xdelta_sha256', 'part_count')) {
        if (-not $kv.ContainsKey($req)) { Stop-Kh 4 ('Manifest: required key ' + $req + ' is missing.') }
    }
    if ($kv['schema'] -ne '1') { Stop-Kh 4 ('Manifest schema ' + $kv['schema'] + ' is not supported by this installer (expected 1). Use the installer that came with this manifest.') }
    foreach ($k in @('vanilla_sha256', 'patched_sha256', 'xdelta_sha256')) {
        if (-not (Test-Sha $kv[$k])) { Stop-Kh 4 ('Manifest: ' + $k + ' is not a SHA256.') }
    }
    $exeSha = ''
    if ($kv.ContainsKey('xdelta3_exe_sha256') -and $kv['xdelta3_exe_sha256'].Length -gt 0) {
        if (-not (Test-Sha $kv['xdelta3_exe_sha256'])) { Stop-Kh 4 'Manifest: xdelta3_exe_sha256 is not a SHA256.' }
        $exeSha = $kv['xdelta3_exe_sha256'].ToLowerInvariant()
    }
    if ($kv['xdelta_name'] -notmatch '^[A-Za-z0-9][A-Za-z0-9._-]*$') { Stop-Kh 4 'Manifest: xdelta_name is not a plain file name.' }
    $pc = [int](Parse-Long $kv['part_count'] 'part_count')
    if ($pc -lt 1 -or $pc -gt 999) { Stop-Kh 4 'Manifest: part_count out of range.' }
    if ($partMap.Count -ne $pc) { Stop-Kh 4 ('Manifest: part_count is ' + $pc + ' but ' + $partMap.Count + ' part.N lines were found.') }
    $parts = New-Object System.Collections.ArrayList
    $seen = @{}
    $sum = [long]0
    for ($i = 0; $i -lt $pc; $i++) {
        if (-not $partMap.ContainsKey($i)) { Stop-Kh 4 ('Manifest: part.' + $i + ' is missing (parts must be numbered 0..' + ($pc - 1) + ').') }
        $f = $partMap[$i].Split('|')
        if ($f.Length -ne 3) { Stop-Kh 4 ('Manifest: part.' + $i + ' must be name|size|sha256.') }
        $pn = $f[0].Trim()
        if ($pn -notmatch '^[A-Za-z0-9][A-Za-z0-9._-]*$') { Stop-Kh 4 ('Manifest: part.' + $i + ' name is not a plain file name.') }
        if ($seen.ContainsKey($pn.ToLowerInvariant())) { Stop-Kh 4 ('Manifest: part name used twice: ' + $pn) }
        $seen[$pn.ToLowerInvariant()] = $true
        $psz = Parse-Long $f[1].Trim() ('part.' + $i)
        if (-not (Test-Sha $f[2].Trim())) { Stop-Kh 4 ('Manifest: part.' + $i + ' checksum is not a SHA256.') }
        $sum += $psz
        [void]$parts.Add([pscustomobject]@{ Index = $i; Name = $pn; Size = $psz; Sha = $f[2].Trim().ToLowerInvariant() })
    }
    $xs = Parse-Long $kv['xdelta_size'] 'xdelta_size'
    if ($sum -ne $xs) { Stop-Kh 4 'Manifest: part sizes do not add up to xdelta_size.' }
    $musicList = New-Object System.Collections.ArrayList
    foreach ($mv in $music) {
        $f = $mv.Split('|')
        $rel = $f[0].Trim()
        $msha = ''
        if ($f.Length -ge 2) { $msha = $f[1].Trim().ToLowerInvariant() }
        if ($f.Length -gt 2 -or ($msha.Length -gt 0 -and -not (Test-Sha $msha))) { Stop-Kh 4 ('Manifest: bad music entry: ' + $mv) }
        if ($rel -notmatch '^[^/\\:*?"<>|]+(/[^/\\:*?"<>|]+)*$') { Stop-Kh 4 ('Manifest: bad music path: ' + $rel) }
        foreach ($seg in $rel.Split('/')) {
            if ($seg -eq '.' -or $seg -eq '..') { Stop-Kh 4 ('Manifest: bad music path: ' + $rel) }
        }
        [void]$musicList.Add([pscustomobject]@{ Rel = $rel; Sha = $msha })
    }
    $steamList = New-Object System.Collections.ArrayList
    foreach ($sv in $steam) {
        $f = $sv.Split('|')
        if ($f.Length -ne 2) { Stop-Kh 4 ('Manifest: bad steam entry: ' + $sv) }
        $sn = $f[0].Trim()
        $ssha = $f[1].Trim().ToLowerInvariant()
        if ($sn -notmatch '^[A-Za-z0-9][A-Za-z0-9._-]*$' -or -not (Test-Sha $ssha)) { Stop-Kh 4 ('Manifest: bad steam entry: ' + $sv) }
        [void]$steamList.Add([pscustomobject]@{ Name = $sn; Sha = $ssha })
    }
    $modName = 'Knight Hub'
    if ($kv.ContainsKey('mod_name') -and $kv['mod_name'].Length -gt 0) { $modName = $kv['mod_name'] }
    return [pscustomobject]@{
        ModName = $modName
        ModVersion = $kv['mod_version']
        VanillaSize = (Parse-Long $kv['vanilla_size'] 'vanilla_size')
        VanillaSha = $kv['vanilla_sha256'].ToLowerInvariant()
        PatchedSize = (Parse-Long $kv['patched_size'] 'patched_size')
        PatchedSha = $kv['patched_sha256'].ToLowerInvariant()
        XdeltaName = $kv['xdelta_name']
        XdeltaSize = $xs
        XdeltaSha = $kv['xdelta_sha256'].ToLowerInvariant()
        Parts = $parts
        ExeSha = $exeSha
        Music = $musicList
        Steam = $steamList
    }
}

# ---------------------------------------------------------------- installed build marker (build 52)

function Write-BuildMarker($Man) {
    $p = Get-GamePath $script:NameMarker
    $t = '# Knight Hub: the build installed in data.win (written by the installer). Older packages leave this data.win alone.' + "`r`n" +
        'mod_version=' + $Man.ModVersion + "`r`n" + 'patched_size=' + $Man.PatchedSize + "`r`n" + 'patched_sha256=' + $Man.PatchedSha + "`r`n"
    try { [System.IO.File]::WriteAllText($p, $t, (New-Object System.Text.UTF8Encoding($false))) }
    catch { Write-LogLine 'WARN' ('could not write ' + $script:NameMarker + ': ' + $_.Exception.Message) }
}

# the build of the Knight Hub in data.win according to the marker, when the marker matches data.win exactly; else -1
function Get-MarkedBuild([string]$DataWin) {
    $p = Get-GamePath $script:NameMarker
    if (-not [System.IO.File]::Exists($p)) { return -1 }
    $kv = @{}
    try {
        foreach ($ln in [System.IO.File]::ReadAllLines($p)) {
            $i = $ln.IndexOf('=')
            if ($ln.StartsWith('#') -or $i -lt 1) { continue }
            $kv[$ln.Substring(0, $i).Trim()] = $ln.Substring($i + 1).Trim()
        }
    } catch { return -1 }
    if (-not ($kv.ContainsKey('mod_version') -and $kv.ContainsKey('patched_size') -and $kv.ContainsKey('patched_sha256'))) { return -1 }
    $v = 0
    $sz = [long]0
    if (-not [int]::TryParse($kv['mod_version'], [ref]$v)) { return -1 }
    if (-not [long]::TryParse($kv['patched_size'], [ref]$sz)) { return -1 }
    if ((Get-FileLength $DataWin) -ne $sz) { return -1 }
    $h = Get-Sha256Hex $DataWin 9 'data.win'
    if ($h -ne $kv['patched_sha256'].ToLowerInvariant()) { return -1 }
    return $v
}

# ---------------------------------------------------------------- classification / backup

function Get-FileClass($Man, [string]$Path, [string]$What) {
    $len = Get-FileLength $Path
    if ($len -ne $Man.VanillaSize -and $len -ne $Man.PatchedSize) {
        return [pscustomobject]@{ Class = 'unknown'; Size = $len; Sha = '' }
    }
    $h = Get-Sha256Hex $Path 9 $What
    $c = 'unknown'
    if ($len -eq $Man.VanillaSize -and $h -eq $Man.VanillaSha) { $c = 'vanilla' }
    elseif ($len -eq $Man.PatchedSize -and $h -eq $Man.PatchedSha) { $c = 'installed' }
    return [pscustomobject]@{ Class = $c; Size = $len; Sha = $h }
}

function Get-BackupState($Man) {
    # none | valid | invalid
    $bk = Get-GamePath $script:NameBackup
    if (-not [System.IO.File]::Exists($bk)) { return 'none' }
    $len = Get-FileLength $bk
    if ($len -ne $Man.VanillaSize) {
        Write-LogLine 'INFO' ('data.win.vanilla size ' + $len + ' does not match vanilla size ' + $Man.VanillaSize)
        return 'invalid'
    }
    $h = Get-Sha256Hex $bk 11 'data.win.vanilla'
    if ($h -eq $Man.VanillaSha) { return 'valid' }
    Write-LogLine 'INFO' ('data.win.vanilla sha256 ' + $h + ' differs from vanilla ' + $Man.VanillaSha)
    return 'invalid'
}

function Stop-UnsupportedDataWin([string]$BackupState) {
    $l = New-Object System.Collections.ArrayList
    [void]$l.Add('Your data.win is NOT a file this installer supports. It is neither the unmodified DELTARUNE Chapter 3 v0.0.105 data.win nor an already-installed Knight Hub.')
    [void]$l.Add('It is probably modded by something else (another mod, or an older Knight Hub build) or it is a different game version. The installer did NOT change anything.')
    [void]$l.Add('')
    [void]$l.Add('How to get a clean data.win:')
    if ($BackupState -eq 'valid') {
        [void]$l.Add('  1) A valid backup exists (data.win.vanilla). Double-click RESTORE_VANILLA.bat to put it back, then run INSTALL_KNIGHT_HUB.bat again.')
    } else {
        [void]$l.Add('  1) If you made a backup called data.win.vanilla with this installer, double-click RESTORE_VANILLA.bat (it checks the backup first).')
    }
    [void]$l.Add('  2) Otherwise let Steam restore the original: Steam > Library > right-click DELTARUNE > Properties > Installed Files > "Verify integrity of game files".')
    [void]$l.Add('     Wait until Steam says it is finished, then run INSTALL_KNIGHT_HUB.bat again. (This installer does not start the Steam check for you.)')
    [void]$l.Add('     Note: Steam verification also reverts other modded game files, and if the game has been updated past v0.0.105 this mod will not fit that newer version.')
    Stop-Kh 6 ($l -join "`n")
}

# ---------------------------------------------------------------- xdelta3

function Resolve-Xdelta($Man) {
    $kx = [Environment]::GetEnvironmentVariable('KH_XDELTA')
    if (-not [string]::IsNullOrEmpty($kx)) {
        if (-not [System.IO.File]::Exists($kx)) { Stop-Kh 3 'KH_XDELTA points to a file that does not exist.' }
        Write-LogLine 'INFO' 'using xdelta3 from KH_XDELTA (hash check skipped)'
        return $kx
    }
    $exe = Get-GamePath 'xdelta3.exe'
    if (-not [System.IO.File]::Exists($exe)) {
        Stop-Kh 3 'xdelta3.exe is missing. It must be in the same folder as this installer (it is part of the Knight Hub package). Copy xdelta3.exe from the package next to INSTALL_KNIGHT_HUB.bat and run it again. The installer never downloads anything. Nothing was changed.'
    }
    if ($Man.ExeSha.Length -gt 0) {
        $h = Get-Sha256Hex $exe 3 'xdelta3.exe'
        if ($h -ne $Man.ExeSha) {
            Stop-Kh 3 'xdelta3.exe is not the copy that belongs to this package (checksum mismatch). Re-copy xdelta3.exe from the package. Nothing was changed.'
        }
    }
    return $exe
}

function Invoke-Xdelta([string]$Exe, [string]$Src, [string]$Patch, [string]$Out) {
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $Exe
    $psi.Arguments = '-d -s ' + (Quote-Arg $Src) + ' ' + (Quote-Arg $Patch) + ' ' + (Quote-Arg $Out)
    $psi.UseShellExecute = $false
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    $psi.RedirectStandardInput = $true
    $psi.CreateNoWindow = $true
    $psi.WorkingDirectory = $script:GameDir
    $proc = $null
    try {
        $proc = [System.Diagnostics.Process]::Start($psi)
    } catch {
        Stop-Kh 3 ('xdelta3 could not be started: ' + (Get-RootEx $_.Exception).Message + ' (the file may be damaged or not a Windows program). Nothing was changed.')
    }
    try {
        $proc.StandardInput.Close()
        $so = $proc.StandardOutput.ReadToEndAsync()
        $se = $proc.StandardError.ReadToEndAsync()
        $proc.WaitForExit()
        $code = $proc.ExitCode
        $txt = ($se.Result + ' ' + $so.Result).Trim()
        if ($txt.Length -gt 1500) { $txt = $txt.Substring(0, 1500) }
        return [pscustomobject]@{ ExitCode = $code; Text = $txt }
    } finally {
        $proc.Dispose()
    }
}

# ---------------------------------------------------------------- patch parts

function Test-Parts($Man) {
    $missing = New-Object System.Collections.ArrayList
    foreach ($p in $Man.Parts) {
        if (-not [System.IO.File]::Exists((Get-GamePath $p.Name))) { [void]$missing.Add($p.Name) }
    }
    if ($missing.Count -gt 0) {
        Stop-Kh 5 ('Patch part file(s) missing: ' + ($missing -join ', ') + '. Put every part of the package (' + $Man.Parts[0].Name + ' ... ' + $Man.Parts[$Man.Parts.Count - 1].Name + ') in the same folder as this installer, then run it again. Nothing was changed.')
    }
    foreach ($p in $Man.Parts) {
        $path = Get-GamePath $p.Name
        $len = Get-FileLength $path
        if ($len -ne $p.Size) {
            Stop-Kh 5 ('Patch part ' + $p.Name + ' has the wrong size (' + $len + ' bytes, expected ' + $p.Size + '). The download or copy is incomplete or damaged. Get the file again and replace it. Nothing was changed.')
        }
        $h = Get-Sha256Hex $path 5 $p.Name
        if ($h -ne $p.Sha) {
            Stop-Kh 5 ('Patch part ' + $p.Name + ' is damaged or is the wrong file (checksum mismatch). Get the file again and replace it. Nothing was changed.')
        }
        Write-LogLine 'INFO' ('part ok: ' + $p.Name)
    }
}

function Join-Parts($Man, [string]$OutPath) {
    $outStream = $null
    $err = $null
    try {
        $outStream = New-Object System.IO.FileStream($OutPath, [System.IO.FileMode]::CreateNew, [System.IO.FileAccess]::Write, [System.IO.FileShare]::None, 1048576)
        foreach ($p in $Man.Parts) {
            $inStream = New-Object System.IO.FileStream((Get-GamePath $p.Name), [System.IO.FileMode]::Open, [System.IO.FileAccess]::Read, [System.IO.FileShare]::Read, 1048576)
            try { $inStream.CopyTo($outStream, 1048576) } finally { $inStream.Dispose() }
        }
        $outStream.Flush()
    } catch {
        $err = $_.Exception
    } finally {
        if ($null -ne $outStream) { $outStream.Dispose() }
    }
    if ($null -ne $err) {
        $root = Get-RootEx $err
        Stop-Kh (Get-IoCode $err 5) ('Could not join the patch parts: ' + $root.Message)
    }
    $len = Get-FileLength $OutPath
    if ($len -ne $Man.XdeltaSize) { Stop-Kh 5 ('Joined patch has the wrong size (' + $len + ', expected ' + $Man.XdeltaSize + '). Nothing was changed.') }
    $h = Get-Sha256Hex $OutPath 5 'the joined patch'
    if ($h -ne $Man.XdeltaSha) { Stop-Kh 5 'Joined patch has the wrong checksum. The parts do not form the expected patch (wrong order or wrong files). Nothing was changed.' }
}

# ---------------------------------------------------------------- recoverable replacement

function Invoke-Swap([string]$TmpPath, [long]$ExpectedSize, [string]$ExpectedSha) {
    $dw = Get-GamePath $script:NameData
    $prev = Get-GamePath $script:NamePrev
    $Man = $script:Manifest

    if ([System.IO.File]::Exists($prev)) {
        # leftover from an interrupted run: only delete it if it is a known regenerable file
        $pi = Get-FileClass $Man $prev 'data.win.knighthub_prev'
        if ($pi.Class -eq 'unknown') {
            Stop-Kh 11 'A file named data.win.knighthub_prev is in the game folder and it is not a recognised DELTARUNE file. It may be your only copy of an older data.win, so the installer will not delete it. Move or rename it, then run this again. Nothing was changed.'
        }
        Say 'Removing a leftover data.win.knighthub_prev from an earlier interrupted run.'
        if (-not (Remove-FileQuiet $prev)) {
            Stop-Kh 15 'Could not remove the leftover data.win.knighthub_prev. Nothing was changed.'
        }
    }

    $hadActive = [System.IO.File]::Exists($dw)
    $moved = $false
    $caught = $null
    try {
        if ($hadActive) {
            $mvErr = $null
            try {
                [System.IO.File]::Move($dw, $prev)
            } catch {
                $mvErr = $_.Exception
            }
            if ($null -ne $mvErr) {
                if ((Get-IoCode $mvErr 9) -eq 15) { Stop-Kh 15 'Cannot rename data.win (permission denied). Nothing was changed.' }
                Stop-Kh 9 'Cannot rename data.win (it is in use - close DELTARUNE). Nothing was changed.'
            }
            $moved = $true
            Write-LogLine 'INFO' 'data.win renamed to data.win.knighthub_prev'
        }
        Test-FailHook 'after_prev_rename'
        $mvErr = $null
        try {
            [System.IO.File]::Move($TmpPath, $dw)
        } catch {
            $mvErr = $_.Exception
        }
        if ($null -ne $mvErr) {
            Stop-Kh (Get-IoCode $mvErr 11) ('Could not move the new file into place: ' + (Get-RootEx $mvErr).Message)
        }
        Write-LogLine 'INFO' 'new file moved to data.win'
        Test-FailHook 'after_move'
        Say 'Verifying the new data.win ...'
        $len = Get-FileLength $dw
        $h = ''
        if ($len -eq $ExpectedSize) { $h = Get-Sha256Hex $dw 12 'the new data.win' }
        if ($len -ne $ExpectedSize -or $h -ne $ExpectedSha) {
            Stop-Kh 12 'The new data.win failed the final check (size/checksum mismatch).'
        }
        Test-FailHook 'after_final_verify'
    } catch {
        $caught = $_.Exception
    }
    if ($null -ne $caught) {
        $code = Get-KhCode $caught
        if ($code -eq 0) { $code = 11 }
        $msg = $caught.Message
        if ((Get-KhCode $caught) -eq 0) { $msg = (Get-RootEx $caught).Message }
        Write-LogLine 'ERROR' ('swap failed (code ' + $code + '): ' + $msg)
        $suffix = ''
        if ($moved) {
            $rbErr = $null
            try {
                if ([System.IO.File]::Exists($dw)) { [System.IO.File]::Delete($dw) }
                [System.IO.File]::Move($prev, $dw)
            } catch {
                $rbErr = (Get-RootEx $_.Exception).Message
            }
            if ($null -ne $rbErr) {
                Stop-Kh 16 ('CRITICAL: the replacement failed AND the previous data.win could not be put back automatically (' + $rbErr + '). Your previous file is saved as data.win.knighthub_prev in the game folder. To fix it by hand: delete data.win if it exists, then rename data.win.knighthub_prev to data.win (or use Steam "Verify integrity of game files"). Original error: ' + $msg)
            }
            Say 'The previous data.win has been put back.'
            $suffix = ' The previous data.win was put back; your game is as it was before.'
        }
        Stop-Kh $code ($msg + $suffix)
    }
    # commit: the old file is no longer needed
    if ($hadActive) {
        if (-not (Remove-FileQuiet $prev)) {
            Warn 'Installed OK, but could not delete data.win.knighthub_prev (a leftover). You can delete it yourself; the next run will clean it up.'
        }
    }
}

# ---------------------------------------------------------------- music

function Find-ZipEntry($Zip, [string]$Rel) {
    $want = $Rel.ToLowerInvariant()
    foreach ($e in $Zip.Entries) {
        $n = $e.FullName.Replace('\', '/').ToLowerInvariant()
        if ($n.EndsWith('/')) { continue }
        if ($n -eq $want -or $n -eq ('mus/' + $want) -or $n.EndsWith('/mus/' + $want)) { return $e }
    }
    return $null
}

function Install-Music($Man) {
    if ($Man.Music.Count -eq 0) { Say 'No optional music listed in the manifest.'; return }
    $musDir = ''
    try { $musDir = [System.IO.Path]::GetFullPath([System.IO.Path]::Combine($script:GameDir, '..', 'mus')) } catch { Warn 'Could not work out the mus folder; skipping music.'; return }
    $sep = [System.IO.Path]::DirectorySeparatorChar
    # the zips the music may be in (opened when first needed), in this order
    $zips = New-Object System.Collections.ArrayList
    foreach ($zn in @($script:NameExtras, $script:NameMusic, $script:NameMusic2, $script:NameMusic3, $script:NameMusic4)) {
        [void]$zips.Add([pscustomobject]@{ Name = $zn; Path = (Get-GamePath $zn); Zip = $null; Tried = $false; Ok = $false })
    }
    $placed = 0; $same = 0; $kept = 0; $missing = 0
    try {
        foreach ($mu in $Man.Music) {
            $relOs = $mu.Rel.Replace('/', [string]$sep)
            $dest = [System.IO.Path]::Combine($musDir, $relOs)
            $leaf = [System.IO.Path]::GetFileName($dest)
            try {
                if ($leaf.ToLowerInvariant() -eq 'kaizoknight.ogg' -and [System.IO.File]::Exists($dest)) {
                    Say ('Music: keeping your existing ' + $mu.Rel + ' (never overwritten).')
                    $kept++
                    continue
                }
                $srcFile = $null
                foreach ($cand in @((Get-GamePath $relOs), (Get-GamePath ('mus' + $sep + $relOs)))) {
                    if ([System.IO.File]::Exists($cand)) { $srcFile = $cand; break }
                }
                $entry = $null
                if ($null -eq $srcFile) {
                    foreach ($zr in $zips) {
                        if ($null -ne $entry) { break }
                        if (-not [System.IO.File]::Exists($zr.Path)) { continue }
                        if (-not $zr.Tried) {
                            $zr.Tried = $true
                            try {
                                Add-Type -AssemblyName System.IO.Compression
                                Add-Type -AssemblyName System.IO.Compression.FileSystem
                                $zr.Zip = [System.IO.Compression.ZipFile]::OpenRead($zr.Path)
                                $zr.Ok = $true
                            } catch {
                                Warn ('Could not open ' + $zr.Name + ' (' + (Get-RootEx $_.Exception).Message + ').')
                            }
                        }
                        if ($zr.Ok) { $entry = Find-ZipEntry $zr.Zip $mu.Rel }
                    }
                }
                if ($null -eq $srcFile -and $null -eq $entry) {
                    Warn ('Optional music file not found: ' + $mu.Rel + ' (put it beside the installer, or inside ' + $script:NameExtras + ' / ' + $script:NameMusic + ' / ' + $script:NameMusic2 + ' / ' + $script:NameMusic3 + ' / ' + $script:NameMusic4 + '). If that song is picked, the fight plays its own music instead.')
                    $missing++
                    continue
                }
                $srcHash = ''
                if ($null -ne $srcFile) {
                    $srcHash = Get-Sha256Hex $srcFile 11 $mu.Rel
                } else {
                    $es = $entry.Open()
                    try { $srcHash = Get-StreamSha256Hex $es } finally { $es.Dispose() }
                }
                if ($mu.Sha.Length -gt 0 -and $srcHash -ne $mu.Sha) {
                    Warn ('Music file ' + $mu.Rel + ' does not match the expected checksum (damaged or a different file); skipped.')
                    $missing++
                    continue
                }
                $overwrite = $false
                if ([System.IO.File]::Exists($dest)) {
                    $dh = Get-Sha256Hex $dest 11 ('existing ' + $mu.Rel)
                    if ($dh -eq $srcHash) {
                        Say ('Music: ' + $mu.Rel + ' already present (identical), skipped.')
                        $same++
                        continue
                    }
                    if (-not $OverwriteMusic) {
                        Warn ('Music: ' + $mu.Rel + ' already exists and differs from the package; left as it is. Run with -OverwriteMusic to replace it.')
                        $kept++
                        continue
                    }
                    $overwrite = $true
                }
                $destDir = [System.IO.Path]::GetDirectoryName($dest)
                [void][System.IO.Directory]::CreateDirectory($destDir)
                $tmp = [System.IO.Path]::Combine($destDir, ($script:TmpPrefix + 'mus_' + [Guid]::NewGuid().ToString('N').Substring(0, 8)))
                [void]$script:ExtraTemps.Add($tmp)
                if ($null -ne $srcFile) {
                    [System.IO.File]::Copy($srcFile, $tmp, $false)
                } else {
                    $es = $entry.Open()
                    $os = New-Object System.IO.FileStream($tmp, [System.IO.FileMode]::CreateNew, [System.IO.FileAccess]::Write, [System.IO.FileShare]::None)
                    try { $es.CopyTo($os, 1048576) } finally { $os.Dispose(); $es.Dispose() }
                }
                $th = Get-Sha256Hex $tmp 11 'a temporary music file'
                if ($th -ne $srcHash) { throw 'copied music file failed verification' }
                if ($overwrite) { [System.IO.File]::Delete($dest) }
                [System.IO.File]::Move($tmp, $dest)
                Say ('Music: installed ' + $mu.Rel)
                $placed++
            } catch {
                Warn ('Music: could not install ' + $mu.Rel + ': ' + (Get-RootEx $_.Exception).Message)
                $missing++
            }
        }
    } finally {
        foreach ($zr in $zips) { if ($zr.Ok) { $zr.Zip.Dispose() } }
    }
    Say ('Music summary: ' + $placed + ' installed, ' + $same + ' already present, ' + $kept + ' kept as is, ' + $missing + ' missing/skipped (optional).')
    if ($missing -gt 0) {
        Warn 'Some optional music is missing. The mod works without it (the affected fights use their default music).'
    }
}

# ---------------------------------------------------------------- stale prev handling

function Invoke-RecoverMissingDataWin {
    $dw = Get-GamePath $script:NameData
    $prev = Get-GamePath $script:NamePrev
    if (-not [System.IO.File]::Exists($dw) -and [System.IO.File]::Exists($prev)) {
        Say 'data.win is missing but data.win.knighthub_prev exists (an earlier run was interrupted). Putting your previous data.win back ...'
        $err = $null
        try {
            [System.IO.File]::Move($prev, $dw)
        } catch {
            $err = $_.Exception
        }
        if ($null -ne $err) {
            Stop-Kh (Get-IoCode $err 16) ('Could not rename data.win.knighthub_prev back to data.win: ' + (Get-RootEx $err).Message + '. Please rename it by hand.')
        }
        Say 'Recovered: data.win restored from the interrupted run.'
    }
}

function Invoke-CleanStalePrev($Man) {
    $prev = Get-GamePath $script:NamePrev
    if ([System.IO.File]::Exists($prev)) {
        $pi = Get-FileClass $Man $prev 'data.win.knighthub_prev'
        if ($pi.Class -ne 'unknown') {
            Say 'Removing a leftover data.win.knighthub_prev (the active data.win is fine).'
            [void](Remove-FileQuiet $prev)
        } else {
            Warn 'data.win.knighthub_prev exists and is not a recognised file; leaving it alone.'
        }
    }
}

# ---------------------------------------------------------------- install

function Invoke-Install {
    $dw = Get-GamePath $script:NameData
    $mode = 'install'
    if ($Force) { $mode = 'install (force)' }
    Say ('Knight Hub installer ' + $script:KhVersion + ' - mode: ' + $mode)
    Invoke-RecoverMissingDataWin
    if (-not [System.IO.File]::Exists($dw)) {
        Stop-Kh 2 'data.win was not found next to this installer. Put INSTALL_KNIGHT_HUB.bat, install_knight_hub.ps1 and all package files in your DELTARUNE chapter3_windows folder (Steam: right-click DELTARUNE > Manage > Browse local files, then open chapter3_windows), then run it from there.'
    }
    if ([System.IO.Path]::GetFileName($script:GameDir) -ne 'chapter3_windows') {
        Warn 'This folder is not named chapter3_windows. If this is not your Chapter 3 game folder, the installer will refuse a wrong data.win anyway.'
    }
    $Man = Read-Manifest
    $script:Manifest = $Man
    Say ('Package: ' + $Man.ModName + ' ' + $Man.ModVersion + ', ' + $Man.Parts.Count + ' patch part(s).')

    Say 'Checking data.win (this takes a few seconds) ...'
    $info = Get-FileClass $Man $dw 'data.win'
    Say ('data.win is: ' + $info.Class + ' (size ' + (Format-MB $info.Size) + ')')
    $bstate = Get-BackupState $Man
    Write-LogLine 'INFO' ('backup state: ' + $bstate)

    $needBackup = $false
    if ($info.Class -eq 'unknown') {
        # build 52: a newer Knight Hub than this package is installed: an older folder's PLAY / INSTALL must not replace it
        $mb = Get-MarkedBuild $dw
        $pv = 0
        [void][int]::TryParse([string]$Man.ModVersion, [ref]$pv)
        if ($mb -gt $pv) {
            Stop-Kh 17 ('A NEWER Knight Hub is installed (build ' + $mb + ') than this package (build ' + $Man.ModVersion + '), so this older package did not touch it. Use the newest Knight Hub folder (PLAY_KNIGHT_HUB.bat there). To go back to build ' + $Man.ModVersion + ' on purpose: RESTORE_VANILLA.bat, then this INSTALL_KNIGHT_HUB.bat. Nothing was changed.')
        }
        Stop-UnsupportedDataWin $bstate
    }
    if ($info.Class -eq 'installed') {
        if (-not $Force) {
            Say 'Knight Hub is already installed in this data.win. Nothing to do (use -Force to reinstall).'
            if ($bstate -eq 'invalid') { Warn 'data.win.vanilla exists but is NOT a valid vanilla file; RESTORE_VANILLA will refuse to use it.' }
            if ($bstate -eq 'none') { Warn 'There is no data.win.vanilla backup, so RESTORE_VANILLA cannot work. Use Steam "Verify integrity of game files" to get the original back if you need it.' }
            Invoke-CleanStalePrev $Man
            Write-BuildMarker $Man
            Install-Music $Man
            Install-KfSongs
            Test-SteamFiles $Man
            return 0
        }
        if ($bstate -ne 'valid') {
            $why = 'not a valid vanilla file'
            if ($bstate -eq 'none') { $why = 'missing' }
            Stop-Kh 13 ('Cannot reinstall: a valid data.win.vanilla backup is needed as the patch source, and it is ' + $why + '. Use Steam "Verify integrity of game files" to restore the original data.win, then run the installer again.')
        }
        Say 'Reinstalling (-Force) using the valid data.win.vanilla backup as the patch source.'
    } else {
        if ($bstate -eq 'invalid') {
            Stop-Kh 7 'data.win.vanilla exists but it is NOT the unmodified vanilla file (wrong size or checksum), so it will not be used and not overwritten. Your current data.win IS verified vanilla. To continue, rename or delete data.win.vanilla yourself (it is probably an old modded file) and run this again; a fresh backup will be made from your current data.win. Nothing was changed.'
        }
        if ($bstate -eq 'none') { $needBackup = $true }
    }

    # ---- preflight (nothing modified yet)
    $xd = Resolve-Xdelta $Man
    Test-XdeltaStartable $xd
    Say 'Checking patch parts ...'
    Test-Parts $Man
    $need = $Man.XdeltaSize + $Man.PatchedSize
    $needWhy = 'joined patch + new data.win'
    if ($needBackup) { $need += $Man.VanillaSize; $needWhy = $needWhy + ' + backup' }
    $need += [long]($Man.PatchedSize * 0.05) + 1048576
    Assert-FreeSpace $need $needWhy
    if (-not (Confirm-Action 'Install Knight Hub now? Your data.win will be replaced (a backup of the original is kept as data.win.vanilla).')) {
        Stop-Kh 14 'Cancelled. Nothing was changed.'
    }
    Assert-Writable
    Assert-DataWinExclusive
    Remove-OwnTemps

    # ---- join parts
    Say 'Joining patch parts ...'
    $tj = New-TempPath 'join'
    Join-Parts $Man $tj
    Say 'Joined patch verified.'
    Test-FailHook 'after_join'

    # ---- backup
    $bk = Get-GamePath $script:NameBackup
    if ($needBackup) {
        Say 'Creating the vanilla backup data.win.vanilla ...'
        $tb = New-TempPath 'backup'
        $cpErr = $null
        try {
            [System.IO.File]::Copy($dw, $tb, $false)
        } catch {
            $cpErr = $_.Exception
        }
        if ($null -ne $cpErr) {
            Stop-Kh (Get-IoCode $cpErr 11) ('Could not copy data.win to make the backup: ' + (Get-RootEx $cpErr).Message)
        }
        $h = Get-Sha256Hex $tb 11 'the backup copy'
        if ($h -ne $Man.VanillaSha) { Stop-Kh 11 'The backup copy did not verify (data.win changed while copying?). Nothing was changed.' }
        $cpErr = $null
        try { [System.IO.File]::Move($tb, $bk) } catch { $cpErr = $_.Exception }
        if ($null -ne $cpErr) { Stop-Kh (Get-IoCode $cpErr 11) ('Could not create data.win.vanilla: ' + (Get-RootEx $cpErr).Message) }
        Say 'Backup created and verified.'
        Test-FailHook 'after_backup'
    } else {
        Say 'Using the existing verified data.win.vanilla as the patch source.'
    }

    # ---- patch
    Say 'Patching (this can take a minute) ...'
    $to = New-TempPath 'out'
    $r = Invoke-Xdelta $xd $bk $tj $to
    if ($r.ExitCode -ne 0) {
        Write-LogLine 'ERROR' ('xdelta3 exit code ' + $r.ExitCode + ': ' + $r.Text)
        Stop-Kh 10 ('xdelta3 failed (exit code ' + $r.ExitCode + '). ' + $r.Text + ' Your data.win was not changed.')
    }
    Write-LogLine 'INFO' 'xdelta3 exit code 0'
    Test-FailHook 'after_patch'
    if (-not [System.IO.File]::Exists($to)) { Stop-Kh 10 'xdelta3 reported success but produced no output file. Your data.win was not changed.' }
    $olen = Get-FileLength $to
    if ($olen -ne $Man.PatchedSize) { Stop-Kh 10 ('The patched file has the wrong size (' + $olen + ', expected ' + $Man.PatchedSize + '). Your data.win was not changed.') }
    $oh = Get-Sha256Hex $to 10 'the patched file'
    if ($oh -ne $Man.PatchedSha) { Stop-Kh 10 'The patched file failed the checksum check. Your data.win was not changed.' }
    Say 'Patched file verified.'
    [void](Remove-FileQuiet $tj)
    Test-FailHook 'after_verify_output'

    # ---- swap
    Say 'Replacing data.win ...'
    Invoke-Swap $to $Man.PatchedSize $Man.PatchedSha
    Say 'data.win is now the Knight Hub build (verified).'
    Write-BuildMarker $Man

    Test-FailHook 'before_music'
    Install-Music $Man
    Install-KfSongs
    Test-SteamFiles $Man
    return 0
}

# ---------------------------------------------------------------- KF Song Pack (build 50)
# knight_hub_kfsongs.zip holds kfsongs/<song_id>/{song.json, inst.ogg, vocals.ogg, lyrics.json} and CREDITS.txt: each file is
# put into the kfsongs folder next to data.win (a file already there and identical is left alone; one that differs is
# replaced - the pack's own files). Optional: without it the hub works and those songs show NOT FOUND.
function Install-KfSongs {
    $zp = Get-GamePath $script:NameKfSongs
    if (-not [System.IO.File]::Exists($zp)) { Say ('KF Song Pack: ' + $script:NameKfSongs + ' not here; skipped (optional).'); return }
    $sep = [System.IO.Path]::DirectorySeparatorChar
    $root = [System.IO.Path]::GetFullPath((Get-GamePath 'kfsongs'))
    $placed = 0; $same = 0; $bad = 0
    $zip = $null
    try {
        Add-Type -AssemblyName System.IO.Compression
        Add-Type -AssemblyName System.IO.Compression.FileSystem
        $zip = [System.IO.Compression.ZipFile]::OpenRead($zp)
        foreach ($e in $zip.Entries) {
            $n = $e.FullName.Replace('\', '/')
            if ($n.EndsWith('/')) { continue }
            if (-not $n.ToLowerInvariant().StartsWith('kfsongs/')) { continue }
            $rel = $n.Substring(8)
            if ($rel.Length -eq 0 -or $rel.Contains('..') -or $rel.StartsWith('/') -or $rel.Contains(':')) { Warn ('KF Song Pack: skipped an odd entry: ' + $n); $bad++; continue }
            $dest = [System.IO.Path]::GetFullPath([System.IO.Path]::Combine($root, $rel.Replace('/', [string]$sep)))
            if (-not $dest.StartsWith($root + [string]$sep, [System.StringComparison]::OrdinalIgnoreCase)) { Warn ('KF Song Pack: skipped an entry outside kfsongs: ' + $n); $bad++; continue }
            try {
                $es = $e.Open()
                $sh = ''
                try { $sh = Get-StreamSha256Hex $es } finally { $es.Dispose() }
                if ([System.IO.File]::Exists($dest)) {
                    $dh = Get-Sha256Hex $dest 11 ('existing kfsongs/' + $rel)
                    if ($dh -eq $sh) { $same++; continue }
                }
                $destDir = [System.IO.Path]::GetDirectoryName($dest)
                [void][System.IO.Directory]::CreateDirectory($destDir)
                $tmp = [System.IO.Path]::Combine($destDir, ($script:TmpPrefix + 'kfs_' + [Guid]::NewGuid().ToString('N').Substring(0, 8)))
                [void]$script:ExtraTemps.Add($tmp)
                $es = $e.Open()
                $os = New-Object System.IO.FileStream($tmp, [System.IO.FileMode]::CreateNew, [System.IO.FileAccess]::Write, [System.IO.FileShare]::None)
                try { $es.CopyTo($os, 1048576) } finally { $os.Dispose(); $es.Dispose() }
                $th = Get-Sha256Hex $tmp 11 'a temporary song pack file'
                if ($th -ne $sh) { throw 'copied song pack file failed verification' }
                if ([System.IO.File]::Exists($dest)) { [System.IO.File]::Delete($dest) }
                [System.IO.File]::Move($tmp, $dest)
                $placed++
            } catch {
                Warn ('KF Song Pack: could not install kfsongs/' + $rel + ': ' + (Get-RootEx $_.Exception).Message)
                $bad++
            }
        }
    } catch {
        Warn ('KF Song Pack: could not open ' + $script:NameKfSongs + ' (' + (Get-RootEx $_.Exception).Message + '); skipped.')
        return
    } finally {
        if ($null -ne $zip) { $zip.Dispose() }
    }
    Say ('KF Song Pack: ' + $placed + ' installed, ' + $same + ' already present, ' + $bad + ' skipped (kfsongs folder next to data.win).')
}

# ---------------------------------------------------------------- Knight Fights Online over Steam (build 45)
# kf_steam.dll (Knight Fights' own small DLL), steam_api64.dll (Valve's, from the Steamworks SDK) and steam_appid.txt (480,
# the "Spacewar" test app Steam rooms run as) stay in this folder next to data.win: the game loads them from here when the
# ONLINE page is opened. Missing or damaged ones only switch the STEAM rows off; practice and relay rooms still work.
function Test-SteamFiles($Man) {
    if ($Man.Steam.Count -eq 0) { Say 'No Steam files listed in the manifest (Steam rooms are not part of this package).'; return }
    $bad = 0
    foreach ($sf in $Man.Steam) {
        $p = Get-GamePath $sf.Name
        if (-not [System.IO.File]::Exists($p)) {
            Warn ($sf.Name + ' is missing from this folder: Steam rooms will not work until it is here (practice and relay rooms work). Copy it from the Knight Hub package.')
            $bad++
            continue
        }
        $h = ''
        try { $h = Get-Sha256Hex $p 11 $sf.Name } catch { $h = '' }
        if ($h -ne $sf.Sha) {
            Warn ($sf.Name + ' is not the file from this package (checksum differs). Copy it from the Knight Hub package again if Steam rooms do not work.')
            $bad++
        }
    }
    if ($bad -eq 0) { Say 'Knight Fights Online Steam files are in place (kf_steam.dll, steam_api64.dll, steam_appid.txt).' }
}

# ---------------------------------------------------------------- restore

function Invoke-RestoreMode {
    $dw = Get-GamePath $script:NameData
    $bk = Get-GamePath $script:NameBackup
    Say ('Knight Hub restore ' + $script:KhVersion + ' - mode: restore vanilla')
    Invoke-RecoverMissingDataWin
    $Man = Read-Manifest
    $script:Manifest = $Man
    $bstate = Get-BackupState $Man
    if ($bstate -eq 'none') {
        Stop-Kh 13 'There is no data.win.vanilla in this folder, so there is nothing to restore from. Use Steam "Verify integrity of game files" (Library > right-click DELTARUNE > Properties > Installed Files) to get the original data.win back. Nothing was changed.'
    }
    if ($bstate -eq 'invalid') {
        Stop-Kh 7 'data.win.vanilla exists but is NOT the unmodified vanilla Chapter 3 v0.0.105 file (wrong size or checksum), so it will not be restored. It was not touched. Use Steam "Verify integrity of game files" (Library > right-click DELTARUNE > Properties > Installed Files) to get the original data.win back.'
    }
    Say 'data.win.vanilla is a valid vanilla backup.'
    if ([System.IO.File]::Exists($dw)) {
        $info = Get-FileClass $Man $dw 'data.win'
        Say ('Current data.win is: ' + $info.Class)
        if ($info.Class -eq 'vanilla') {
            Say 'data.win is already the vanilla file. Nothing to do.'
            Invoke-CleanStalePrev $Man
            return 0
        }
        if ($info.Class -eq 'unknown') {
            Warn 'Current data.win is not recognised (some other mod?). Restoring will replace it.'
        }
    }
    Assert-FreeSpace ($Man.VanillaSize + [long]($Man.VanillaSize * 0.05) + 1048576) 'temporary copy of the backup'
    if (-not (Confirm-Action 'Restore the vanilla data.win now? The current data.win will be replaced.')) {
        Stop-Kh 14 'Cancelled. Nothing was changed.'
    }
    Assert-Writable
    Assert-DataWinExclusive
    Remove-OwnTemps
    $tc = New-TempPath 'restore'
    $cpErr = $null
    try {
        [System.IO.File]::Copy($bk, $tc, $false)
    } catch {
        $cpErr = $_.Exception
    }
    if ($null -ne $cpErr) {
        Stop-Kh (Get-IoCode $cpErr 11) ('Could not copy the backup: ' + (Get-RootEx $cpErr).Message)
    }
    $h = Get-Sha256Hex $tc 11 'the restore copy'
    if ($h -ne $Man.VanillaSha) { Stop-Kh 11 'The restore copy did not verify. Nothing was changed.' }
    Test-FailHook 'after_restore_copy'
    Invoke-Swap $tc $Man.VanillaSize $Man.VanillaSha
    Say 'Restored: data.win is the original vanilla file again. data.win.vanilla was kept.'
    # The package's files - the Knight Fights Steam files too - stay in this folder: the unmodded game never loads them, and
    # installing again needs them here (PLAY_KNIGHT_HUB.bat restores and installs in one go when it replaces an older build;
    # build 45 removed the Steam files at this point, which left Steam rooms NOT INSTALLED after an upgrade).
    Say 'The Knight Hub package files stay in this folder (kf_steam.dll, steam_api64.dll and steam_appid.txt too): the unmodded game does not use them, and installing again needs them.'
    return 0
}

# ---------------------------------------------------------------- main

function Invoke-Main {
    $rc = 1
    try {
        Initialize-Log
        Write-LogLine 'INFO' ('==== run start ==== installer ' + $script:KhVersion + ', PowerShell ' + $PSVersionTable.PSVersion.ToString() + ', ' + [Environment]::OSVersion.Platform.ToString())
        if ($script:GameDir -match '(?i)\.zip[\\/]' -or $script:GameDir -match '(?i)\\AppData\\Local\\Temp\\Temp\d+_') {
            Stop-Kh 2 'This installer is running from inside a zip file. Extract the whole package first (right-click the zip > Extract All), copy the files into your chapter3_windows folder, and run it from there.'
        }
        $res = $null
        if ($Restore) { $res = Invoke-RestoreMode } else { $res = Invoke-Install }
        if ($res -is [array]) { $res = $res[$res.Length - 1] }
        $rc = [int]$res
        Say ''
        Say ('RESULT: SUCCESS (exit code ' + $rc + ')')
        Write-Host 'Log: knight_hub_install.log (in this folder)'
    } catch {
        $ex = $_.Exception
        $code = Get-KhCode $ex
        $msg = $ex.Message
        if ($code -eq 0) {
            $code = 1
            $msg = 'Unexpected error: ' + (Get-RootEx $ex).GetType().Name + ': ' + (Get-RootEx $ex).Message + ' (at ' + (Get-Clean ([string]$_.InvocationInfo.PositionMessage)) + ')'
        }
        Write-Host ''
        Say-Error ('ERROR: ' + $msg)
        Say-Error ('RESULT: FAILED (exit code ' + $code + ')')
        Write-Host 'Details were written to knight_hub_install.log (in this folder). Exit codes are listed in README_INSTALL.txt.'
        $rc = $code
    } finally {
        Remove-OwnTemps
    }
    return $rc
}

$khResult = Invoke-Main
if ($khResult -is [array]) { $khResult = $khResult[$khResult.Length - 1] }
exit ([int]$khResult)
