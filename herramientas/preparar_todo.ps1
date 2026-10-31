# Descarga e instala de una vez todo lo que hace falta para COMPILAR la traducción (no para jugarla: para jugar basta el
# zip de Releases). Lo arranca «PREPARAR TODO.bat» desde la carpeta del repositorio.
# Baja solo programas y fuentes de sus páginas oficiales, comprueba la SHA-256 de cada archivo y no toca el juego.
param([switch]$SoloTexto)
$ErrorActionPreference = "Stop"
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$repo = Split-Path -Parent $PSScriptRoot
$h = Join-Path $repo "herramientas"
$tmp = Join-Path $env:TEMP "preparar_y5"; New-Item -ItemType Directory -Force $tmp | Out-Null

function Paso($t) { Write-Host ""; Write-Host "== $t" -ForegroundColor Cyan }
function Bajar($url, $destino, $sha) {
    if ((Test-Path $destino) -and ((Get-FileHash $destino -Algorithm SHA256).Hash -eq $sha)) { Write-Host "   ya estaba: $(Split-Path -Leaf $destino)"; return }
    New-Item -ItemType Directory -Force (Split-Path $destino) | Out-Null
    Write-Host "   bajando $(Split-Path -Leaf $destino) ..."
    Invoke-WebRequest -Uri $url -OutFile $destino -UseBasicParsing
    $got = (Get-FileHash $destino -Algorithm SHA256).Hash
    if ($got -ne $sha) { Remove-Item $destino -Force; throw "La SHA-256 de $(Split-Path -Leaf $destino) no coincide (esperada $sha, llegó $got). No se usa." }
}

Write-Host "PREPARAR TODO - Yakuza 5 Remastered: traducción al español (compilar desde el código)" -ForegroundColor Green
Write-Host "Repositorio: $repo"
if ($repo -ne "C:\Mods\yakuza5") {
    Write-Host "AVISO: algunos scripts esperan el repositorio en C:\Mods\yakuza5 (ver COMPILAR.md). Puedes seguir y moverlo después." -ForegroundColor Yellow
}

Paso "1/5 Python 3.12"
$py = $null
foreach ($c in @(@("py", "-3.12"), @("python"))) {
    try { $v = & $c[0] $c[1..9] -c "import sys; print('%d.%d' % sys.version_info[:2])" 2>$null; if ($v -eq "3.12") { $py = $c; break } } catch {}
}
if (-not $py) {
    Write-Host "   No encuentro Python 3.12." -ForegroundColor Yellow
    if ((Read-Host "   ¿Lo instalo con winget (Python.Python.3.12)? S/N") -match "^[sS]") {
        winget install -e --id Python.Python.3.12 --accept-source-agreements --accept-package-agreements
        $py = @("py", "-3.12")
    } else { throw "Instala Python 3.12 (https://www.python.org/downloads/) y vuelve a abrir PREPARAR TODO.bat" }
}
Write-Host "   Python: $($py -join ' ')"

Paso "2/5 Paquetes de Python"
$paq = @("numpy==2.5.4")
if (-not $SoloTexto) {
    $r = Read-Host "   ¿Instalar también lo de las IMÁGENES (OCR y borrado con LaMa; unos 3 GB, solo para rehacer texturas)? S/N"
    if ($r -match "^[sS]") { $paq += @("pillow==12.3.0", "opencv-python-headless==5.0.0.93", "rapidocr-onnxruntime==1.4.4", "simple-lama-inpainting==0.1.2") }
}
& $py[0] $py[1..9] -m pip install --upgrade @paq
if ($LASTEXITCODE -ne 0) { throw "pip no pudo instalar los paquetes" }

