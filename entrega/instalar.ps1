# Yakuza 5 Remastered - Traducción al español v1.0 (21-10-2026)
# Instala o quita la traducción. Antes de instalar guarda los archivos originales del juego en «respaldo_original»
# (junto a este instalador); «Quitar» los devuelve. No toca partidas, logros ni horas de Steam.
param([string]$Accion = "")
$ErrorActionPreference = "Stop"
$VERSION = "1.0.1"
$aqui = Split-Path -Parent $MyInvocation.MyCommand.Path
$arch = Join-Path $aqui "archivos\data"
$resp = Join-Path $aqui "respaldo_original"

function Buscar-Juego {
    $carpetas = @()
    $steam = (Get-ItemProperty "HKCU:\Software\Valve\Steam" -ErrorAction SilentlyContinue).SteamPath
    if ($steam) {
        $carpetas += $steam
        $vdf = Join-Path $steam "steamapps\libraryfolders.vdf"
        if (Test-Path $vdf) {
            foreach ($m in [regex]::Matches((Get-Content $vdf -Raw), '"path"\s+"([^"]+)"')) { $carpetas += $m.Groups[1].Value -replace '\\', '\' }
        }
    }
    foreach ($c in ($carpetas | Select-Object -Unique)) {
        $j = Join-Path $c "steamapps\common\Yakuza 5\main"
        if (Test-Path (Join-Path $j "data\wdr_par_en\wdr.par")) { return $j }
    }
    return $null
}

Write-Host "Yakuza 5 Remastered - Traducción al español v$VERSION" -ForegroundColor Yellow
if (Get-Process Yakuza5 -ErrorAction SilentlyContinue) { Write-Host "Cierra el juego antes de seguir." -ForegroundColor Red; Read-Host "Enter para salir"; exit 1 }
$juego = Buscar-Juego
if (-not $juego) {
    Write-Host "No encontré el juego automáticamente."
    $juego = Read-Host "Pega la carpeta «main» del juego (la que contiene Yakuza5.exe y «data»)"
    if (-not (Test-Path (Join-Path $juego "data\wdr_par_en\wdr.par"))) { Write-Host "Esa carpeta no es la del juego." -ForegroundColor Red; Read-Host "Enter para salir"; exit 1 }
}
$data = Join-Path $juego "data"
Write-Host "Juego: $juego"
if (-not $Accion) { $Accion = Read-Host "Escribe 1 para INSTALAR o 2 para QUITAR la traducción" }

$lista = Get-ChildItem $arch -Recurse -File | ForEach-Object { $_.FullName.Substring($arch.Length + 1) }
if ($Accion -eq "1") {
    if (-not (Test-Path $resp)) {
        Write-Host "Guardando los archivos originales en $resp ..."
        foreach ($r in $lista) {
            $d = Join-Path $resp $r; New-Item -ItemType Directory -Force (Split-Path $d) | Out-Null
            Copy-Item (Join-Path $data $r) $d
        }
    }
    Write-Host "Instalando $($lista.Count) archivos..."
    foreach ($r in $lista) {
        $d = Join-Path $data $r
        Remove-Item $d -Force   # por si es un enlace: se escribe un archivo nuevo, el original queda en el respaldo
        Copy-Item (Join-Path $arch $r) $d
    }
    Set-Content (Join-Path $data "traduccion_es_version.txt") "Traducción al español v$VERSION" -Encoding UTF8
    Write-Host "¡Listo! Abre el juego con el idioma en inglés." -ForegroundColor Green
} elseif ($Accion -eq "2") {
    if (-not (Test-Path $resp)) { Write-Host "No hay respaldo: usa «Verificar integridad» en Steam para volver al original." -ForegroundColor Red; Read-Host "Enter para salir"; exit 1 }
    foreach ($r in $lista) { $d = Join-Path $data $r; Remove-Item $d -Force; Copy-Item (Join-Path $resp $r) $d }
    Remove-Item (Join-Path $data "traduccion_es_version.txt") -ErrorAction SilentlyContinue
    Write-Host "Traducción quitada: el juego vuelve a estar en inglés." -ForegroundColor Green
}
Read-Host "Enter para salir"
