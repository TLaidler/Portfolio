window._oppShowReal = false;

window.toggleOppReal = function (real) {
  window._oppShowReal = !!real;
  window.renderOppChart();
};

window.renderOppChart = function () {
  const el = document.getElementById('chart-opp');
  if (!el || !window.Plotly) return;
  let payload;
  try {
    payload = JSON.parse(el.dataset.payload);
  } catch (e) { return; }

  const showReal = window._oppShowReal;
  const months = payload.points.map(p => p.month);
  const buy = payload.points.map(p => parseFloat(showReal ? p.wealth_buy_real : p.wealth_buy_nominal));
  const rent = payload.points.map(p => parseFloat(showReal ? p.wealth_rent_real : p.wealth_rent_nominal));
  const be = payload.summary.breakeven_month;

  const isDark = document.documentElement.classList.contains('dark');
  const ink500 = isDark ? '#94A3B8' : '#64748B';
  const ink100 = isDark ? '#1F2937' : '#F1F5F9';

  const traces = [
    {
      x: months, y: buy, name: 'Comprar', mode: 'lines',
      line: { color: '#0E9F6E', width: 2.5 },
    },
    {
      x: months, y: rent, name: 'Alugar+Investir', mode: 'lines',
      line: { color: '#2563EB', width: 2.5 },
    },
  ];
  if (be) {
    traces.push({
      x: [be], y: [buy[be - 1]],
      mode: 'markers+text',
      marker: { size: 12, color: '#F59E0B', line: { color: '#fff', width: 2 } },
      text: [`break-even (mês ${be})`], textposition: 'top center',
      textfont: { color: ink500, size: 11 },
      showlegend: false,
    });
  }

  Plotly.newPlot(el, traces, {
    margin: { l: 70, r: 30, t: 10, b: 40 },
    paper_bgcolor: 'rgba(0,0,0,0)',
    plot_bgcolor: 'rgba(0,0,0,0)',
    font: { family: 'Inter, sans-serif', color: ink500, size: 11 },
    xaxis: { title: 'Mês', gridcolor: ink100, zerolinecolor: ink100 },
    yaxis: {
      title: showReal ? 'Patrimônio real (R$)' : 'Patrimônio nominal (R$)',
      gridcolor: ink100, tickformat: ',.0f',
    },
    legend: { orientation: 'h', y: -0.2 },
    hovermode: 'x unified',
  }, { responsive: true, displayModeBar: false });
};

document.addEventListener('htmx:afterSwap', () => {
  setTimeout(() => window.renderOppChart && window.renderOppChart(), 50);
});
