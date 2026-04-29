window.fmt = (function () {
  const brl = new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' });
  const pct = new Intl.NumberFormat('pt-BR', { style: 'percent', minimumFractionDigits: 2, maximumFractionDigits: 2 });
  const dec = new Intl.NumberFormat('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });

  function formatBRL(v) {
    const n = typeof v === 'number' ? v : parseFloat(String(v).replace(/[^\d.-]/g, ''));
    return isFinite(n) ? brl.format(n) : '—';
  }
  function formatPercent(v) {
    const n = typeof v === 'number' ? v : parseFloat(v);
    return isFinite(n) ? pct.format(n) : '—';
  }
  function formatMonths(m) {
    if (m == null) return '—';
    const years = Math.floor(m / 12);
    const months = m % 12;
    const parts = [];
    if (years) parts.push(years + (years === 1 ? ' ano' : ' anos'));
    if (months) parts.push(months + (months === 1 ? ' mês' : ' meses'));
    return parts.join(' e ') || '0 meses';
  }
  function parseBRLInput(s) {
    if (!s) return 0;
    return parseFloat(String(s).replace(/[^\d,.-]/g, '').replace(/\./g, '').replace(',', '.')) || 0;
  }
  return { formatBRL, formatPercent, formatMonths, parseBRLInput, dec };
})();
