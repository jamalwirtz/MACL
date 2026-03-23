/* MUDDO AGRO — MAIN JS (Enhanced) */

// NAVBAR SCROLL
const navbar = document.getElementById('navbar');
if (navbar) window.addEventListener('scroll', () => navbar.classList.toggle('scrolled', window.scrollY > 30), { passive: true });

// HAMBURGER
const hamburger = document.getElementById('hamburger');
const navLinks  = document.getElementById('navLinks');
if (hamburger && navLinks) hamburger.addEventListener('click', () => { navLinks.classList.toggle('open'); hamburger.classList.toggle('open'); });
document.querySelectorAll('.dropdown-toggle').forEach(t => t.addEventListener('click', e => { if (window.innerWidth <= 768) { e.preventDefault(); t.closest('.nav-dropdown').classList.toggle('open'); } }));

// SCROLL REVEAL
const revealObserver = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      const delay = entry.target.dataset.revealDelay || 0;
      setTimeout(() => entry.target.classList.add('revealed'), Number(delay));
      revealObserver.unobserve(entry.target);
    }
  });
}, { threshold: 0.1, rootMargin: '0px 0px -40px 0px' });
document.querySelectorAll('[data-reveal]').forEach((el, i) => {
  if (!el.dataset.revealDelay) {
    const siblings = el.parentElement ? [...el.parentElement.children].filter(c => c.hasAttribute('data-reveal')) : [];
    el.dataset.revealDelay = siblings.indexOf(el) * 80;
  }
  revealObserver.observe(el);
});

// ANIMATED COUNTERS
function animateCounter(el) {
  const target = parseInt(el.dataset.target, 10);
  const duration = 1600;
  const start = performance.now();
  const update = (time) => {
    const p = Math.min((time - start) / duration, 1);
    el.textContent = Math.round((1 - Math.pow(1 - p, 3)) * target);
    if (p < 1) requestAnimationFrame(update);
  };
  requestAnimationFrame(update);
}
const counterObs = new IntersectionObserver((entries) => {
  entries.forEach(e => { if (e.isIntersecting && !e.target.dataset.done) { e.target.dataset.done = '1'; animateCounter(e.target); } });
}, { threshold: 0.5 });
document.querySelectorAll('[data-target]').forEach(c => counterObs.observe(c));

// RIPPLE EFFECT
document.addEventListener('click', (e) => {
  const btn = e.target.closest('.btn-primary, .btn-green, .btn-ripple, .nav-cta');
  if (!btn) return;
  const rect = btn.getBoundingClientRect();
  const ripple = document.createElement('span');
  ripple.className = 'ripple';
  ripple.style.left = (e.clientX - rect.left) + 'px';
  ripple.style.top  = (e.clientY - rect.top) + 'px';
  btn.classList.add('btn-ripple');
  btn.appendChild(ripple);
  setTimeout(() => ripple.remove(), 600);
});

// LEAF PARTICLES
function spawnLeaves() {
  const container = document.querySelector('.hero-particles');
  if (!container) return;
  const leaves = ['🌿','🍃','✦','❋'];
  for (let i = 0; i < 14; i++) {
    const el = document.createElement('span');
    el.className = 'leaf-particle';
    el.textContent = leaves[Math.floor(Math.random() * leaves.length)];
    el.style.left = Math.random() * 100 + '%';
    el.style.animationDuration = (8 + Math.random() * 12) + 's';
    el.style.animationDelay    = (Math.random() * 10) + 's';
    el.style.fontSize = (12 + Math.random() * 12) + 'px';
    el.style.opacity  = (0.1 + Math.random() * 0.25).toString();
    container.appendChild(el);
  }
}
spawnLeaves();

