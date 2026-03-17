# Copia figuras do pipeline para writing_latex/Tese/pngs/exp1-exp7
# Execute a partir da raiz do repo Mestrado ou ajuste $OUT e $DEST.

$ErrorActionPreference = "Stop"
$Mestrado = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$OUT = Join-Path $Mestrado "pipeline\model_training\outputs"
$DEST = Join-Path $Mestrado "writing_latex\Tese\pngs"

$map = @(
    @{ exp = "exp1"; src = "resultado1_split0.8-0.2_all-features" },
    @{ exp = "exp2"; src = "resultado2_split0.8-0.2_less_features" },
    @{ exp = "exp3"; src = "resultado3_split0.8-0.2_less-features_noMin" },
    @{ exp = "exp4"; src = "resultado4_split0.8-0.2_less-features_noKmeans" },
    @{ exp = "exp5"; src = "resultado5_split0.8-0.2_less_features_noMin-noKmeans" },
    @{ exp = "exp6"; src = "resultado6.1_split0.65-0.35_less_feaures_noMin-noKmeans" },
    @{ exp = "exp7"; src = "resultado6.2_applyTestOnlyRealCurves" }
)

foreach ($m in $map) {
    $srcDir = Join-Path $OUT $m.src
    $destDir = Join-Path $DEST $m.exp
    if (-not (Test-Path $srcDir)) {
        Write-Warning "Origem nao encontrada: $srcDir"
        continue
    }
    if (-not (Test-Path $destDir)) { New-Item -ItemType Directory -Path $destDir -Force | Out-Null }
    $pngs = Get-ChildItem $srcDir -Filter "*.png"
    foreach ($f in $pngs) {
        Copy-Item $f.FullName -Destination $destDir -Force
        Write-Host "Copiado: $($m.exp)/$($f.Name)"
    }
}

Write-Host "Concluido. Figuras em $DEST\exp1 .. exp7"
