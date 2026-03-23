/* ═══════════════════════════════════════════════════════════════════════════
   MUDDO AGRO — THEME MANAGER
   Handles dark/light mode toggle with localStorage persistence
   ═══════════════════════════════════════════════════════════════════════════ */

(function () {
  'use strict';

  const STORAGE_KEY = 'muddo-theme';
  const DARK  = 'dark';
  const LIGHT = 'light';

  // ── Apply theme instantly (before paint) to avoid flash ──────────────────
  function getStoredTheme() {
    try { return localStorage.getItem(STORAGE_KEY) || LIGHT; } catch { return LIGHT; }
  }

  function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    document.body.setAttribute('data-theme', theme);

    // Update all toggle button labels
    document.querySelectorAll('[data-theme-label]').forEach(el => {
      el.textContent = theme === DARK ? 'Light Mode' : 'Dark Mode';
    });
    document.querySelectorAll('[data-theme-icon]').forEach(el => {
      el.className = theme === DARK ? 'fas fa-sun icon-sun' : 'fas fa-moon icon-moon';
    });

    // Persist
    try { localStorage.setItem(STORAGE_KEY, theme); } catch {}

    // Dispatch event for any listeners
    document.dispatchEvent(new CustomEvent('themechange', { detail: { theme } }));
  }

  function toggleTheme() {
    const current = getStoredTheme();
    const next    = current === DARK ? LIGHT : DARK;

    // Add a brief transition overlay for a smooth "wipe" feel
    const overlay = document.createElement('div');
    overlay.style.cssText = `
      position:fixed;inset:0;z-index:99999;pointer-events:none;
      background:${next === DARK ? '#0d1a0f' : '#fafaf7'};
      opacity:0;transition:opacity .18s ease;
    `;
    document.body.appendChild(overlay);
    requestAnimationFrame(() => {
      overlay.style.opacity = '.35';
      setTimeout(() => {
        applyTheme(next);
        overlay.style.opacity = '0';
        setTimeout(() => overlay.remove(), 220);
      }, 80);
    });
  }

  // ── Init on earliest possible moment ─────────────────────────────────────
  const storedTheme = getStoredTheme();
  if (storedTheme === DARK) {
    // Apply immediately to <html> to prevent light flash
    document.documentElement.setAttribute('data-theme', DARK);
  }

  // ── Wire up all toggle buttons when DOM is ready ──────────────────────────
  function initToggles() {
    document.querySelectorAll('.theme-toggle, .theme-toggle-nav, .theme-toggle-pill').forEach(btn => {
      // Remove old listeners by cloning
      const fresh = btn.cloneNode(true);
      btn.parentNode.replaceChild(fresh, btn);
      fresh.addEventListener('click', (e) => {
        e.preventDefault();
        toggleTheme();
      });
    });
    // Apply current theme labels
    applyTheme(getStoredTheme());
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initToggles);
  } else {
    initToggles();
  }

  // ── Expose global toggle for inline onclick usage ─────────────────────────
  window.toggleTheme   = toggleTheme;
  window.getCurrentTheme = getStoredTheme;

})();

/* ─── DARK MODE HERO ENHANCEMENT ─────────────────────────────────────────── */
document.addEventListener('themechange', function(e) {
  const isDark = e.detail.theme === 'dark';
  const hero   = document.querySelector('.hero');
  if (!hero) return;

  // Remove existing star particles
  hero.querySelectorAll('.star-particle').forEach(s => s.remove());

  if (isDark) {
    // Spawn subtle star field
    const container = hero.querySelector('.hero-particles') || hero;
    for (let i = 0; i < 28; i++) {
      const star = document.createElement('span');
      star.className = 'star-particle';
      const size = 1 + Math.random() * 2.5;
      star.style.cssText = `
        position:absolute;
        left:${Math.random()*100}%;
        top:${Math.random()*100}%;
        width:${size}px; height:${size}px;
        border-radius:50%;
        background:rgba(255,255,255,${.2 + Math.random() * .5});
        animation:pulse ${2 + Math.random()*3}s ease-in-out infinite;
        animation-delay:${Math.random()*4}s;
        pointer-events:none;
        z-index:1;
      `;
      container.appendChild(star);
    }
  }
});
