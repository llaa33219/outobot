const PROVIDER_KEYS = [
  { name: 'openai', inputId: 'openaiKeyInput', statusId: 'openaiStatus', key: 'openai' },
  { name: 'anthropic', inputId: 'anthropicKeyInput', statusId: 'anthropicStatus', key: 'anthropic' },
  { name: 'google', inputId: 'googleKeyInput', statusId: 'googleStatus', key: 'google' },
  { name: 'minimax', inputId: 'minimaxKeyInput', statusId: 'minimaxStatus', key: 'minimax' },
  { name: 'glm', inputId: 'glmKeyInput', statusId: 'glmStatus', key: 'glm' },
  { name: 'kimi', inputId: 'kimiKeyInput', statusId: 'kimiStatus', key: 'kimi' },
];

const AGENT_DEFAULTS = {
  'outo': { icon: '🔆', label: 'OutObot', role: 'Coordinator', desc: 'Main orchestrator' },
  'peritus': { icon: '💠', label: 'Peritus', role: 'Professional', desc: 'General work' },
  'inquisitor': { icon: '🔎', label: 'Inquisitor', role: 'Research', desc: 'Research specialist' },
  'rimor': { icon: '⚡', label: 'Rimor', role: 'Explorer', desc: 'Fast exploration' },
  'recensor': { icon: '✔', label: 'Recensor', role: 'Review', desc: 'Verification' },
  'cogitator': { icon: '🧠', label: 'Cogitator', role: 'Thinking', desc: 'Deep analysis' },
  'creativus': { icon: '✨', label: 'Creativus', role: 'Creative', desc: 'Creative solutions' },
  'artifex': { icon: '🎭', label: 'Artifex', role: 'Artistic', desc: 'Design work' },
};

class OutObotChat {
  constructor() {
    this.els = {
      agentBar: document.getElementById('agentBar'),
      connectionStatus: document.getElementById('connectionStatus'),
      sidebarToggle: document.getElementById('sidebarToggle'),
      settingsToggle: document.getElementById('settingsToggle'),
      skillsToggle: document.getElementById('skillsToggle'),
      chatArea: document.getElementById('chatArea'),
      welcome: document.getElementById('welcome'),
      welcomeSetup: document.getElementById('welcomeSetup'),
      scrollBtn: document.getElementById('scrollBtn'),
      messageInput: document.getElementById('messageInput'),
      sendBtn: document.getElementById('sendBtn'),
      sidebar: document.getElementById('sidebar'),
      sidebarAgents: document.getElementById('sidebarAgents'),
      sidebarSessions: document.getElementById('sidebarSessions'),
      sessionList: document.getElementById('sessionList'),
      activityLog: document.getElementById('activityLog'),
      settingsModal: document.getElementById('settingsModal'),
      skillsModal: document.getElementById('skillsModal'),
      modalClose: document.getElementById('modalClose'),
      defaultProviderSelect: document.getElementById('defaultProviderSelect'),
      defaultModelSelect: document.getElementById('defaultModelSelect'),
      saveFeedback: document.getElementById('saveFeedback'),
      settingsCancel: document.getElementById('settingsCancel'),
      settingsSave: document.getElementById('settingsSave'),
      fileInput: document.getElementById('fileInput'),
      attachBtn: document.getElementById('attachBtn'),
      attachmentPreview: document.getElementById('attachmentPreview'),
    };

    this.pendingAttachments = [];
    this.providerConfig = {};
    this.agentConfig = AGENT_DEFAULTS;
    this.currentAgent = 'outo';
    this.currentSession = null;
    this.sessions = [];
    this.processing = false;
    this.userScrolledUp = false;
    
    this.ws = null;
    this.reconnectDelay = 1000;
    this.maxReconnectDelay = 10000;
    this.reconnecting = false;
    this.currentBubble = null;
    this.currentContentEl = null;
    this.currentActivityEl = null;
    this.activeAgents = new Set();
    this.involvedAgents = new Set();
    this.agentTokens = {};
    this.subAgentCards = {};
    this.contentStreamEl = null;
    this.currentTextSegment = null;
    this.currentSegmentText = '';
    this.hasStreamedTopLevel = false;
    this.callStack = [];
    this.agentStartTimes = {};
    this.agentMeta = AGENT_DEFAULTS;

    if (window.innerWidth <= 960) {
      this.els.sidebar.classList.add('collapsed');
    }

    if (typeof marked !== 'undefined') {
      marked.use({ breaks: true, gfm: true });
    }

    this.bindEvents();
    this.init();
  }