// CAROUSEL CLASS
class Carousel {
  constructor(el) {
    this.el    = el;
    this.track = el.querySelector('.hero-slides');
    this.items = el.querySelectorAll('.hero-slide');
    this.dots  = el.querySelectorAll('.carousel-dot');
    this.cur   = 0; this.auto = null;
    this.el.querySelector('.carousel-prev')?.addEventListener('click', () => this.go(this.cur - 1));
    this.el.querySelector('.carousel-next')?.addEventListener('click', () => this.go(this.cur + 1));
    this.dots.forEach((d, i) => d.addEventListener('click', () => this.go(i)));
    this.startAuto();
    this.el.addEventListener('mouseenter', () => this.stopAuto());
    this.el.addEventListener('mouseleave', () => this.startAuto());
  }
  go(n) {
    this.cur = ((n % this.items.length) + this.items.length) % this.items.length;
    if (this.track) this.track.style.transform = `translateX(-${this.cur * 100}%)`;
    this.dots.forEach((d, i) => d.classList.toggle('active', i === this.cur));
  }
  startAuto() { this.auto = setInterval(() => this.go(this.cur + 1), 4200); }
  stopAuto()  { clearInterval(this.auto); }
}
document.querySelectorAll('.hero-carousel').forEach(el => new Carousel(el));

// PRODUCT SEARCH
const productSearch = document.getElementById('productSearch');
if (productSearch) productSearch.addEventListener('input', () => {
  const q = productSearch.value.toLowerCase();
  document.querySelectorAll('.product-card').forEach(card => card.style.display = card.textContent.toLowerCase().includes(q) ? '' : 'none');
});

// FLASH AUTO-CLOSE
setTimeout(() => document.querySelectorAll('.flash').forEach(f => { f.style.transition='opacity .3s'; f.style.opacity='0'; setTimeout(()=>f.remove(),300); }), 5000);

// PAGE TRANSITION
document.querySelectorAll('a:not([href^="#"]):not([target="_blank"]):not([href^="mailto"]):not([href^="tel"])').forEach(a => {
  a.addEventListener('click', e => { if (a.href && a.href !== window.location.href && !e.ctrlKey && !e.metaKey) { document.body.style.opacity='0'; document.body.style.transition='opacity .18s ease'; } });
});
window.addEventListener('pageshow', () => { document.body.style.opacity='1'; document.body.style.transition='opacity .3s ease'; });

// TILT ON STAT CARDS
document.querySelectorAll('.hero-stat-card').forEach(card => {
  card.addEventListener('mousemove', e => {
    const r = card.getBoundingClientRect();
    const x = (e.clientX - r.left) / r.width - 0.5, y = (e.clientY - r.top) / r.height - 0.5;
    card.style.transform = `perspective(600px) rotateY(${x*10}deg) rotateX(${-y*10}deg) translateY(-4px)`;
  });
  card.addEventListener('mouseleave', () => card.style.transform = '');
});

// ─── NAV SEARCH AUTOCOMPLETE ──────────────────────────────────────────────
const navSearch = document.getElementById('navSearch');
const searchDrop = document.getElementById('searchDropdown');
let searchTimer;

function toggleSearchExpand() {
  const input = document.getElementById('navSearch');
  input.style.width   = '180px';
  input.style.opacity = '1';
  input.focus();
}
function collapseSearch() {
  const input = document.getElementById('navSearch');
  input.style.width   = '0';
  input.style.opacity = '0';
  if (searchDrop) searchDrop.style.display = 'none';
}