Paso "3/5 ParTool 1.3.4 (Kaplas80, ParManager)"
$zip = Join-Path $tmp "partool.zip"
Bajar "https://github.com/Kaplas80/ParManager/releases/download/v1.3.4/v1.3.4-windows-x64.zip" $zip "9D63A8B960689D9CE1B6A634DA574871F2956D26DCD21F66EB46653EC3A8EE08"
$pt = Join-Path $h "partool\ParTool.exe"
if (-not ((Test-Path $pt) -and ((Get-FileHash $pt -Algorithm SHA256).Hash -eq "B798027A243229C04741E491ABB1F92AE4CC7A379C0CBA31B81446F9BE4E5B3F"))) {
    Expand-Archive $zip (Join-Path $h "partool") -Force
    if ((Get-FileHash $pt -Algorithm SHA256).Hash -ne "B798027A243229C04741E491ABB1F92AE4CC7A379C0CBA31B81446F9BE4E5B3F") { throw "ParTool.exe no es el esperado" }
}
Write-Host "   listo: herramientas\partool\ParTool.exe"

Paso "4/5 reARMP (Ret-HZ) y texconv (Microsoft DirectXTex may2026)"
$ra = Join-Path $repo "entrega\Herramientas para traduccion\programas\reARMP"
New-Item -ItemType Directory -Force (Join-Path $h "reARMP") | Out-Null
Copy-Item (Join-Path $ra "*") (Join-Path $h "reARMP") -Force
Write-Host "   listo: herramientas\reARMP\reARMP.py (copia incluida en el repositorio)"
Bajar "https://github.com/microsoft/DirectXTex/releases/download/may2026/texconv.exe" (Join-Path $h "texconv\texconv.exe") "DCFDEC10244E02CF5037FBA089C55FB7E1326B1C8181742D77D15FA5CB5EEF06"
Write-Host "   listo: herramientas\texconv\texconv.exe"

Paso "5/5 Fuentes de Google Fonts (para redibujar texturas)"
$gf = "https://raw.githubusercontent.com/google/fonts/6c1dbe27dcf7d817d4b62cec033ba77fa8e2a5ec"
$fuentes = @(
    @("Bangers-Regular.ttf", "ofl/bangers/Bangers-Regular.ttf"), @("CaveatBrush-Regular.ttf", "ofl/caveatbrush/CaveatBrush-Regular.ttf"),
    @("FjallaOne-Regular.ttf", "ofl/fjallaone/FjallaOne-Regular.ttf"), @("GochiHand-Regular.ttf", "ofl/gochihand/GochiHand-Regular.ttf"),
    @("Kalam-Bold.ttf", "ofl/kalam/Kalam-Bold.ttf"), @("Knewave-Regular.ttf", "ofl/knewave/Knewave-Regular.ttf"),
    @("LilitaOne-Regular.ttf", "ofl/lilitaone/LilitaOne-Regular.ttf"), @("MarckScript-Regular.ttf", "ofl/marckscript/MarckScript-Regular.ttf"),
    @("NanumBrushScript-Regular.ttf", "ofl/nanumbrushscript/NanumBrushScript-Regular.ttf"), @("Oswald.ttf", "ofl/oswald/Oswald%5Bwght%5D.ttf"),
    @("PermanentMarker-Regular.ttf", "apache/permanentmarker/PermanentMarker-Regular.ttf"), @("RockSalt-Regular.ttf", "apache/rocksalt/RockSalt-Regular.ttf"),
    @("RubikDirt-Regular.ttf", "ofl/rubikdirt/RubikDirt-Regular.ttf"), @("SedgwickAveDisplay-Regular.ttf", "ofl/sedgwickavedisplay/SedgwickAveDisplay-Regular.ttf"),
    @("Shojumaru-Regular.ttf", "ofl/shojumaru/Shojumaru-Regular.ttf"), @("YujiSyuku-Regular.ttf", "ofl/yujisyuku/YujiSyuku-Regular.ttf"))
$sha = @{}
Get-Content (Join-Path $PSScriptRoot "fuentes_img.sha256") | ForEach-Object { $a = $_ -split "\s+\*?", 2; $sha[$a[1]] = $a[0].ToUpper() }
foreach ($f in $fuentes) { Bajar "$gf/$($f[1])" (Join-Path $h "fuentes_img\$($f[0])") $sha[$f[0]] }

Write-Host ""
Write-Host "TODO LISTO. Ahora sigue COMPILAR.md desde el paso «Copiar y desempaquetar los archivos del juego»." -ForegroundColor Green
