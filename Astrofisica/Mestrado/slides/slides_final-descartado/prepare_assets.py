# -*- coding: utf-8 -*-
"""
Prepara os assets do deck final da defesa.
- Copia figuras curadas de slides/figs e writing_latex/Tese/pngs
- Extrai midias selecionadas do PPTX do seminario (part1)
Idempotente: pode rodar quantas vezes quiser.
"""
import shutil
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent          # slides/slides_final
SLIDES = HERE.parent                             # slides/
ROOT = SLIDES.parent                             # Mestrado/
TESE_PNGS = ROOT / 'writing_latex' / 'Tese' / 'pngs'
PART1_PPTX = (SLIDES / 'slides_mestrado_part1' /
              'Projeto_Mestrado_ Pipeline para treinamento de modelo '
              'Machine Learning detecção de ocultações.pptx')

ASSETS = HERE / 'assets'

FIGS = ['ocultacao_ilustracao.png', 'pipeline.png', 'quaoar_curva.png',
        'quaoar_recortes.png', 'exp1_roc.png', 'exp1_confusion.png',
        'exp3real_roc.png', 'exp3real_confusion.png', 'metrics_vs_threshold.png',
        'feat_importance_rf.png', 'on_logo.png']

TESE = ['curva.png', 'OccUmbriel_mapa.png', 'OccUmbriel_mapa2.png',
        'OccUmbriel_outputExemplo.png', 'OccUmbriel_outputExemplo2.png',
        'Cordas atualizadas.png', 'Bardecker12.png', 'fluxo1.png', 'fluxo2.png',
        'diagrama_1.png', 'sigmoide.png', 'RF_img.png', 'manual_2.png', 'kfold.png',
        'Learning-curves-of-models-with-training-data-A-XGBoost-B-Random-Forest-C.png',
        'quaoar_test.png', 'quaoar_recorte_tau_ajustado.png',
        'quaoar_recortes_janelas_expandidas.png', 'ModelosSORA.png',
        'Quaoar_XgBoost_full_pict.png', 'Quaoar_XgBoost_1st_cut.png',
        'Quaoar_XgBoost_2st3st_cut.png', 'Quaoar_XgBoost_4st_cut.png',
        'Quaoar_XgBoost_5st_cut.png',
        'resultado3/histograma_kmeans_por_classe.png',
        'resultado3/RF_curva_FN_1.png', 'resultado3/RF_curva_FN_2.png']

PART1_MEDIA = ['image12.png', 'image18.png', 'image19.png', 'image21.png',
               'image22.png', 'image23.png', 'image24.png', 'image25.png',
               'image27.jpg', 'image28.png', 'image34.png', 'image38.png',
               'image39.png', 'image47.png', 'image51.png']


def main():
    for sub in ('figs', 'tese', 'part1'):
        (ASSETS / sub).mkdir(parents=True, exist_ok=True)

    missing = []
    for name in FIGS:
        src = SLIDES / 'figs' / name
        if src.exists():
            shutil.copy2(src, ASSETS / 'figs' / name)
        else:
            missing.append(str(src))

    for name in TESE:
        src = TESE_PNGS / name
        if src.exists():
            shutil.copy2(src, ASSETS / 'tese' / Path(name).name)
        else:
            missing.append(str(src))

    with zipfile.ZipFile(PART1_PPTX) as z:
        names = set(z.namelist())
        for m in PART1_MEDIA:
            member = f'ppt/media/{m}'
            if member in names:
                (ASSETS / 'part1' / m).write_bytes(z.read(member))
            else:
                missing.append(member)

    n = sum(1 for _ in ASSETS.rglob('*') if _.is_file())
    print(f'assets prontos: {n} arquivos em {ASSETS}')
    if missing:
        print('FALTANDO:')
        for m in missing:
            print('  -', m)
    return 1 if missing else 0


if __name__ == '__main__':
    raise SystemExit(main())
