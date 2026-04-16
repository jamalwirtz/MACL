/* ══════════════════════════════════════════════════════════
   MUDDO AGRO — MAIN JS  v5
   Scroll reveal · progress bar · hamburger · modals · 
   search suggest · theme · back-to-top · ripple
══════════════════════════════════════════════════════════ */

(function(){
  "use strict";

  // ── SCROLL PROGRESS BAR ─────────────────────────────────
  const prog = document.querySelector('.scroll-progress');
  if(prog){
    window.addEventListener('scroll', () => {
      const pct = (window.scrollY / (document.documentElement.scrollHeight - window.innerHeight)) * 100;
      prog.style.width = Math.min(100, pct) + '%';
    }, {passive:true});
  }

  // ── NAVBAR SCROLL CLASS ──────────────────────────────────
  const navbar = document.getElementById('navbar');
  if(navbar) window.addEventListener('scroll', () =>
    navbar.classList.toggle('scrolled', window.scrollY > 40), {passive:true});

  // ── HAMBURGER ────────────────────────────────────────────
  const hamburger = document.getElementById('hamburger');
  const navLinks  = document.getElementById('navLinks');
  if(hamburger && navLinks){
    hamburger.addEventListener('click', e => {
      e.stopPropagation();
      const open = navLinks.classList.toggle('open');
      hamburger.classList.toggle('open', open);
      hamburger.setAttribute('aria-expanded', open);
    });
    document.addEventListener('click', e => {
      if(!navbar.contains(e.target)){
        navLinks.classList.remove('open');
        hamburger.classList.remove('open');
        hamburger.setAttribute('aria-expanded','false');
      }
    });
    navLinks.querySelectorAll('a').forEach(a => a.addEventListener('click', () => {
      if(window.innerWidth <= 768){
        navLinks.classList.remove('open');
        hamburger.classList.remove('open');
        hamburger.setAttribute('aria-expanded','false');
      }
    }));
  }

  // Mobile dropdown toggle
  document.querySelectorAll('.dropdown-toggle').forEach(t => {
    t.addEventListener('click', e => {
      if(window.innerWidth <= 768){
        e.preventDefault();
        t.closest('.nav-dropdown').classList.toggle('open');
      }
    });
  });

  // ── SCROLL REVEAL ────────────────────────────────────────
  const reveals = document.querySelectorAll('[data-reveal]');
  if(reveals.length && 'IntersectionObserver' in window){
    const io = new IntersectionObserver(entries => {
      entries.forEach(en => {
        if(en.isIntersecting){
          const delay = en.target.dataset.revealDelay ? parseInt(en.target.dataset.revealDelay) : 0;
          setTimeout(() => en.target.classList.add('revealed'), delay);
          io.unobserve(en.target);
        }
      });
    }, {threshold: .12, rootMargin: '0px 0px -40px 0px'});
    reveals.forEach(el => io.observe(el));
  }

  // ── BACK TO TOP ──────────────────────────────────────────
  const btt = document.getElementById('backToTop');
  if(btt){
    window.addEventListener('scroll', () =>
      btt.classList.toggle('visible', window.scrollY > 400), {passive:true});
    btt.addEventListener('click', () =>
      window.scrollTo({top:0, behavior:'smooth'}));
  }

  // ── RIPPLE BUTTONS ───────────────────────────────────────
  document.querySelectorAll('.btn-ripple').forEach(btn => {
    btn.addEventListener('click', e => {
      const rect = btn.getBoundingClientRect();
      const rip  = document.createElement('span');
      rip.style.cssText = [
        'position:absolute','border-radius:50%','width:6px','height:6px','margin:-3px',
        'background:rgba(255,255,255,.35)',
        'animation:rippleEffect .55s ease-out forwards','pointer-events:none',
        `left:${e.clientX - rect.left}px`,
        `top:${e.clientY - rect.top}px`
      ].join(';');
      btn.appendChild(rip);
      setTimeout(() => rip.remove(), 600);
    });
  });

  // ── THEME TOGGLE (global function) ───────────────────────
  window.toggleTheme = function(){
    const next = document.documentElement.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', next);
    try { localStorage.setItem('muddo-theme', next); } catch(e){}
  };

  // ── GLOBAL SEARCH SUGGESTIONS ────────────────────────────
  const searchInput = document.getElementById('globalSearchInput');
  const searchSugBox = document.getElementById('searchSuggestions');
  if(searchInput && searchSugBox){
    let debTimer;
    searchInput.addEventListener('input', () => {
      clearTimeout(debTimer);
      const q = searchInput.value.trim();
      if(!q){ searchSugBox.innerHTML = ''; searchSugBox.style.display = 'none'; return; }
      debTimer = setTimeout(() => fetchSuggestions(q), 250);
    });
    document.addEventListener('click', e => {
      if(!searchInput.closest('form').contains(e.target)){
        searchSugBox.innerHTML = ''; searchSugBox.style.display = 'none';
      }
    });
    searchInput.addEventListener('keydown', e => {
      if(e.key === 'Enter'){
        e.preventDefault();
        window.location.href = '/search?q=' + encodeURIComponent(searchInput.value.trim());
      }
    });
  }

  function fetchSuggestions(q){
    fetch('/api/search?q=' + encodeURIComponent(q))
      .then(r => r.json())
      .then(data => {
        if(!searchSugBox) return;
        if(!data.length){ searchSugBox.innerHTML = ''; searchSugBox.style.display = 'none'; return; }
        searchSugBox.style.display = 'block';
        searchSugBox.innerHTML = data.slice(0,6).map(p => `
          <a href="/product/${p.id}" class="search-suggestion-item" style="display:flex;align-items:center;gap:10px;padding:9px 14px;border-bottom:1px solid var(--bd2);text-decoration:none;transition:background .15s;">
            <img src="${p.image}" alt="${p.name}" class="ss-img" onerror="this.style.display='none'">
            <div><div class="ss-name">${p.name}</div><div class="ss-cat">${p.category}</div></div>
          </a>`).join('');
      }).catch(() => {});
  }

  // Keyboard shortcut: / to focus search
  document.addEventListener('keydown', e => {
    if(e.key === '/' && document.activeElement.tagName !== 'INPUT' && document.activeElement.tagName !== 'TEXTAREA'){
      e.preventDefault();
      const si = document.getElementById('globalSearchInput');
      if(si){ si.focus(); si.select(); }
    }
  });

  // ── PRODUCT MODALS ───────────────────────────────────────
  window.openProductModal = function(productId){
    fetch('/product/' + productId + '?modal=1')
      .then(r => r.text())
      .then(html => {
        const overlay = document.createElement('div');
        overlay.className = 'modal-overlay';
        overlay.style.cssText = 'position:fixed;inset:0;background:rgba(8,6,15,.8);backdrop-filter:blur(6px);z-index:10000;display:flex;align-items:center;justify-content:center;padding:20px;';
        overlay.innerHTML = `<div class="product-modal" style="position:relative;max-width:600px;width:100%;max-height:90vh;overflow-y:auto;border-radius:20px;background:var(--bg-c);border:1.5px solid var(--bd);box-shadow:0 24px 80px rgba(0,0,0,.25);animation:modalSlideIn .3s cubic-bezier(.34,1.56,.64,1);">${html}</div>`;
        overlay.addEventListener('click', e => { if(e.target === overlay) closeModal(overlay); });
        document.body.appendChild(overlay);
        document.body.style.overflow = 'hidden';
      }).catch(() => window.location.href = '/product/' + productId);
  };

  window.closeModal = function(overlay){
    if(!overlay) overlay = document.querySelector('.modal-overlay');
    if(overlay){ overlay.remove(); document.body.style.overflow = ''; }
  };

  document.addEventListener('keydown', e => {
    if(e.key === 'Escape') closeModal();
  });

  // ── NEWSLETTER FORM ──────────────────────────────────────
  const nForm = document.getElementById('newsletterForm');
  if(nForm){
    nForm.addEventListener('submit', async e => {
      e.preventDefault();
      const email = nForm.querySelector('[name=email]')?.value;
      const btn   = nForm.querySelector('button[type=submit]');
      if(!email) return;
      const orig = btn.innerHTML;
      btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Subscribing…';
      btn.disabled = true;
      try {
        const res = await fetch('/subscribe', {
          method: 'POST',
          headers: {'Content-Type':'application/json'},
          body: JSON.stringify({email, name: ''})
        });
        const data = await res.json();
        if(data.ok){
          btn.innerHTML = '<i class="fas fa-check"></i> Subscribed!';
          btn.style.background = '#3a5a20';
          nForm.querySelector('[name=email]').value = '';
          setTimeout(() => { btn.innerHTML = orig; btn.disabled = false; btn.style.background = ''; }, 3000);
        } else {
          btn.innerHTML = data.msg || 'Try again';
          setTimeout(() => { btn.innerHTML = orig; btn.disabled = false; }, 2500);
        }
      } catch(err){
        btn.innerHTML = 'Error — try again';
        setTimeout(() => { btn.innerHTML = orig; btn.disabled = false; }, 2500);
      }
    });
  }

  // ── SCROLL PROGRESS BAR: inject if missing ───────────────
  if(!document.querySelector('.scroll-progress')){
    const bar = document.createElement('div');
    bar.className = 'scroll-progress';
    bar.style.cssText = 'position:fixed;top:0;left:0;height:3px;z-index:10001;background:linear-gradient(90deg,#e8651a,#1a6abf,#ffd080);pointer-events:none;width:0;transition:width .1s;box-shadow:0 0 8px rgba(232,101,26,.4);';
    document.body.prepend(bar);
  }

  // ── STATS COUNTER ANIMATION ──────────────────────────────
  function animateCount(el){
    const target = parseInt(el.dataset.target || el.textContent);
    if(isNaN(target)) return;
    const duration = 1200;
    const start = Date.now();
    const from = 0;
    const tick = () => {
      const elapsed = Date.now() - start;
      const progress = Math.min(elapsed / duration, 1);
      const ease = 1 - Math.pow(1 - progress, 3);
      el.textContent = Math.round(from + (target - from) * ease) + (el.dataset.suffix || '');
      if(progress < 1) requestAnimationFrame(tick);
    };
    requestAnimationFrame(tick);
  }
  document.querySelectorAll('.count-up').forEach(el => {
    const io = new IntersectionObserver(entries => {
      if(entries[0].isIntersecting){ animateCount(el); io.disconnect(); }
    }, {threshold:.5});
    io.observe(el);
  });

  // ── SHARE BUTTONS ────────────────────────────────────────
  window.shareWhatsApp = function(text){
    const url = encodeURIComponent(text + ' ' + window.location.href);
    window.open('https://wa.me/?text=' + url, '_blank');
  };
  window.shareFacebook = function(){
    window.open('https://www.facebook.com/sharer/sharer.php?u=' + encodeURIComponent(window.location.href), '_blank', 'width=600,height=400');
  };
  window.copyLink = function(){
    navigator.clipboard?.writeText(window.location.href).then(() => {
      const btn = event.currentTarget;
      const orig = btn.innerHTML;
      btn.innerHTML = '<i class="fas fa-check"></i> Copied!';
      setTimeout(() => btn.innerHTML = orig, 2000);
    });
  };

  // ── TOAST NOTIFICATION SYSTEM ────────────────────────────
  window.toast = {
    show(msg, type='info', dur=3500){
      let container = document.querySelector('.flash-container');
      if(!container){
        container = document.createElement('div');
        container.className = 'flash-container';
        document.body.appendChild(container);
      }
      const el = document.createElement('div');
      el.className = `flash flash-${type} slide-in-right`;
      el.innerHTML = `<i class="fas fa-${type==='error'?'exclamation-circle':type==='success'?'check-circle':'info-circle'}"></i><span>${msg}</span><button class="flash-close" onclick="this.closest('.flash').remove()"><i class="fas fa-times"></i></button>`;
      container.appendChild(el);
      setTimeout(() => {
        el.style.animation = 'toastOut .35s ease forwards';
        setTimeout(() => el.remove(), 380);
      }, dur);
    },
    success(msg){ this.show(msg,'success'); },
    error(msg)  { this.show(msg,'error'); },
    info(msg)   { this.show(msg,'info'); }
  };

  // ── LAZY IMAGES ──────────────────────────────────────────
  if('IntersectionObserver' in window){
    const io = new IntersectionObserver(entries => {
      entries.forEach(en => {
        if(en.isIntersecting){
          const img = en.target;
          if(img.dataset.src){ img.src = img.dataset.src; delete img.dataset.src; }
          img.classList.add('loaded');
          io.unobserve(img);
        }
      });
    }, {rootMargin:'100px'});
    document.querySelectorAll('img[loading="lazy"]').forEach(img => io.observe(img));
  }

})(); // end IIFE