  bindEvents() {
    this.els.settingsToggle.addEventListener('click', () => this.openSettings());
    this.els.skillsToggle.addEventListener('click', () => this.openSkills());
    this.els.modalClose.addEventListener('click', () => this.closeSettings());
    document.getElementById('skillsModalClose')?.addEventListener('click', () => this.closeSkills());
    document.getElementById('skillsCloseBtn')?.addEventListener('click', () => this.closeSkills());
    document.getElementById('syncSkillsBtn')?.addEventListener('click', () => this.syncSkills());
    document.getElementById('installSkillBtn')?.addEventListener('click', () => this.installSkill());
    this.els.settingsCancel.addEventListener('click', () => this.closeSettings());
    this.els.settingsSave.addEventListener('click', () => this.saveSettings());
    this.els.sidebarToggle.addEventListener('click', () => this.toggleSidebar());
    this.els.sendBtn.addEventListener('click', () => this.sendMessage());
    this.els.attachBtn.addEventListener('click', () => this.els.fileInput.click());
    this.els.fileInput.addEventListener('change', (e) => this.handleFileSelect(e));

    this.els.messageInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        this.sendMessage();
      }
    });

    this.els.messageInput.addEventListener('input', () => this.autoResizeTextarea());

    this.els.chatArea.addEventListener('scroll', () => {
      const el = this.els.chatArea;
      const atBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 60;
      this.userScrolledUp = !atBottom;
      this.els.scrollBtn.classList.toggle('hidden', atBottom);
    });

    this.els.scrollBtn.addEventListener('click', () => this.scrollToBottom(true));

    document.querySelectorAll('.key-toggle').forEach((btn) => {
      btn.addEventListener('click', () => {
        const input = document.getElementById(btn.dataset.target);
        if (!input) return;
        const isPassword = input.type === 'password';
        input.type = isPassword ? 'text' : 'password';
        const openEye = btn.querySelector('.eye-open');
        const closedEye = btn.querySelector('.eye-closed');
        if (openEye && closedEye) {
          openEye.style.display = isPassword ? 'none' : '';
          closedEye.style.display = isPassword ? '' : 'none';
        }
      });
    });

    document.querySelectorAll('.key-clear').forEach((btn) => {
      btn.addEventListener('click', () => {
        const input = document.getElementById(btn.dataset.target);
        if (input) {
          input.value = '';
          input.focus();
        }
      });
    });

    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        if (!this.els.settingsModal.classList.contains('hidden')) {
          this.closeSettings();
        } else if (!this.els.sidebar.classList.contains('collapsed') && window.innerWidth <= 960) {
          this.toggleSidebar();
        }
      }
    });

    this.els.settingsModal.addEventListener('click', (e) => {
      if (e.target === this.els.settingsModal) {
        this.closeSettings();
      }
    });

    this.els.skillsModal?.addEventListener('click', (e) => {
      if (e.target === this.els.skillsModal) {
        this.closeSkills();
      }
    });

    this.els.defaultProviderSelect?.addEventListener('change', () => {
      this.updateDefaultModels();
    });
    this.els.defaultModelSelect?.addEventListener('change', () => {
    });

    document.getElementById('newSessionBtn')?.addEventListener('click', () => this.createNewSession());
  }

  async init() {
    this.updateConnectionStatus('connecting');
    
    try {
      await Promise.all([
        this.loadProviders(),
        this.loadAgents(),
        this.loadSessions(),
        this.loadSkills()
      ]);
      
      this.buildAgentBar();
      this.buildSidebarAgents();
      this.renderSessionList();
      this.checkWelcomeSetup();
      this.connectWebSocket();
    } catch (error) {
      console.error('Init error:', error);
      this.updateConnectionStatus('disconnected');
    }
  }

  connectWebSocket() {
    this.updateConnectionStatus('connecting');
    const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
    this.ws = new WebSocket(protocol + '//' + location.host + '/ws/chat');

    this.ws.onopen = () => {
      this.updateConnectionStatus('connected');
      this.reconnectDelay = 1000;
      this.reconnecting = false;
      this.logActivity('Connected to server');
    };

    this.ws.onclose = () => {
      this.updateConnectionStatus('disconnected');
      if (this.processing) {
        this.setProcessing(false);
        this.deactivateAllAgents();
      }
      this.reconnecting = true;
      setTimeout(() => {
        this.reconnectDelay = Math.min(this.reconnectDelay * 1.5, this.maxReconnectDelay);
        this.connectWebSocket();
      }, this.reconnectDelay);
    };

    this.ws.onerror = () => {
      this.updateConnectionStatus('disconnected');
    };

    this.ws.onmessage = (e) => {
      try {
        const event = JSON.parse(e.data);
        this.handleEvent(event);
      } catch (err) {
        console.error('Failed to parse event:', err);
      }
    };
  }

  handleEvent(event) {
    const { type, agent_name, data } = event;
    const agent = agent_name || 'outo';

    switch (type) {
      case 'token':
        this.ensureAgentBubble(agent);
        this.agentTokens[agent] = (this.agentTokens[agent] || '') + (data.content || '');
        if (this.subAgentCards[agent]) {
          const card = this.subAgentCards[agent];
          this._ensureCardTextSegment(card);
          card.currentSegmentText += data.content || '';
          card.currentTextSegment.textContent = card.currentSegmentText;
          card.contentStreamEl.scrollTop = card.contentStreamEl.scrollHeight;
        } else {
          this.ensureTextSegment();
          this.currentSegmentText += data.content || '';
          this.currentTextSegment.textContent = this.currentSegmentText;
          this.hasStreamedTopLevel = true;
        }
        this.scrollToBottom();
        break;

      case 'agent_call': {
        const caller = data.from || agent;
        const target = data.agent_name || agent;
        this.ensureAgentBubble(caller);
        if (this.subAgentCards[caller]) {
          this._finalizeCardTextSegment(this.subAgentCards[caller]);
        } else {
          this.finalizeCurrentTextSegment();
        }
        this.involvedAgents.add(caller);
        this.involvedAgents.add(target);
        this.setAgentActive(caller, true);
        this.setAgentActive(target, true);
        this.addActivityChip('agent-call', this.getAgentIcon(caller) + ' → ' + this.getAgentIcon(target) + ' ' + this.getAgentLabel(target));
        this.agentTokens[target] = '';
        this.agentStartTimes[target] = Date.now();
        if (this.subAgentCards[caller]) {
          this.subAgentCards[caller].cardEl.classList.add('delegating');
          this.subAgentCards[caller].cardEl.classList.remove('active-focus');
        }
        const card = this.createAgentCard(caller, target, data.message || '');
        card.callerName = caller;
        card.cardEl.classList.add('active-focus');
        this.subAgentCards[target] = card;
        if (this.callStack.length === 0) {
          this.callStack.push(caller);
        }
        this.callStack.push(target);
        this.addLogEntry(this.getAgentIcon(caller), '<strong>' + this.getAgentLabel(caller) + '</strong> → <strong>' + this.getAgentLabel(target) + '</strong> called', null, data.message ? this.truncateText(data.message, 120) : null);
        this.scrollToBottom();
        break;
      }

      case 'agent_return': {
        this.setAgentActive(agent, false);
        if (this.subAgentCards[agent]) {
          const card = this.subAgentCards[agent];
          const tokens = this.agentTokens[agent] || '';
          if (!card.finishRendered) {
            this._finalizeAgentCard(card, tokens, data.result);
          } else if (data.result && data.result.trim() && !card.resultSection.classList.contains('visible')) {
            card.resultEl.innerHTML = this.renderMarkdown(data.result);
            card.resultSection.classList.add('visible');
          }
          const elapsed = ((Date.now() - (this.agentStartTimes[agent] || Date.now())) / 1000).toFixed(1);
          card.statusEl.textContent = 'Done';
          card.statusEl.className = 'ic-status done';
          if (card.elapsedEl) card.elapsedEl.textContent = elapsed + 's';
          card.cardEl.classList.add('completed');
          card.cardEl.classList.remove('active-focus');
          const callerName = card.callerName;
          if (callerName && this.subAgentCards[callerName]) {
            this.subAgentCards[callerName].cardEl.classList.remove('delegating');
            this.subAgentCards[callerName].cardEl.classList.add('active-focus');
          }
          setTimeout(() => { card.cardEl.classList.add('collapsed'); }, 1000);
          delete this.subAgentCards[agent];
        }
        delete this.agentStartTimes[agent];
        const retIdx = this.callStack.lastIndexOf(agent);
        if (retIdx >= 0) this.callStack.splice(retIdx, 1);
        this.addLogEntry(this.getAgentIcon(agent), '<strong>' + this.getAgentLabel(agent) + '</strong> done', null, data.result ? this.truncateText(data.result, 120) : null);
        break;
      }

      case 'tool_call':
        this.ensureAgentBubble(agent);
        if (this.subAgentCards[agent]) {
          this._finalizeCardTextSegment(this.subAgentCards[agent]);
        } else {
          this.finalizeCurrentTextSegment();
        }
        this.involvedAgents.add(agent);
        this.addActivityChip('tool-call', '⚡ ' + (data.tool_name || 'tool'));
        this.createToolCard(agent, data.tool_name || 'tool', data.arguments || {});
        this.addLogEntry('⚡', '<strong>' + this.getAgentLabel(agent) + '</strong> → ' + (data.tool_name || 'tool') + '()', null, data.arguments ? JSON.stringify(data.arguments) : null);
        this.scrollToBottom();
        break;

      case 'tool_result':
        this.addLogEntry('✅', '<strong>' + this.getAgentLabel(agent) + '</strong> tool result', null, data.result ? this.truncateText(data.result, 120) : null);
        break;

      case 'finish':
        if (this.subAgentCards[agent]) {
          const card = this.subAgentCards[agent];
          const tokens = this.agentTokens[agent] || '';
          this._finalizeAgentCard(card, tokens, data.message);
          card.finishRendered = true;
          const subElapsed = ((Date.now() - (this.agentStartTimes[agent] || Date.now())) / 1000).toFixed(1);
          if (card.elapsedEl) card.elapsedEl.textContent = subElapsed + 's';
          this.setAgentActive(agent, false);
          this.scrollToBottom();
          break;
        }
        this.ensureAgentBubble(agent);
        const output = data.output || '';
        if (!this.hasStreamedTopLevel && output) {
          this.ensureTextSegment();
          this.currentTextSegment.innerHTML = this.renderMarkdown(output);
          this.currentTextSegment = null;
          this.currentSegmentText = '';
        } else {
          this.finalizeCurrentTextSegment();
        }
        Object.keys(this.subAgentCards).forEach((name) => {
          const c = this.subAgentCards[name];
          if (!c.finishRendered) {
            this._finalizeAgentCard(c, this.agentTokens[name] || '', null);
          }
          c.statusEl.textContent = 'Done';
          c.statusEl.className = 'ic-status done';
          c.cardEl.classList.add('completed', 'collapsed');
        });
        this.subAgentCards = {};
        this.callStack = [];
        if (this.currentTextSegment && !this.currentTextSegment.textContent.trim() && !this.currentTextSegment.innerHTML.trim()) {
          this.currentTextSegment.remove();
          this.currentTextSegment = null;
        }
        const mainTokens = this.agentTokens[agent] || '';
        const mainReturn = data.output || '';
        if (this.hasStreamedTopLevel && mainReturn.trim() && mainReturn.trim() !== mainTokens.trim()) {
          const returnSection = document.createElement('div');
          returnSection.className = 'ic-section ic-result-section visible main-return-section';
          const returnLabel = document.createElement('div');
          returnLabel.className = 'ic-section-label';
          returnLabel.textContent = '✦ Response';
          const returnEl = document.createElement('div');
          returnEl.className = 'ic-content ic-result';
          returnEl.innerHTML = this.renderMarkdown(mainReturn);
          returnSection.appendChild(returnLabel);
          returnSection.appendChild(returnEl);
          this.contentStreamEl.appendChild(returnSection);
        }
        this.addMessageTrail();
        this.deactivateAllAgents();
        this.setProcessing(false);
        this.addLogEntry('✅', 'Response complete', 'log-finish');
        if (data.session_id) {
          this._lastSessionId = data.session_id;
          this.currentSession = data.session_id;
          if (!this.sessions.includes(data.session_id)) {
            this.sessions.unshift(data.session_id);
            this.renderSessionList();
          }
        }
        this.scrollToBottom();
        break;

      case 'error':
        this.finalizeCurrentTextSegment();
        Object.keys(this.subAgentCards).forEach((name) => {
          const c = this.subAgentCards[name];
          if (!c.finishRendered) {
            this._finalizeAgentCard(c, this.agentTokens[name] || '', null);
          }
          c.statusEl.textContent = 'Error';
          c.statusEl.className = 'ic-status done';
          c.cardEl.classList.add('completed', 'collapsed');
        });
        this.subAgentCards = {};
        this.callStack = [];
        this.showError(data.message || 'An unknown error occurred.');
        this.deactivateAllAgents();
        this.setProcessing(false);
        this.addLogEntry('❌', data.message || 'Error', 'log-error');
        this.scrollToBottom();
        break;

      case 'thinking':
        this.addLogEntry('💭', '<strong>' + this.getAgentLabel(agent) + '</strong> thinking', null, data.content ? this.truncateText(data.content, 120) : null);
        break;

      default:
        break;
    }
  }

  async loadProviders() {
    try {
      const res = await fetch('/api/providers');
      this.providerConfig = await res.json();
    } catch (err) {
      console.error('Failed to load providers:', err);
    }
  }

  async loadAgents() {
    try {
      const res = await fetch('/api/agents');
      const data = await res.json();
      if (data.agents && typeof data.agents === 'object') {
        const merged = {};
        Object.keys(AGENT_DEFAULTS).forEach(key => {
          merged[key] = { ...AGENT_DEFAULTS[key], ...(data.agents[key] || {}) };
        });
        this.agentConfig = merged;
      }
    } catch (err) {
      console.error('Failed to load agents:', err);
    }
  }

  async loadSessions() {
    try {
      const res = await fetch('/api/sessions');
      const data = await res.json();
      this.sessions = data.sessions || [];
    } catch (err) {
      console.error('Failed to load sessions:', err);
    }
  }

  async loadSkills() {
    try {
      const res = await fetch('/api/skills');
      const data = await res.json();
      this.skillsData = data;
    } catch (err) {
      console.error('Failed to load skills:', err);
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

  buildAgentBar() {
    this.els.agentBar.innerHTML = '';
    Object.entries(this.agentConfig).forEach(([key, agent]) => {
      const badge = document.createElement('div');
      badge.className = 'agent-badge';
      badge.dataset.agent = key;
      badge.innerHTML = `<span class="badge-icon">${agent.icon || '🔆'}</span>${agent.label || agent.name || key}`;
      this.els.agentBar.appendChild(badge);
    });
  }

  getProviderModels(providerName) {
    const defaults = {
      openai: ['gpt-5.4-pro', 'gpt-5.4', 'gpt-5.4-mini', 'gpt-5.3-codex', 'gpt-5.3'],
      anthropic: ['claude-opus-4-6', 'claude-sonnet-4-6'],
      google: ['gemini-3.1-pro', 'gemini-3-flash'],
      minimax: ['MiniMax-M2.7', 'MiniMax-M2.5-highspeed', 'MiniMax-M2.5', 'MiniMax-M2.1'],
      glm: ['GLM-5', 'GLM-4.7'],
      glm_coding: ['GLM-5', 'GLM-4.7'],
      kimi: ['kimi-k2.5', 'kimi-k2.5-thinking', 'kimi-k2'],
      kimi_code: ['kimi-k2.5', 'kimi-k2.5-thinking', 'kimi-k2'],
    };
    return defaults[providerName] || [];
  }

  populateDefaultProviderSelect() {
    if (!this.els.defaultProviderSelect) return;
    const sel = this.els.defaultProviderSelect;
    sel.innerHTML = '';
    
    const providers = ['openai', 'anthropic', 'google', 'minimax', 'glm', 'kimi'];
    const availableProviders = [];
    
    providers.forEach(key => {
      const input = document.getElementById(`${key}KeyInput`);
      const apiKey = input?.value?.trim() || '';
      const config = this.providerConfig[key] || {};
      
      if (apiKey || config.enabled) {
        availableProviders.push(key);
      }
    });
    
    if (availableProviders.length === 0) {
      sel.innerHTML = '<option value="">No API keys configured</option>';
      return;
    }
    
    const displayNames = {
      openai: 'OpenAI',
      anthropic: 'Anthropic',
      google: 'Google',
      minimax: 'MiniMax',
      glm: 'GLM',
      kimi: 'Kimi'
    };
    
    availableProviders.forEach(key => {
      const opt = document.createElement('option');
      opt.value = key;
      opt.textContent = displayNames[key] || key;
      sel.appendChild(opt);
    });
    
    const config = this.providerConfig[availableProviders[0]] || {};
    if (config.enabled) {
      sel.value = availableProviders[0];
    }
  }

  updateDefaultModels() {
    if (!this.els.defaultModelSelect) return;
    const providerName = this.els.defaultProviderSelect?.value;
    const sel = this.els.defaultModelSelect;
    sel.innerHTML = '';
    
    const models = this.getProviderModels(providerName);
    models.forEach((m) => {
      const opt = document.createElement('option');
      opt.value = m;
      opt.textContent = m;
      sel.appendChild(opt);
    });
  }

  buildSidebarAgents() {
    this.els.sidebarAgents.innerHTML = '';
    Object.entries(this.agentConfig).forEach(([key, agent]) => {
      const card = document.createElement('div');
      card.className = 'sidebar-agent';
      card.dataset.agent = key;
      card.innerHTML = `
        <div class="sa-icon">${agent.icon || '🔆'}</div>
        <div class="sa-info">
          <div class="sa-name">${agent.label || agent.name || key}</div>
          <div class="sa-status">${agent.role || 'Agent'}</div>
        </div>
        <div class="sa-dot"></div>
      `;
      card.addEventListener('click', () => this.selectAgent(key));
      this.els.sidebarAgents.appendChild(card);
    });
  }

  renderSessionList() {
    const list = this.els.sessionList;
    list.innerHTML = '';
    
    if (this.sessions.length === 0) {
      list.innerHTML = '<div class="session-empty">No sessions yet</div>';
      return;
    }
    
    this.sessions.forEach((sessionId) => {
      const item = document.createElement('div');
      item.className = 'session-item';
      item.textContent = sessionId.length > 12 ? sessionId.substring(0, 12) + '...' : sessionId;
      item.addEventListener('click', () => this.loadSessionData(sessionId));
      list.appendChild(item);
    });
  }

  checkWelcomeSetup() {
    if (!this.els.welcomeSetup) return;
    
    const configured = Object.entries(this.providerConfig)
      .filter(([key, val]) => val && val.enabled).length;
    
    if (configured === 0) {
      this.els.welcomeSetup.innerHTML = '<button class="welcome-setup-btn" id="welcomeSetupBtn">Set up API keys</button>';
      document.getElementById('welcomeSetupBtn')?.addEventListener('click', () => this.openSettings());
    } else {
      this.els.welcomeSetup.innerHTML = '';
    }
  }

  selectAgent(agentKey) {
    this.currentAgent = agentKey;
    
    document.querySelectorAll('.sidebar-agent').forEach(el => {
      el.classList.toggle('active', el.dataset.agent === agentKey);
    });
    
    document.querySelectorAll('.agent-badge').forEach(el => {
      el.classList.toggle('active', el.dataset.agent === agentKey);
    });
    
    this.logActivity(`Switched to ${this.agentConfig[agentKey]?.label || agentKey}`);
  }

  createNewSession() {
    this.currentSession = null;
    
    const chatArea = this.els.chatArea;
    
    chatArea.querySelectorAll('.message').forEach(el => el.remove());
    chatArea.querySelectorAll('.agent-card').forEach(el => el.remove());
    chatArea.querySelectorAll('.tool-card').forEach(el => el.remove());
    
    let welcome = chatArea.querySelector('.welcome');
    if (!welcome) {
      welcome = document.createElement('div');
      welcome.className = 'welcome';
      welcome.id = 'welcome';
      welcome.innerHTML = `
        <div class="welcome-icon">
          <img src="/logo.svg" alt="OutObot" class="welcome-logo-img">
        </div>
        <h2>Welcome to OutObot</h2>
        <p>Your multi-agent AI system.<br>Multiple specialist agents collaborate to answer your questions.</p>
        <div class="welcome-agents">
          <div class="welcome-agent">
            <span class="agent-icon">🔆</span>
            <span>OutObot</span>
          </div>
          <div class="welcome-agent">
            <span class="agent-icon">💠</span>
            <span>Peritus</span>
          </div>
          <div class="welcome-agent">
            <span class="agent-icon">🔎</span>
            <span>Inquisitor</span>
          </div>
          <div class="welcome-agent">
            <span class="agent-icon">⚡</span>
            <span>Rimor</span>
          </div>
          <div class="welcome-agent">
            <span class="agent-icon">✔</span>
            <span>Recensor</span>
          </div>
          <div class="welcome-agent">
            <span class="agent-icon">🧠</span>
            <span>Cogitator</span>
          </div>
          <div class="welcome-agent">
            <span class="agent-icon">✨</span>
            <span>Creativus</span>
          </div>
          <div class="welcome-agent">
            <span class="agent-icon">🎭</span>
            <span>Artifex</span>
          </div>
        </div>
        <div class="welcome-setup" id="welcomeSetup"></div>
      `;
      chatArea.insertBefore(welcome, chatArea.firstChild);
      this.els.welcome = welcome;
    } else {
      welcome.classList.remove('hidden');
      this.els.welcome = welcome;
    }
    
    this.currentBubble = null;
    this.currentContentEl = null;
    this.currentActivityEl = null;
    this.contentStreamEl = null;
    this.currentTextSegment = null;
    this.currentSegmentText = '';
    this.hasStreamedTopLevel = false;
    this.agentTokens = {};
    this.subAgentCards = {};
    this.callStack = [];
    this.agentStartTimes = {};
    this.activeAgents.clear();
    this.involvedAgents.clear();
    
    this.logActivity('Started new session');
  }

  async loadSessionData(sessionId) {
    this.currentSession = sessionId;
    
    this.currentBubble = null;
    this.currentContentEl = null;
    this.currentActivityEl = null;
    this.contentStreamEl = null;
    this.currentTextSegment = null;
    this.currentSegmentText = '';
    this.hasStreamedTopLevel = false;
    this.agentTokens = {};
    this.subAgentCards = {};
    this.callStack = [];
    this.agentStartTimes = {};
    
    this.els.chatArea.querySelectorAll('.message, .agent-card, .tool-card, .interaction-card').forEach(el => el.remove());
    
    const data = await this.loadSession(sessionId);
    if (!data || !data.messages) {
      this.logActivity('Failed to load session', 'error');
      return;
    }
    
    const welcome = this.els.chatArea.querySelector('.welcome');
    if (welcome) welcome.classList.add('hidden');
    
    if (data.events && data.events.length > 0) {
      this.replaySession(data.events);
    } else {
      const existingContainer = this.els.chatArea.querySelector('.message-container');
      if (existingContainer) existingContainer.remove();
      
      const container = document.createElement('div');
      container.className = 'message-container';
      this.els.chatArea.appendChild(container);
      
      data.messages.forEach(msg => {
        const cat = msg.category;
        if (cat === 'user' || (msg.sender === 'You')) {
          this.renderUserMessage(msg.content, container);
        } else if (cat === 'top-level') {
          this.renderAgentMessage(msg.content, msg.sender, container);
        } else if (cat === 'loop-internal') {
          this.renderLoopInternalMessage(msg.caller || msg.sender, msg.sender, msg.content, container);
        } else {
          this.renderAgentMessage(msg.content, msg.sender, container);
        }
      });
    }
    
    this.scrollToBottom();
    this.logActivity(`Loaded session ${sessionId.substring(0, 8)}...`);
  }

  replaySession(events) {
    this.subAgentCards = {};
    this.callStack = [];
    this.agentTokens = {};
    this.agentStartTimes = {};
    
    const existingContainer = this.els.chatArea.querySelector('.message-container');
    if (existingContainer) existingContainer.remove();
    
    const container = document.createElement('div');
    container.className = 'message-container';
    this.els.chatArea.appendChild(container);
    
    this.ensureAgentBubble('outo');
    
    events.forEach((event, index) => {
      setTimeout(() => {
        this.handleEvent(event);
        this.scrollToBottom();
      }, index * 60);
    });
    
    this.logActivity(`Replaying ${events.length} events...`);
  }

  async sendMessage() {
    const text = this.els.messageInput.value.trim();
    if (!text || this.processing) return;
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN || this.reconnecting) {
      this.showError('Not connected to server. Please wait...');
      return;
    }

    this.hideWelcome();
    this.addUserMessage(text);

    let attachments = [];
    
    if (this.pendingAttachments.length > 0) {
      this.setProcessing(true);
      this.addLogEntry('📤', '<strong>Uploading files...</strong>');
      
      for (const file of this.pendingAttachments) {
        try {
          const formData = new FormData();
          const blob = this.dataURLtoBlob(file.data);
          const fileObj = new File([blob], file.name, { type: file.type });
          formData.append('file', fileObj);
          
          const response = await fetch('/api/upload', {
            method: 'POST',
            body: formData
          });
          
          if (response.ok) {
            const result = await response.json();
            attachments.push({
              path: result.path,
              name: result.name,
              type: result.type
            });
            this.addLogEntry('✅', `Uploaded: ${result.name}`);
          } else {
            this.addLogEntry('❌', `Failed to upload: ${file.name}`);
          }
        } catch (err) {
          this.addLogEntry('❌', `Upload error: ${file.name} - ${err.message}`);
        }
      }
    }

    const payload = {
      message: text,
      agent: this.currentAgent,
      session_id: this.currentSession,
      attachments: attachments
    };
    this.ws.send(JSON.stringify(payload));
    this.pendingAttachments = [];
    this.renderAttachmentPreview();

    this.els.messageInput.value = '';
    this.autoResizeTextarea();
    this.setProcessing(true);
    this.activeAgents.clear();
    this.involvedAgents.clear();
    this.currentBubble = null;
    this.currentContentEl = null;
    this.currentActivityEl = null;
    this.contentStreamEl = null;
    this.currentTextSegment = null;
    this.currentSegmentText = '';
    this.hasStreamedTopLevel = false;
    this.agentTokens = {};
    this.subAgentCards = {};
    this.callStack = [];
    this.agentStartTimes = {};
    this.clearActivityLog();
    this.addLogEntry('💬', '<strong>User</strong> message sent');
  }

  dataURLtoBlob(dataURL) {
    const parts = dataURL.split(',');
    const mime = parts[0].match(/:(.*?);/)[1];
    const bstr = atob(parts[1]);
    let n = bstr.length;
    const u8arr = new Uint8Array(n);
    while (n--) {
      u8arr[n] = bstr.charCodeAt(n);
    }
    return new Blob([u8arr], { type: mime });
  }

  hideWelcome() {
    if (this.els.welcome) {
      this.els.welcome.remove();
      this.els.welcome = null;
    }
  }

  addUserMessage(text) {
    const time = this.formatTime();
    const msg = document.createElement('div');
    msg.className = 'message user';
    msg.innerHTML = `
      <div class="message-avatar">👤</div>
      <div class="message-body">
        <div class="message-header">
          <span class="message-name">You</span>
          <span class="message-time">${time}</span>
        </div>
        <div class="message-content">${this.escapeHTML(text)}</div>
      </div>
    `;
    this.els.chatArea.appendChild(msg);
    this.scrollToBottom(true);
  }

  ensureAgentBubble(agentName) {
    if (this.currentBubble) return;

    const meta = this.agentMeta[agentName] || { icon: '🔆', label: agentName, color: '#6366f1' };
    const time = this.formatTime();

    const msg = document.createElement('div');
    msg.className = 'message agent';

    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.style.background = meta.color || '#6366f1';
    avatar.textContent = meta.icon || '🔆';

    const body = document.createElement('div');
    body.className = 'message-body';

    const header = document.createElement('div');
    header.className = 'message-header';
    header.innerHTML = '<span class="message-name" style="color:' + (meta.color || '#6366f1') + '">' + (meta.label || agentName) + '</span><span class="message-time">' + time + '</span>';

    const activity = document.createElement('div');
    activity.className = 'agent-activity';

    const thinking = document.createElement('div');
    thinking.className = 'thinking-indicator';
    thinking.innerHTML = '<div class="thinking-dots"><span></span><span></span><span></span></div><span>Processing...</span>';

    const contentStream = document.createElement('div');
    contentStream.className = 'content-stream';

    const textSegment = document.createElement('div');
    textSegment.className = 'text-segment message-content';
    contentStream.appendChild(textSegment);

    body.appendChild(header);
    body.appendChild(activity);
    body.appendChild(contentStream);
    body.appendChild(thinking);
    msg.appendChild(avatar);
    msg.appendChild(body);

    this.els.chatArea.appendChild(msg);
    this.currentBubble = msg;
    this.contentStreamEl = contentStream;
    this.currentTextSegment = textSegment;
    this.currentSegmentText = '';
    this.currentContentEl = textSegment;
    this.currentActivityEl = activity;
    this.involvedAgents.add(agentName);
  }

  finalizeCurrentTextSegment() {
    if (!this.currentTextSegment) return;
    if (this.currentSegmentText.trim()) {
      this.currentTextSegment.innerHTML = this.renderMarkdown(this.currentSegmentText);
    } else {
      this.currentTextSegment.remove();
    }
    this.currentTextSegment = null;
    this.currentSegmentText = '';
  }

  ensureTextSegment() {
    if (this.currentTextSegment) return;
    if (!this.contentStreamEl) return;
    const segment = document.createElement('div');
    segment.className = 'text-segment message-content';
    this.contentStreamEl.appendChild(segment);
    this.currentTextSegment = segment;
    this.currentContentEl = segment;
    this.currentSegmentText = '';
  }

  createAgentCard(caller, target, message) {
    const callerMeta = this.agentMeta[caller] || { icon: '🔆', label: caller, color: '#6366f1' };
    const targetMeta = this.agentMeta[target] || { icon: '🔆', label: target, color: '#6366f1' };

    let depth = 0;
    if (this.subAgentCards[caller]) {
      depth = (parseInt(this.subAgentCards[caller].cardEl.dataset.depth) || 0) + 1;
    }

    const card = document.createElement('div');
    card.className = 'interaction-card agent-card';
    card.style.setProperty('--card-color', targetMeta.color);
    card.dataset.depth = depth;

    const header = document.createElement('div');
    header.className = 'ic-header';
    header.innerHTML =
      '<span class="ic-toggle">▼</span>' +
      '<span class="ic-header-text">' +
        '<span style="color:' + callerMeta.color + '">' + callerMeta.icon + ' ' + this.escapeHTML(callerMeta.label) + '</span>' +
        ' <span class="ic-arrow">→</span> ' +
        '<span style="color:' + targetMeta.color + '">' + targetMeta.icon + ' ' + this.escapeHTML(targetMeta.label) + '</span>' +
      '</span>' +
      '<span class="ic-status running">Processing</span>' +
      '<span class="ic-elapsed"></span>';
    header.addEventListener('click', () => card.classList.toggle('collapsed'));

    const body = document.createElement('div');
    body.className = 'ic-body';

    const bodyInner = document.createElement('div');
    bodyInner.className = 'ic-body-inner';

    const contentStreamEl = document.createElement('div');
    contentStreamEl.className = 'ic-content-stream';

    const resultSection = document.createElement('div');
    resultSection.className = 'ic-section ic-result-section';
    const resultLabel = document.createElement('div');
    resultLabel.className = 'ic-section-label';
    resultLabel.textContent = '✦ Result';
    const resultEl = document.createElement('div');
    resultEl.className = 'ic-content ic-result';
    resultSection.appendChild(resultLabel);
    resultSection.appendChild(resultEl);

    bodyInner.appendChild(contentStreamEl);
    bodyInner.appendChild(resultSection);
    body.appendChild(bodyInner);

    card.appendChild(header);
    card.appendChild(body);

    this.contentStreamEl.appendChild(card);

    const cardObj = {
      cardEl: card,
      headerEl: header,
      statusEl: header.querySelector('.ic-status'),
      elapsedEl: header.querySelector('.ic-elapsed'),
      contentStreamEl: contentStreamEl,
      resultSection: resultSection,
      resultEl: resultEl,
      currentTextSegment: null,
      currentSegmentText: '',
      callerName: null,
      finishRendered: false
    };

    if (message) {
      const msgEl = document.createElement('div');
      msgEl.className = 'ic-delegation-msg';
      msgEl.textContent = '💬 "' + message + '"';
      bodyInner.insertBefore(msgEl, contentStreamEl);
    }

    return cardObj;
  }

  _ensureCardTextSegment(card) {
    if (card.currentTextSegment) return;
    const segment = document.createElement('div');
    segment.className = 'text-segment ic-content';
    card.contentStreamEl.appendChild(segment);
    card.currentTextSegment = segment;
    card.currentSegmentText = '';
  }

  _finalizeCardTextSegment(card) {
    if (!card.currentTextSegment) return;
    if (card.currentSegmentText.trim()) {
      card.currentTextSegment.innerHTML = this.renderMarkdown(card.currentSegmentText);
    } else {
      card.currentTextSegment.remove();
    }
    card.currentTextSegment = null;
    card.currentSegmentText = '';
  }

  _finalizeAgentCard(card, tokens, result) {
    this._finalizeCardTextSegment(card);
    if (tokens && tokens.trim()) {
      card.resultEl.innerHTML = this.renderMarkdown(tokens);
    }
    if (result && result.trim()) {
      card.resultEl.innerHTML = this.renderMarkdown(result);
      card.resultSection.classList.add('visible');
    }
  }

  createToolCard(agentName, toolName, args) {
    const meta = this.agentMeta[agentName] || { icon: '🔆', label: agentName, color: '#6366f1' };

    const card = document.createElement('div');
    card.className = 'interaction-card tool-card';

    const header = document.createElement('div');
    header.className = 'ic-header';
    header.innerHTML =
      '<span class="ic-toggle">▼</span>' +
      '<span class="ic-header-text">' +
        '<span style="color:' + meta.color + '">' + meta.icon + ' ' + this.escapeHTML(meta.label) + '</span>' +
        ' → ⚡ <strong>' + this.escapeHTML(toolName) + '</strong>()' +
      '</span>' +
      '<span class="ic-status done">Executed</span>';
    header.addEventListener('click', () => card.classList.toggle('collapsed'));

    const body = document.createElement('div');
    body.className = 'ic-body';

    const bodyInner = document.createElement('div');
    bodyInner.className = 'ic-body-inner';

    const argsEl = document.createElement('div');
    argsEl.className = 'ic-tool-args';
    argsEl.textContent = args ? JSON.stringify(args, null, 2) : '';

    bodyInner.appendChild(argsEl);
    body.appendChild(bodyInner);

    card.appendChild(header);
    card.appendChild(body);

    if (this.subAgentCards[agentName]) {
      this.subAgentCards[agentName].contentStreamEl.appendChild(card);
    } else if (this.contentStreamEl) {
      this.contentStreamEl.appendChild(card);
    }
  }

  addActivityChip(type, text) {
    const activity = this.currentActivityEl;
    if (!activity) return;
    const chip = document.createElement('div');
    chip.className = 'activity-chip ' + type;
    chip.textContent = text;
    activity.appendChild(chip);
  }

  setAgentActive(agentName, active) {
    if (active) {
      this.activeAgents.add(agentName);
    } else {
      this.activeAgents.delete(agentName);
    }
    document.querySelectorAll('.sidebar-agent').forEach(el => {
      if (el.dataset.agent === agentName) {
        el.classList.toggle('active', active);
      }
    });
  }

  deactivateAllAgents() {
    this.activeAgents.clear();
    document.querySelectorAll('.sidebar-agent').forEach(el => {
      el.classList.remove('active');
    });
  }

  setProcessing(processing) {
    this.processing = processing;
    this.updateUIState();
  }

  getAgentIcon(agentName) {
    const meta = this.agentMeta[agentName] || {};
    return meta.icon || '🔆';
  }

  getAgentLabel(agentName) {
    const meta = this.agentMeta[agentName] || {};
    return meta.label || agentName;
  }

  getAgentColor(agentName) {
    const meta = this.agentMeta[agentName] || {};
    return meta.color || '#6366f1';
  }

  formatTime() {
    return new Date().toLocaleTimeString([], { hour12: false });
  }

  truncateText(text, maxLen) {
    if (!text) return '';
    return text.length > maxLen ? text.substring(0, maxLen) + '...' : text;
  }

  escapeHTML(str) {
    if (!str) return '';
    return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#039;');
  }

  renderMarkdown(text) {
    if (typeof marked !== 'undefined') {
      return marked.parse(text || '');
    }
    return this.escapeHTML(text || '');
  }

  addMessageTrail() {
    const bubble = this.currentBubble;
    if (!bubble) return;
    const thinking = bubble.querySelector('.thinking-indicator');
    if (thinking) thinking.remove();
  }

  showError(message) {
    const errorEl = document.createElement('div');
    errorEl.className = 'error-message';
    errorEl.textContent = message;
    if (this.currentBubble) {
      const content = this.currentBubble.querySelector('.message-content');
      if (content) content.appendChild(errorEl);
    }
  }

  clearActivityLog() {
    if (!this.els.activityLog) return;
    this.els.activityLog.innerHTML = '<div class="activity-empty">No activity yet</div>';
  }

  handleStreamEvent(data, bubble, currentContent) {
    const contentEl = bubble.querySelector('.message-content');
    const activityContainer = bubble.querySelector('.activity-container');

    switch (data.type) {
      case 'token':
        currentContent += data.content || '';
        contentEl.innerHTML = marked.parse(currentContent);
        this.scrollToBottom();
        break;

      case 'tool':
      case 'agent':
        this.logActivity(data.content);
        if (activityContainer) {
          const chip = document.createElement('div');
          chip.className = 'activity-chip';
          chip.textContent = data.content.substring(0, 50);
          activityContainer.appendChild(chip);
        }
        this.scrollToBottom();
        break;

      case 'thinking':
        this.logActivity(data.content);
        break;

      case 'error':
        this.renderError(data.content, bubble);
        this.logActivity(`Error: ${data.content}`, 'error');
        break;

      case 'finish':
        if (data.session_id) {
          this._lastSessionId = data.session_id;
          this.currentSession = data.session_id;
        }
        break;
    }

    return currentContent;
  }

  createAgentBubble(agentName, container) {
    const meta = this.agentMeta[agentName] || { icon: '🔆', label: agentName, color: '#6366f1' };
    const time = this.formatTime();
    const bubble = document.createElement('div');
    bubble.className = 'message agent';
    bubble.innerHTML = `
      <div class="message-avatar" style="background:${meta.color || '#6366f1'};color:var(--bg-primary);">${meta.icon || '🔆'}</div>
      <div class="message-body">
        <div class="message-header">
          <span class="message-name" style="color:${meta.color || '#6366f1'}">${meta.label || agentName}</span>
          <span class="message-time">${time}</span>
        </div>
        <div class="agent-activity"></div>
        <div class="content-stream">
          <div class="text-segment message-content"></div>
        </div>
        <div class="thinking-indicator hidden">
          <div class="thinking-dots">
            <span></span><span></span><span></span>
          </div>
          <span>Processing...</span>
        </div>
      </div>
    `;
    container.appendChild(bubble);
    return bubble;
  }

  renderUserMessage(text, container) {
    const msg = document.createElement('div');
    msg.className = 'message user';
    msg.innerHTML = `
      <div class="message-avatar">👤</div>
      <div class="message-body">
        <div class="message-header">
          <span class="message-name">You</span>
        </div>
        <div class="message-content">${marked.parse(text)}</div>
      </div>
    `;
    container.appendChild(msg);
    this.scrollToBottom();
  }

  renderAgentMessage(content, agentName, container) {
    const bubble = this.createAgentBubble(agentName, container);
    const contentStreamEl = bubble.querySelector('.content-stream');
    if (contentStreamEl) {
      const returnSection = document.createElement('div');
      returnSection.className = 'ic-section ic-result-section visible main-return-section';
      returnSection.innerHTML =
        '<div class="ic-section-label">✦ Response</div>' +
        '<div class="ic-content ic-result">' + marked.parse(content) + '</div>';
      contentStreamEl.appendChild(returnSection);
    }
    this.scrollToBottom();
  }

  renderLoopInternalMessage(caller, target, content, container) {
    const callerMeta = this.agentMeta[caller] || { icon: '🔆', label: caller, color: '#6366f1' };
    const targetMeta = this.agentMeta[target] || { icon: '🔆', label: target, color: '#6366f1' };

    const card = document.createElement('div');
    card.className = 'interaction-card agent-card completed collapsed';
    card.style.setProperty('--card-color', targetMeta.color);
    card.dataset.depth = 0;

    const header = document.createElement('div');
    header.className = 'ic-header';
    header.innerHTML =
      '<span class="ic-toggle">▼</span>' +
      '<span class="ic-header-text">' +
        '<span style="color:' + callerMeta.color + '">' + callerMeta.icon + ' ' + this.escapeHTML(callerMeta.label) + '</span>' +
        ' <span class="ic-arrow">→</span> ' +
        '<span style="color:' + targetMeta.color + '">' + targetMeta.icon + ' ' + this.escapeHTML(targetMeta.label) + '</span>' +
      '</span>' +
      '<span class="ic-status done">Done</span>' +
      '<span class="ic-elapsed"></span>';
    header.addEventListener('click', () => card.classList.toggle('collapsed'));

    const body = document.createElement('div');
    body.className = 'ic-body';

    const bodyInner = document.createElement('div');
    bodyInner.className = 'ic-body-inner';

    const contentStreamEl = document.createElement('div');
    contentStreamEl.className = 'ic-content-stream';

    const resultSection = document.createElement('div');
    resultSection.className = 'ic-section ic-result-section visible';
    resultSection.innerHTML =
      '<div class="ic-section-label">✦ Result</div>' +
      '<div class="ic-content ic-result">' + marked.parse(content) + '</div>';

    bodyInner.appendChild(contentStreamEl);
    bodyInner.appendChild(resultSection);
    body.appendChild(bodyInner);
    card.appendChild(header);
    card.appendChild(body);
    container.appendChild(card);
    this.scrollToBottom();
  }

  renderError(errorText, bubble) {
    const contentEl = bubble.querySelector('.message-content');
    contentEl.innerHTML += `<div class="error-message">${errorText}</div>`;
  }

  showThinking(bubble) {
    const indicator = bubble.querySelector('.thinking-indicator');
    if (indicator) indicator.classList.remove('hidden');
  }

  hideThinking(bubble) {
    const indicator = bubble.querySelector('.thinking-indicator');
    if (indicator) indicator.classList.add('hidden');
  }

  async openSettings() {
    this.els.settingsModal.classList.remove('hidden');
    this.els.saveFeedback.textContent = '';
    this.els.saveFeedback.className = 'save-feedback';

    Object.entries(this.providerConfig).forEach(([key, val]) => {
      const input = document.getElementById(`${key}KeyInput`);
      const status = document.getElementById(`${key}Status`);
      if (input && val) input.value = val.api_key || '';
      if (status) this.setKeyStatus(status, val.enabled);
    });

    this.populateDefaultProviderSelect();
    this.updateDefaultModels();
    
    const providers = ['openai', 'anthropic', 'google', 'minimax', 'glm', 'kimi'];
    providers.forEach(key => {
      const input = document.getElementById(`${key}KeyInput`);
      if (input) {
        input.oninput = () => {
          this.populateDefaultProviderSelect();
          this.updateDefaultModels();
        };
      }
    });
  }

  closeSettings() {
    this.els.settingsModal.classList.add('hidden');
  }

  setKeyStatus(el, configured) {
    if (configured) {
      el.textContent = 'Configured';
      el.className = 'key-status configured';
    } else {
      el.textContent = 'Not set';
      el.className = 'key-status unconfigured';
    }
  }

  async saveSettings() {
    this.els.settingsSave.disabled = true;
    this.els.saveFeedback.textContent = 'Saving...';
    this.els.saveFeedback.className = 'save-feedback';

    const config = {};
    
    const providers = ['openai', 'anthropic', 'google', 'minimax', 'glm', 'kimi'];
    providers.forEach(key => {
      const input = document.getElementById(`${key}KeyInput`);
      const apiKey = input?.value?.trim() || '';
      
      config[key] = {
        enabled: apiKey.length > 0,
        api_key: apiKey,
        model: ''
      };
    });

    const defaultProvider = this.els.defaultProviderSelect?.value || '';
    const defaultModel = this.els.defaultModelSelect?.value || '';
    
    if (defaultProvider && config[defaultProvider]) {
      config[defaultProvider].model = defaultModel;
    }

    try {
      const res = await fetch('/api/providers', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config)
      });

      if (!res.ok) throw new Error('Failed to save');

      await this.loadProviders();
      
      this.els.saveFeedback.textContent = 'Saved';
      this.els.saveFeedback.className = 'save-feedback success';
      
      setTimeout(() => {
        this.els.saveFeedback.textContent = '';
        this.els.saveFeedback.className = 'save-feedback';
      }, 3000);
      
      this.closeSettings();
      this.checkWelcomeSetup();
      this.logActivity('Settings saved');
      
    } catch (err) {
      console.error('Save error:', err);
      this.els.saveFeedback.textContent = 'Error saving';
      this.els.saveFeedback.className = 'save-feedback error';
    } finally {
      this.els.settingsSave.disabled = false;
    }
  }

  async openSkills() {
    this.els.skillsModal?.classList.remove('hidden');
    this.renderSkillsList();
  }

  closeSkills() {
    this.els.skillsModal?.classList.add('hidden');
  }

  async syncSkills() {
    const btn = document.getElementById('syncSkillsBtn');
    if (btn) {
      btn.disabled = true;
      btn.textContent = 'Syncing...';
    }
    
    try {
      const res = await fetch('/api/skills/sync', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      
      if (!res.ok) throw new Error('Failed to sync');
      
      await this.loadSkills();
      this.renderSkillsList();
      this.logActivity('Skills synced');
    } catch (err) {
      console.error('Sync error:', err);
      this.logActivity('Failed to sync skills', 'error');
    } finally {
      if (btn) {
        btn.disabled = false;
        btn.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21.5 2v6h-6M2.5 22v-6h6M2 11.5a10 10 0 0 1 18.8-4.3M22 12.5a10 10 0 0 1-18.8 4.3"/></svg> Sync Skills`;
      }
    }
  }

  renderSkillsList() {
    const list = document.getElementById('skillsList');
    if (!list) return;
    
    const skills = this.skillsData?.skills || [];
    
    if (skills.length === 0) {
      list.innerHTML = '<div class="skills-empty">No skills installed</div>';
      return;
    }
    
    list.innerHTML = '';
    skills.forEach(skill => {
      const item = document.createElement('div');
      item.className = 'skill-item';
      item.innerHTML = `
        <div class="skill-info">
          <div class="skill-name">${skill.name || 'Unnamed'}</div>
          <div class="skill-desc">${skill.description || ''}</div>
        </div>
      `;
      list.appendChild(item);
    });
  }

  async installSkill() {
    const input = document.getElementById('skillInstallInput');
    const skillName = input?.value?.trim();
    
    if (!skillName) return;
    
    const btn = document.getElementById('installSkillBtn');
    if (btn) {
      btn.disabled = true;
      btn.textContent = 'Installing...';
    }
    
    try {
      const res = await fetch('/api/skills/install', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: skillName })
      });
      
      if (!res.ok) throw new Error('Failed to install');
      
      await this.loadSkills();
      this.renderSkillsList();
      if (input) input.value = '';
      this.logActivity(`Installed skill: ${skillName}`);
    } catch (err) {
      console.error('Install error:', err);
      this.logActivity(`Failed to install: ${skillName}`, 'error');
    } finally {
      if (btn) {
        btn.disabled = false;
        btn.textContent = 'Install';
      }
    }
  }

  toggleSidebar() {
    this.els.sidebar.classList.toggle('collapsed');
  }

  updateConnectionStatus(state) {
    const el = this.els.connectionStatus;
    el.className = 'connection-status ' + state;
    const textEl = el.querySelector('.status-text');
    const labels = {
      connecting: 'Connecting...',
      connected: 'Connected',
      disconnected: 'Disconnected'
    };
    textEl.textContent = labels[state] || state;
  }

  updateUIState() {
    this.els.sendBtn.disabled = this.processing;
    this.els.messageInput.disabled = this.processing;
    this.els.attachBtn.disabled = this.processing;
  }

  logActivity(message, type = 'info') {
    const log = this.els.activityLog;
    const empty = log.querySelector('.activity-empty');
    if (empty) empty.remove();

    const entry = document.createElement('div');
    entry.className = 'log-entry';
    if (type === 'error') entry.classList.add('log-error');

    const time = new Date().toLocaleTimeString([], { hour12: false });
    
    entry.innerHTML = `
      <div class="log-main">
        <span class="log-time">${time}</span>
        <span class="log-text">${message}</span>
      </div>
    `;
    
    log.appendChild(entry);
    log.scrollTop = log.scrollHeight;
  }

  addLogEntry(icon, message, type, details) {
    const fullMessage = icon ? `${icon} ${message}` : message;
    this.logActivity(fullMessage, type);
  }

  scrollToBottom(force = false) {
    if (force || !this.userScrolledUp) {
      this.els.chatArea.scrollTop = this.els.chatArea.scrollHeight;
    }
    this.els.scrollBtn.classList.add('hidden');
  }

  autoResizeTextarea() {
    this.els.messageInput.style.height = 'auto';
    this.els.messageInput.style.height = Math.min(this.els.messageInput.scrollHeight, 200) + 'px';
  }

  handleFileSelect(e) {
    const files = Array.from(e.target.files);
    if (!files.length) return;

    files.forEach(file => {
      const reader = new FileReader();
      reader.onload = (event) => {
        this.pendingAttachments.push({
          name: file.name,
          type: file.type,
          data: event.target.result
        });
        this.renderAttachmentPreview();
      };
      reader.readAsDataURL(file);
    });

    e.target.value = '';
  }

  renderAttachmentPreview() {
    const preview = this.els.attachmentPreview;
    preview.innerHTML = '';
    
    if (this.pendingAttachments.length === 0) {
      preview.style.display = 'none';
      return;
    }

    preview.style.display = 'flex';
    
    this.pendingAttachments.forEach((file, idx) => {
      const item = document.createElement('div');
      item.className = 'attach-item';
      item.innerHTML = `
        <span class="attach-icon"></span>
        <span class="attach-name">${file.name}</span>
        <button class="attach-remove" data-index="${idx}"></button>
      `;
      item.querySelector('.attach-remove').addEventListener('click', (e) => {
        const index = parseInt(e.target.dataset.index);
        this.pendingAttachments.splice(index, 1);
        this.renderAttachmentPreview();
      });
      preview.appendChild(item);
    });
  }

  clearAttachments() {
    this.pendingAttachments = [];
    this.els.attachmentPreview.innerHTML = '';
    this.els.attachmentPreview.style.display = 'none';
  }
}

document.addEventListener('DOMContentLoaded', () => {
  window.chat = new OutObotChat();
});
