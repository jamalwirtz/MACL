/* ═══════════════════════════════════════════════════════════════
   MUDDO AGRO — ENHANCEMENTS JS
   Toast system, lazy image loader, mobile UX, stock chips
   ═══════════════════════════════════════════════════════════════ */

// ─── GLOBAL TOAST SYSTEM ─────────────────────────────────────────────────
window.toast = (function() {
  let container = null;
  function getContainer() {
    if (!container) {
      container = document.createElement('div');
      container.className = 'toast-container';
      document.body.appendChild(container);
    }
    return container;
  }
  function show(message, type = 'success', duration = 3500) {
    const c = getContainer();
    const t = document.createElement('div');
    t.className = `toast ${type !== 'success' ? type : ''}`.trim();
    const icons = { success: 'fa-check-circle', error: 'fa-exclamation-circle', warning: 'fa-exclamation-triangle', info: 'fa-info-circle' };
    t.innerHTML = `<i class="fas ${icons[type] || 'fa-check-circle'}" style="font-size:.95rem;flex-shrink:0;"></i><span>${message}</span>`;
    c.appendChild(t);
    setTimeout(() => {
      t.style.transition = 'opacity .3s ease, transform .3s ease';
      t.style.opacity = '0'; t.style.transform = 'translateX(20px)';
      setTimeout(() => t.remove(), 320);
    }, duration);
    return t;
  }
  return { show, success: m => show(m,'success'), error: m => show(m,'error'), warning: m => show(m,'warning'), info: m => show(m,'info') };
})();

// ─── LAZY IMAGE OBSERVER ──────────────────────────────────────────────────
(function() {
  if (!('IntersectionObserver' in window)) return;
  const obs = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const img = entry.target;
        img.addEventListener('load',  () => img.classList.add('loaded'), { once: true });
        img.addEventListener('error', () => img.classList.add('loaded'), { once: true });
        obs.unobserve(img);
      }
    });
  }, { rootMargin: '100px' });
  document.querySelectorAll('img[loading="lazy"]').forEach(img => obs.observe(img));
})();

// ─── MOBILE NAV TOUCH SWIPE TO CLOSE ──────────────────────────────────────
(function() {
  let startX = null;
  const navLinks = document.getElementById('navLinks');
  if (!navLinks) return;
  document.addEventListener('touchstart', e => { startX = e.touches[0].clientX; }, { passive: true });
  document.addEventListener('touchend', e => {
    if (startX === null) return;
    const dx = startX - e.changedTouches[0].clientX;
    if (dx > 60 && navLinks.classList.contains('open')) {
      navLinks.classList.remove('open');
      document.getElementById('hamburger')?.classList.remove('open');
    }
    startX = null;
  }, { passive: true });
})();

// ─── SCROLL PROGRESS INDICATOR ───────────────────────────────────────────
(function() {
  const bar = document.createElement('div');
  bar.style.cssText = 'position:fixed;top:0;left:0;height:3px;z-index:99999;background:linear-gradient(90deg,var(--green-mid),var(--gold));transition:width .1s ease;pointer-events:none;';
  document.body.appendChild(bar);
  window.addEventListener('scroll', () => {
    const pct = (window.scrollY / (document.body.scrollHeight - window.innerHeight)) * 100;
    bar.style.width = Math.min(pct, 100) + '%';
  }, { passive: true });
})();

// ─── PRODUCT CARD STOCK CHIPS ─────────────────────────────────────────────
(function() {
  document.querySelectorAll('.product-card[data-id]').forEach(card => {
    const img = card.querySelector('.product-card-img');
    if (!img) return;
    const stock = parseInt(card.dataset.stock ?? '-1', 10);
    if (stock < 0) return;  // no stock data
    const chip = document.createElement('span');
    chip.className = 'stock-chip ' + (stock === 0 ? 'stock-out' : stock <= 10 ? 'stock-low' : 'stock-in');
    chip.innerHTML = stock === 0 ? '<i class="fas fa-times-circle" style="margin-right:4px;"></i>Out of stock'
                   : stock <= 10 ? `<i class="fas fa-exclamation-circle" style="margin-right:4px;"></i>Low stock (${stock})`
                   : '<i class="fas fa-check-circle" style="margin-right:4px;"></i>In stock';
    img.appendChild(chip);
  });
})();

// ─── SMOOTH SECTION TRANSITIONS ──────────────────────────────────────────
document.querySelectorAll('.section, .section-alt').forEach(section => {
  section.style.transition = 'background-color .35s ease';
});

// ─── KEYBOARD SHORTCUT: / to focus search ─────────────────────────────────
document.addEventListener('keydown', e => {
  if (e.key === '/' && !['INPUT','TEXTAREA','SELECT'].includes(document.activeElement?.tagName)) {
    e.preventDefault();
    const form  = document.getElementById('globalSearchForm');
    const input = document.getElementById('globalSearchInput');
    if (form && input) {
      form.classList.add('open');
      input.focus();
    } else {
      window.location.href = '/search';
    }
  }
});

// ─── COPY-TO-CLIPBOARD UTILITY ─────────────────────────────────────────────
window.copyToClipboard = function(text, successMsg = 'Copied!') {
  navigator.clipboard.writeText(text)
    .then(() => window.toast?.success(successMsg))
    .catch(() => { const t = prompt('Copy this:', text); });
};

// ─── CONFIRM DIALOGS — NICER ──────────────────────────────────────────────
document.querySelectorAll('[data-confirm]').forEach(el => {
  el.addEventListener('click', function(e) {
    if (!confirm(this.dataset.confirm)) {
      e.preventDefault(); e.stopPropagation();
    }
  });
});

// ─── AUTO-HIDE TOPBAR ON SCROLL DOWN, SHOW ON SCROLL UP ───────────────────
(function() {
  const topbar = document.querySelector('.topbar');
  if (!topbar || window.innerWidth < 768) return;
  let lastY = 0;
  window.addEventListener('scroll', () => {
    const y = window.scrollY;
    if (y > 100) {
      topbar.style.transition = 'transform .25s ease';
      topbar.style.transform  = y > lastY ? 'translateY(-100%)' : 'translateY(0)';
    } else {
      topbar.style.transform = 'translateY(0)';
    }
    lastY = y;
  }, { passive: true });
})();

// ─── FORM VALIDATION ENHANCEMENT ─────────────────────────────────────────
document.querySelectorAll('form:not([novalidate])').forEach(form => {
  form.addEventListener('submit', e => {
    const invalids = form.querySelectorAll(':invalid');
    if (invalids.length) {
      invalids[0].focus();
      invalids.forEach(el => {
        el.style.borderColor = '#e53935';
        el.addEventListener('input', () => { el.style.borderColor = ''; }, { once: true });
      });
    }
  });
});

// ─── PRINT BUTTON PULSE ───────────────────────────────────────────────────
document.querySelectorAll('.print-btn').forEach(btn => {
  btn.addEventListener('click', () => window.print());
});

// ─── ANNOUNCE PAGE LOAD TO SCREEN READERS ────────────────────────────────
(function() {
  const live = document.createElement('div');
  live.setAttribute('aria-live', 'polite');
  live.setAttribute('aria-atomic', 'true');
  live.style.cssText = 'position:absolute;left:-9999px;width:1px;height:1px;overflow:hidden;';
  document.body.appendChild(live);
  window.announce = msg => { live.textContent = ''; setTimeout(() => live.textContent = msg, 50); };
})();
