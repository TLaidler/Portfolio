window.app = (function () {
  function toggleTheme() {
    const dark = document.documentElement.classList.toggle('dark');
    localStorage.setItem('theme', dark ? 'dark' : 'light');
  }

  function toast(message, type = 'info', duration = 5000) {
    const cont = document.getElementById('toasts');
    if (!cont) return;
    const colors = {
      info: 'border-brand-blue-600',
      success: 'border-brand-green-600',
      warning: 'border-amber-500',
      error: 'border-red-500',
    };
    const el = document.createElement('div');
    el.className = `bg-white dark:bg-ink-700 text-ink-700 dark:text-ink-50 shadow-soft-md rounded-xl p-4 border-l-4 ${colors[type] || colors.info} animate-fade-up`;
    el.innerHTML = `<div class="text-sm">${message}</div>`;
    cont.appendChild(el);
    setTimeout(() => el.remove(), duration);
  }

  function animateNumber(el, target, opts = {}) {
    const dur = opts.duration ?? 700;
    const start = performance.now();
    const fmt = opts.format || ((n) => n.toFixed(2));
    function step(now) {
      const t = Math.min(1, (now - start) / dur);
      const eased = 1 - Math.pow(1 - t, 3);
      el.textContent = fmt(target * eased);
      if (t < 1) requestAnimationFrame(step);
    }
    requestAnimationFrame(step);
  }

  // Máscara monetária BR para inputs com data-mask="brl"
  document.addEventListener('input', (e) => {
    const t = e.target;
    if (!t.matches || !t.matches('[data-mask="brl"]')) return;
    const digits = t.value.replace(/\D/g, '');
    if (!digits) { t.value = ''; return; }
    const n = parseInt(digits, 10) / 100;
    t.value = n.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  });

  // Re-renderiza ícones Lucide após swap HTMX
  document.addEventListener('htmx:afterSwap', () => {
    if (window.lucide) lucide.createIcons();
  });

  return { toggleTheme, toast, animateNumber };
})();
