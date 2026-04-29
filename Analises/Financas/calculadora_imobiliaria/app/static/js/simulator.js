window.renderBalanceChart = function () {
  const el = document.getElementById('chart-balance');
  if (!el || !window.Plotly) return;
  let payload;
  try {
    payload = JSON.parse(el.dataset.payload);
  } catch (e) {
    return;
  }
  const insts = payload.installments || [];
  const months = insts.map(i => i.month);
  const balance = insts.map(i => parseFloat(i.balance));
  const cumInterest = [];
  const cumPrincipal = [];
  let ci = 0, cp = 0;
  for (const i of insts) {
    ci += parseFloat(i.interest);
    cp += parseFloat(i.principal);
    cumInterest.push(ci);
    cumPrincipal.push(cp);
  }

  const isDark = document.documentElement.classList.contains('dark');
  const ink500 = isDark ? '#94A3B8' : '#64748B';
  const ink100 = isDark ? '#1F2937' : '#F1F5F9';

  Plotly.newPlot(el, [
    {
      x: months, y: cumPrincipal, name: 'Amortização acumulada',
      type: 'scatter', mode: 'lines', stackgroup: 'one', fill: 'tonexty',
      line: { color: '#0E9F6E', width: 0 },
      fillcolor: 'rgba(14,159,110,0.55)',
    },
    {
      x: months, y: cumInterest, name: 'Juros acumulados',
      type: 'scatter', mode: 'lines', stackgroup: 'one',
      line: { color: '#F59E0B', width: 0 },
      fillcolor: 'rgba(245,158,11,0.45)',
    },
    {
      x: months, y: balance, name: 'Saldo devedor',
      type: 'scatter', mode: 'lines',
      line: { color: '#2563EB', width: 2, dash: 'dot' },
      yaxis: 'y2',
    },
  ], {
    margin: { l: 60, r: 50, t: 10, b: 40 },
    paper_bgcolor: 'rgba(0,0,0,0)',
    plot_bgcolor: 'rgba(0,0,0,0)',
    font: { family: 'Inter, sans-serif', color: ink500, size: 11 },
    xaxis: { title: 'Mês', gridcolor: ink100, zerolinecolor: ink100 },
    yaxis: {
      title: 'Acumulado pago (R$)', gridcolor: ink100, zerolinecolor: ink100,
      tickformat: ',.0f',
    },
    yaxis2: {
      title: 'Saldo devedor (R$)', overlaying: 'y', side: 'right',
      gridcolor: 'rgba(0,0,0,0)',
      tickformat: ',.0f',
    },
    legend: { orientation: 'h', y: -0.2 },
    hovermode: 'x unified',
  }, { responsive: true, displayModeBar: false });
};

document.addEventListener('htmx:afterSwap', () => {
  setTimeout(() => window.renderBalanceChart(), 50);
});
