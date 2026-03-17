"""
Copia os PNGs gerados pelo pipeline para o diretório da tese LaTeX.

Uso:
    python copy_plots_to_thesis.py

Mapeia cada subdiretório de outputs/ para writing_latex/Tese/pngs/<subdir>/,
criando os diretórios necessários automaticamente.
"""

import shutil
from pathlib import Path

# Diretórios base
SCRIPT_DIR = Path(__file__).resolve().parent
OUTPUTS_DIR = SCRIPT_DIR / "outputs"
THESIS_PNGS_DIR = SCRIPT_DIR.parent.parent / "writing_latex" / "Tese" / "pngs"

# Subdiretórios de resultados a copiar
RESULT_DIRS = [
    "resultado_split0.35-0.65_less_feature",
    "resultado_split0.4-0.6_less_feature",
    "resultado_split0.8-0.2_less_feature",
    "resultado_split0.8-0.2_less_feature_noKmeans",
]


def copy_pngs():
    copied = 0
    for subdir_name in RESULT_DIRS:
        src_dir = OUTPUTS_DIR / subdir_name
        if not src_dir.is_dir():
            print(f"[SKIP] {src_dir} nao encontrado")
            continue

        dst_dir = THESIS_PNGS_DIR / subdir_name
        dst_dir.mkdir(parents=True, exist_ok=True)

        for png_file in src_dir.glob("*.png"):
            dst_file = dst_dir / png_file.name
            shutil.copy2(png_file, dst_file)
            copied += 1

    # Copiar PNGs soltos em outputs/ (e.g., cross_validation, learning curve)
    for png_file in OUTPUTS_DIR.glob("*.png"):
        dst_file = THESIS_PNGS_DIR / png_file.name
        THESIS_PNGS_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(png_file, dst_file)
        copied += 1

    print(f"[OK] {copied} arquivos PNG copiados para {THESIS_PNGS_DIR}")


if __name__ == "__main__":
    copy_pngs()
