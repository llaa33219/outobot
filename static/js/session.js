/**
 * Session Management for OutObot
 * Handles loading and saving sessions via API
 */

class SessionManager {
  constructor(chat) {
    this.chat = chat;
  }

  async loadSessions() {
    try {
      const res = await fetch('/api/sessions');
      const data = await res.json();
      this.chat.sessions = data.sessions || [];
    } catch (err) {
      console.error('Failed to load sessions:', err);
    }
  }

  async loadSession(sessionId) {
    try {
      const res = await fetch(`/api/session/${sessionId}`);
      const data = await res.json();
      return data;
    } catch (err) {
      console.error('Failed to load session:', err);
      return null;
    }
  }

  renderSessionList() {
    const list = this.chat.els.sessionList;
    list.innerHTML = '';
    
    if (this.chat.sessions.length === 0) {
      list.innerHTML = '<div class="session-empty">No sessions yet</div>';
      return;
    }
    
    this.chat.sessions.forEach((sessionId) => {
      const item = document.createElement('div');
      item.className = 'session-item';
      item.textContent = sessionId.length > 12 ? sessionId.substring(0, 12) + '...' : sessionId;
      item.addEventListener('click', () => this.chat.loadSessionData(sessionId));
      list.appendChild(item);
    });
  }
}

// Export for use in other modules
window.SessionManager = SessionManager;
