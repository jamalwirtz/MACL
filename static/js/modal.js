/* ═══════════════════════════════════════════════════════════════
   MUDDO AGRO — PRODUCT MODAL
   ═══════════════════════════════════════════════════════════════ */

const overlay    = document.getElementById('productModalOverlay');
const modalImg   = document.getElementById('modalImg');
const modalTag   = document.getElementById('modalTag');
const modalName  = document.getElementById('modalName');
const modalDesc  = document.getElementById('modalDesc');
const modalIngr  = document.getElementById('modalIngr');
const modalForm  = document.getElementById('modalForm');
const modalCrops = document.getElementById('modalCrops');
const modalDose  = document.getElementById('modalDose');
const modalPack  = document.getElementById('modalPack');
const modalEnqBtn= document.getElementById('modalEnqBtn');
const modalViewBtn=document.getElementById('modalViewBtn');
const modalCounter=document.getElementById('modalCounter');

let allCards = [];
let currentIdx = 0;

function openModal(idx) {
  if (!overlay || !allCards.length) return;
  currentIdx = idx;
  const card = allCards[idx];
  const data = card.dataset;

  // Image
  if (modalImg) modalImg.src = data.img || 'https://images.unsplash.com/photo-1416879595882-3373a0480b5b?w=800';
  // Tag
  if (modalTag) {
    const tagMap = { pesticide:'#c0392b,🐛 Pesticide', herbicide:'var(--green-mid),🌱 Herbicide', fungicide:'#7b52d4,🔬 Fungicide', other:'var(--brown),📦 Agri Input' };
    const [color, label] = (tagMap[data.cat] || 'var(--brown),📦 Agri Input').split(',');
    modalTag.textContent = label;
    modalTag.style.background = color + '18';
    modalTag.style.color = color;
  }
  if (modalName)  modalName.textContent  = data.name  || '';
  if (modalDesc)  modalDesc.textContent  = data.desc  || '';
  if (modalIngr)  modalIngr.textContent  = data.ingr  || '—';
  if (modalForm)  modalForm.textContent  = data.form  || '—';
  if (modalCrops) modalCrops.textContent = data.crops || '—';
  if (modalDose)  modalDose.textContent  = data.dose  || '—';
  if (modalPack)  modalPack.textContent  = data.pack  || '—';
  if (modalEnqBtn) modalEnqBtn.href = '/contact?subject=Enquiry+' + encodeURIComponent(data.name || '');
  if (modalViewBtn) modalViewBtn.href = '/product/' + (data.id || '');
  if (modalCounter) modalCounter.textContent = (idx + 1) + ' / ' + allCards.length;

  overlay.classList.add('open');
  document.body.style.overflow = 'hidden';
}

function closeModal() {
  if (!overlay) return;
  overlay.classList.remove('open');
  document.body.style.overflow = '';
}

function modalNav(dir) {
  const n = ((currentIdx + dir) + allCards.length) % allCards.length;
  openModal(n);
}

// Close on overlay click
overlay?.addEventListener('click', e => { if (e.target === overlay) closeModal(); });

// Close on Escape
document.addEventListener('keydown', e => { if (e.key === 'Escape') closeModal(); });

// Arrow key navigation
document.addEventListener('keydown', e => {
  if (!overlay?.classList.contains('open')) return;
  if (e.key === 'ArrowRight') modalNav(1);
  if (e.key === 'ArrowLeft')  modalNav(-1);
});

// Bind "Quick View" buttons
function initProductModals() {
  allCards = [...document.querySelectorAll('.product-card[data-id]')];
  allCards.forEach((card, i) => {
    // Quick view button
    let qvBtn = card.querySelector('.quick-view-btn');
    if (!qvBtn) {
      qvBtn = document.createElement('button');
      qvBtn.className = 'quick-view-btn';
      qvBtn.innerHTML = '<i class="fas fa-eye" style="margin-right:5px;"></i>Quick View';
      card.querySelector('.product-card-img')?.appendChild(qvBtn);
    }
    qvBtn.addEventListener('click', e => { e.preventDefault(); e.stopPropagation(); openModal(i); });
    // Clicking the card image also opens modal
    card.querySelector('.product-card-img')?.addEventListener('click', e => {
      if (!e.target.closest('a') && !e.target.closest('button')) { e.preventDefault(); openModal(i); }
    });
  });
}

document.addEventListener('DOMContentLoaded', initProductModals);
// Also run immediately in case DOM is already loaded
if (document.readyState !== 'loading') initProductModals();
