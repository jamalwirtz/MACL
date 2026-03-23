/* ═══════════════════════════════════════════════════════════════
   MUDDO AGRO — CHAT SYSTEM
   ═══════════════════════════════════════════════════════════════ */

class MuddoChat {
  constructor() {
    this.currentWith  = null;  // {id, role, name}
    this.lastMsgId    = 0;
    this.pollInterval = null;
    this.container    = document.getElementById('chatMessages');
    this.inputBox     = document.getElementById('chatInput');
    this.sendBtn      = document.getElementById('chatSendBtn');
    this.headerName   = document.getElementById('chatHeaderName');
    this.headerStatus = document.getElementById('chatHeaderStatus');
    this.headerAvatar = document.getElementById('chatHeaderAvatar');
    this.chatMain     = document.getElementById('chatMainArea');
    this.chatEmpty    = document.getElementById('chatEmptyState');
    this.myInitial    = document.body.dataset.userInitial || 'U';
    this.myId         = parseInt(document.body.dataset.userId || '0', 10);
    this.myRole       = document.body.dataset.userRole || 'agent';

    if (this.sendBtn)  this.sendBtn.addEventListener('click', () => this.sendMessage());
    if (this.inputBox) {
      this.inputBox.addEventListener('keydown', e => {
        if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); this.sendMessage(); }
      });
      // Auto-resize textarea
      this.inputBox.addEventListener('input', () => {
        this.inputBox.style.height = 'auto';
        this.inputBox.style.height = Math.min(this.inputBox.scrollHeight, 120) + 'px';
      });
    }

    // Contact click handlers
    document.querySelectorAll('.chat-contact[data-id]').forEach(el => {
      el.addEventListener('click', () => this.selectContact(el));
    });

    // If a contact is pre-selected via URL hash, open it
    const hash = window.location.hash.replace('#chat-', '');
    if (hash) {
      const preselect = document.querySelector(`.chat-contact[data-id="${hash}"]`);
      if (preselect) this.selectContact(preselect);
    }

    // Start unread badge polling (always active)
    this.pollUnread();
    setInterval(() => this.pollUnread(), 6000);
  }

  selectContact(el) {
    document.querySelectorAll('.chat-contact').forEach(c => c.classList.remove('active'));
    el.classList.add('active');
    el.querySelector('.chat-unread-badge')?.remove();

    this.currentWith = {
      id:   parseInt(el.dataset.id, 10),
      role: el.dataset.role || 'agent',
      name: el.dataset.name || 'User',
    };

    // Update header
    if (this.headerName)   this.headerName.textContent   = this.currentWith.name;
    if (this.headerStatus) this.headerStatus.innerHTML   = `<span class="status-dot ${el.dataset.status || 'offline'}"></span> ${el.dataset.status || 'offline'}`;
    if (this.headerAvatar) this.headerAvatar.textContent = this.currentWith.name.charAt(0).toUpperCase();
    if (this.chatMain)     this.chatMain.style.display   = 'flex';
    if (this.chatEmpty)    this.chatEmpty.style.display  = 'none';

    this.lastMsgId = 0;
    this.container.innerHTML = '';
    this.loadMessages(true);

    clearInterval(this.pollInterval);
    this.pollInterval = setInterval(() => this.loadMessages(false), 3000);
    this.inputBox?.focus();
  }

  async loadMessages(scroll) {
    if (!this.currentWith) return;
    try {
      const url = `/api/chat/messages?with_id=${this.currentWith.id}&with_role=${this.currentWith.role}&after=${this.lastMsgId}`;
      const res  = await fetch(url);
      const data = await res.json();
      if (!data.messages?.length) return;

      data.messages.forEach(m => {
        if (m.id <= this.lastMsgId) return;
        this.lastMsgId = m.id;
        this.appendMessage(m);
      });
      if (scroll) this.scrollBottom();
      else {
        const container = this.container;
        const atBottom  = container.scrollHeight - container.scrollTop - container.clientHeight < 80;
        if (atBottom) this.scrollBottom();
      }
      // Mark as read
      fetch(`/api/chat/mark-read`, { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ from_id: this.currentWith.id, from_role: this.currentWith.role }) });
    } catch(e) { /* silent */ }
  }

  appendMessage(m) {
    const isSent = (m.sender_role === this.myRole && m.sender_id === this.myId);
    const initial = isSent ? this.myInitial : (this.currentWith?.name?.charAt(0) || '?');
    const time = new Date(m.created_at).toLocaleTimeString([], { hour:'2-digit', minute:'2-digit' });

    const wrapper = document.createElement('div');
    wrapper.className = `chat-msg ${isSent ? 'sent' : 'received'}`;
    wrapper.innerHTML = `
      ${!isSent ? `<div class="msg-avatar">${initial}</div>` : ''}
      <div>
        <div class="msg-bubble">${this.escapeHtml(m.content)}<span class="msg-time">${time}</span></div>
      </div>
      ${isSent ? `<div class="msg-avatar" style="background:var(--gold);color:var(--green-deep);">${initial}</div>` : ''}
    `;
    this.container.appendChild(wrapper);
  }

  async sendMessage() {
    const content = this.inputBox?.value.trim();
    if (!content || !this.currentWith) return;
    this.inputBox.value = '';
    this.inputBox.style.height = 'auto';

    try {
      const res = await fetch('/api/chat/send', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ to_id: this.currentWith.id, to_role: this.currentWith.role, content })
      });
      const data = await res.json();
      if (data.message) {
        this.appendMessage(data.message);
        this.scrollBottom();
        // Update sidebar preview
        const contact = document.querySelector(`.chat-contact[data-id="${this.currentWith.id}"]`);
        const preview = contact?.querySelector('.chat-contact-preview');
        if (preview) preview.textContent = 'You: ' + content.substring(0, 40);
      }
    } catch(e) { this.inputBox.value = content; }
  }

  scrollBottom() {
    if (this.container) this.container.scrollTop = this.container.scrollHeight;
  }

  async pollUnread() {
    try {
      const res  = await fetch('/api/chat/unread');
      const data = await res.json();
      // Update nav badge
      const navBadge = document.getElementById('chatNavBadge');
      if (navBadge) {
        navBadge.textContent = data.total || '';
        navBadge.style.display = data.total ? '' : 'none';
      }
      // Update notification bell
      const bell = document.getElementById('notifCount');
      if (bell) bell.textContent = data.total || 0;

      // Update per-contact badges in sidebar
      if (data.per_contact) {
        Object.entries(data.per_contact).forEach(([key, count]) => {
          const [from_id, from_role] = key.split('_');
          const contact = document.querySelector(`.chat-contact[data-id="${from_id}"][data-role="${from_role}"]`);
          if (!contact) return;
          let badge = contact.querySelector('.chat-unread-badge');
          if (count > 0) {
            if (!badge) { badge = document.createElement('span'); badge.className = 'chat-unread-badge'; contact.querySelector('.chat-contact-meta')?.appendChild(badge); }
            badge.textContent = count;
          } else { badge?.remove(); }
        });
      }
    } catch(e) { /* silent */ }
  }

  escapeHtml(str) {
    return str.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/\n/g,'<br>');
  }
}

// Init on DOM ready
if (document.getElementById('chatMessages')) {
  window.muddoChat = new MuddoChat();
}
