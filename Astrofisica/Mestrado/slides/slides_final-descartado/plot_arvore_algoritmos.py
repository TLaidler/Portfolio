# -*- coding: utf-8 -*-
"""
Diagrama da genealogia dos algoritmos baseados em árvores usados na dissertação.
Bagging e Boosting como ramos IRMÃOS (duas respostas ao dilema viés-variância),
não como estágios de uma linha evolutiva. Paleta ON: branco + azul claro + navy.

Saída: arvore_algoritmos.png (nesta pasta e em writing_latex/Tese/pngs/).
"""
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

HERE = Path(__file__).resolve().parent
TESE_PNGS = HERE.parent.parent / 'writing_latex' / 'Tese' / 'pngs'

NAVY = '#1D2D54'
BLUE = '#4896DE'
LIGHT = '#EAF2FB'
WHITE = '#FFFFFF'

fig, ax = plt.subplots(figsize=(12.5, 7.6))
ax.set_xlim(0, 100)
ax.set_ylim(0, 100)
ax.axis('off')
fig.patch.set_facecolor(WHITE)


def node(cx, cy, w, h, lines, used=False, dashed=False):
    """Caixa arredondada centrada em (cx, cy). used=True -> preenchimento azul."""
    face = BLUE if used else LIGHT
    txt = WHITE if used else NAVY
    box = FancyBboxPatch(
        (cx - w / 2, cy - h / 2), w, h,
        boxstyle='round,pad=0.6,rounding_size=1.6',
        linewidth=2.0 if used else 1.5,
        edgecolor=NAVY, facecolor=face,
        linestyle='--' if dashed else '-', zorder=3)
    ax.add_patch(box)
    n = len(lines)
    for i, (text, size, weight, style) in enumerate(lines):
        dy = (n - 1) / 2 * (h / (n + 0.6)) - i * (h / (n + 0.6))
        ax.text(cx, cy + dy, text, ha='center', va='center', color=txt,
                fontsize=size, fontweight=weight, fontstyle=style, zorder=4)


def line(pts, dashed=False):
    xs, ys = zip(*pts)
    ax.plot(xs, ys, color=NAVY, lw=1.8, zorder=2, solid_capstyle='round',
            linestyle='--' if dashed else '-')


L = lambda t, s=13, w='normal', st='normal': (t, s, w, st)

# ---- nós -------------------------------------------------------------------
node(50, 90, 34, 8, [L('Árvore de Decisão', 15, 'bold'), L('(CART, 1984)', 12)])

node(25, 68, 33, 15, [L('BAGGING', 15, 'bold'),
                      L('reduz variância', 12, 'normal', 'italic'),
                      L('árvores paralelas', 12)])
node(70, 68, 33, 15, [L('BOOSTING', 15, 'bold'),
                      L('reduz viés', 12, 'normal', 'italic'),
                      L('árvores sequenciais', 12)])

node(25, 46, 31, 8, [L('Random Forest', 15, 'bold'), L('(2001)', 12)], used=True)
node(70, 46, 31, 8, [L('Gradient Boosting', 15, 'bold'), L('(2001)', 12)])

node(56, 22, 24, 8, [L('XGBoost', 15, 'bold'), L('(2016)', 12)], used=True)
node(84, 22, 24, 8, [L('CatBoost', 15, 'bold'), L('(2018)', 12)], used=True)

node(19, 22, 30, 12, [L('Regressão Logística', 14, 'bold'),
                      L('modelo linear', 11, 'normal', 'italic'),
                      L('fora da família (baseline)', 11)],
     used=True, dashed=True)

# ---- conectores ------------------------------------------------------------
line([(50, 85.4), (50, 79)])                 # raiz -> barra
line([(25, 79), (70, 79)])                   # barra horizontal
line([(25, 79), (25, 76.4)])
line([(70, 79), (70, 76.4)])
line([(25, 59.4), (25, 50.6)])               # bagging -> RF
line([(70, 59.4), (70, 50.6)])               # boosting -> GB
line([(70, 41.4), (70, 33)])                 # GB -> barra
line([(56, 33), (84, 33)])
line([(56, 33), (56, 26.6)])
line([(84, 33), (84, 26.6)])

# separador da Regressão Logística (fora da genealogia de árvores)
line([(4.5, 34.5), (36, 34.5)], dashed=True)

# ---- legenda ---------------------------------------------------------------
ax.add_patch(FancyBboxPatch((3.0, 3.2), 3.2, 2.6,
                            boxstyle='round,pad=0.2,rounding_size=0.6',
                            linewidth=2.0, edgecolor=NAVY, facecolor=BLUE))
ax.text(7.4, 4.5, 'classificadores avaliados nesta dissertação',
        ha='left', va='center', color=NAVY, fontsize=11.5)
ax.add_patch(FancyBboxPatch((3.0, -0.6), 3.2, 2.6,
                            boxstyle='round,pad=0.2,rounding_size=0.6',
                            linewidth=1.5, edgecolor=NAVY, facecolor=LIGHT))
ax.text(7.4, 0.7, 'conceito ou algoritmo de referência',
        ha='left', va='center', color=NAVY, fontsize=11.5)

fig.tight_layout()
for out in (HERE / 'arvore_algoritmos.png', TESE_PNGS / 'arvore_algoritmos.png'):
    fig.savefig(out, dpi=200, facecolor=WHITE, bbox_inches='tight')
    print('salvo:', out)
plt.close(fig)