if (navSearch) {
  navSearch.addEventListener('input', () => {
    clearTimeout(searchTimer);
    const q = navSearch.value.trim();
    if (q.length < 2) { searchDrop.style.display = 'none'; return; }
    searchTimer = setTimeout(async () => {
      try {
        const res  = await fetch(`/api/search?q=${encodeURIComponent(q)}`);
        const data = await res.json();
        if (!data.length) { searchDrop.style.display = 'none'; return; }
        const catColors = {pesticide:'#c0392b',herbicide:'#2d6e35',fungicide:'#3f51b5',other:'#f57c00'};
        searchDrop.innerHTML = data.map(p => `
          <a href="/product/${p.id}" style="display:flex;align-items:center;gap:10px;padding:10px 14px;text-decoration:none;border-bottom:1px solid var(--border-color);transition:background .15s;" onmouseover="this.style.background='var(--bg-alt)'" onmouseout="this.style.background=''">
            <img src="${p.image}" style="width:36px;height:36px;border-radius:8px;object-fit:cover;flex-shrink:0;">
            <div style="min-width:0;flex:1;">
              <div style="font-size:.86rem;font-weight:700;color:var(--text-primary);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">${p.name}</div>
              <span style="font-size:.68rem;font-weight:800;padding:2px 7px;border-radius:100px;background:${catColors[p.category] || '#607d8b'}22;color:${catColors[p.category] || '#607d8b'};text-transform:capitalize;">${p.category}</span>
            </div>
          </a>`).join('') +
          `<a href="/search?q=${encodeURIComponent(q)}" style="display:block;padding:10px 14px;font-size:.82rem;font-weight:700;color:var(--green-mid);text-align:center;text-decoration:none;" onmouseover="this.style.background='var(--bg-alt)'" onmouseout="this.style.background=''">See all results for "${q}" →</a>`;
        searchDrop.style.display = 'block';
      } catch(e) { /* silent */ }
    }, 280);
  });
  navSearch.addEventListener('keydown', e => {
    if (e.key === 'Escape') collapseSearch();
  });
  document.addEventListener('click', e => {
    if (!e.target.closest('#navSearchWrap')) { searchDrop.style.display = 'none'; }
  });
}

// ─── NEWSLETTER FORM ──────────────────────────────────────────────────────
async function submitNewsletter(e) {
  e.preventDefault();
  const form  = document.getElementById('newsletterForm');
  const msg   = document.getElementById('newsletterMsg');
  const email = form.querySelector('[name=email]').value;
  const btn   = form.querySelector('button[type=submit]');
  btn.disabled = true;
  btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Subscribing…';
  try {
    const res  = await fetch('/newsletter/subscribe', { method:'POST', headers:{'Content-Type':'application/x-www-form-urlencoded'}, body:`email=${encodeURIComponent(email)}`});
    const data = await res.json();
    msg.textContent = data.msg;
    msg.style.color = data.ok ? '#a5d6a7' : '#ef9a9a';
    if (data.ok) {
      form.querySelector('[name=email]').value = '';
      btn.innerHTML = '<i class="fas fa-check"></i> Subscribed!';
    } else {
      btn.disabled = false;
      btn.innerHTML = '<i class="fas fa-paper-plane"></i> Subscribe';
    }
  } catch(err) {
    msg.textContent = 'Something went wrong. Please try again.';
    btn.disabled = false;
    btn.innerHTML = '<i class="fas fa-paper-plane"></i> Subscribe';
  }
}

// ─── GLOBAL SEARCH BAR ───────────────────────────────────────────────────
(function() {
  const form   = document.getElementById('globalSearchForm');
  const input  = document.getElementById('globalSearchInput');
  const toggle = document.getElementById('searchToggle');
  if (!form || !input || !toggle) return;

  let suggestBox = null;
  let debounceT  = null;

  toggle.addEventListener('click', () => {
    form.classList.toggle('open');
    if (form.classList.contains('open')) {
      input.focus();
    } else {
      input.value = '';
      removeSuggestions();
    }
  });

  input.addEventListener('input', () => {
    clearTimeout(debounceT);
    const q = input.value.trim();
    if (q.length < 2) { removeSuggestions(); return; }
    debounceT = setTimeout(() => fetchSuggestions(q), 220);
  });

  input.addEventListener('keydown', e => {
    if (e.key === 'Escape') { form.classList.remove('open'); input.value = ''; removeSuggestions(); }
    if (e.key === 'Enter')  { e.preventDefault(); form.submit(); }
  });

  async function fetchSuggestions(q) {
    try {
      const res  = await fetch(`/api/search?q=${encodeURIComponent(q)}&limit=6`);
      const data = await res.json();
      showSuggestions(data.results || [], q);
    } catch {}
  }

  function showSuggestions(results, q) {
    removeSuggestions();
    suggestBox = document.createElement('div');
    suggestBox.className = 'search-suggestions';

    if (!results.length) {
      suggestBox.innerHTML = `<div class="ss-empty"><i class="fas fa-search" style="display:block;margin-bottom:6px;color:var(--border-color);font-size:1.4rem;"></i>No results for "<strong>${q}</strong>"</div>`;
    } else {
      results.forEach(r => {
        const a = document.createElement('a');
        a.className = 'search-suggestion-item';
        a.href = `/product/${r.id}`;
        a.innerHTML = `
          <img class="ss-img" src="${r.image || ''}" alt="${r.name}" loading="lazy"
               onerror="this.style.background='var(--bg-alt)';this.src=''">
          <div>
            <div class="ss-name">${highlight(r.name, q)}</div>
            <div class="ss-cat">${r.category}</div>
          </div>`;
        suggestBox.appendChild(a);
      });
      const viewAll = document.createElement('a');
      viewAll.href = `/search?q=${encodeURIComponent(q)}`;
      viewAll.style.cssText = 'display:block;padding:11px 14px;text-align:center;font-size:.82rem;font-weight:700;color:var(--green-mid);border-top:1px solid var(--border-color);text-decoration:none;';
      viewAll.textContent = `View all results for "${q}" →`;
      suggestBox.appendChild(viewAll);
    }

    form.style.position = 'relative';
    form.appendChild(suggestBox);
  }

  function removeSuggestions() {
    if (suggestBox) { suggestBox.remove(); suggestBox = null; }
  }

  function highlight(text, q) {
    const re = new RegExp(`(${q.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
    return text.replace(re, '<mark style="background:rgba(200,168,75,.35);border-radius:2px;padding:0 1px;">$1</mark>');
  }

  document.addEventListener('click', e => {
    if (!form.contains(e.target)) { form.classList.remove('open'); input.value = ''; removeSuggestions(); }
  });
})();

// ─── PRODUCT SHARE BUTTONS ──────────────────────────────────────────────
window.shareProduct = function(method, name, url) {
  const fullUrl = url || window.location.href;
  const text    = `Check out ${name} from Muddo Agro Chemicals LTD`;
  if (method === 'wa') {
    window.open(`https://wa.me/?text=${encodeURIComponent(text + ' ' + fullUrl)}`, '_blank');
  } else if (method === 'fb') {
    window.open(`https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(fullUrl)}`, '_blank', 'width=600,height=400');
  } else if (method === 'copy') {
    navigator.clipboard.writeText(fullUrl).then(() => {
      const btn = document.querySelector('.share-btn.cp');
      if (btn) {
        const orig = btn.innerHTML;
        btn.innerHTML = '<i class="fas fa-check"></i> Copied!';
        btn.style.background = 'var(--green-mid)'; btn.style.color = '#fff';
        setTimeout(() => { btn.innerHTML = orig; btn.style.background = ''; btn.style.color = ''; }, 2000);
      }
    }).catch(() => alert('Link: ' + fullUrl));
  } else if (method === 'print') {
    window.print();
  }
};

// ─── NEWSLETTER FORM ─────────────────────────────────────────────────────
const nlForm = document.getElementById('newsletterForm');
if (nlForm) {
  nlForm.addEventListener('submit', async e => {
    e.preventDefault();
    const email = nlForm.querySelector('input[type=email]')?.value;
    const name  = nlForm.querySelector('input[name=name]')?.value || '';
    if (!email) return;
    const btn = nlForm.querySelector('button[type=submit]');
    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
    try {
      const res = await fetch('/subscribe', {
        method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ email, name })
      });
      const data = await res.json();
      nlForm.innerHTML = `<div style="color:#f5c842;font-size:1rem;font-weight:700;text-align:center;padding:14px;">
        <i class="fas fa-check-circle" style="font-size:1.5rem;display:block;margin-bottom:8px;"></i>
        ${data.message || 'Thank you for subscribing!'}
      </div>`;
    } catch {
      btn.disabled = false;
      btn.innerHTML = '<i class="fas fa-paper-plane"></i> Subscribe';
    }
  });
}
