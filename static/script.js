/**
 * OutObot Chat - Main Entry Point
 * Wires together UI, Events, Replay, and Session modules
 */

const PROVIDER_KEYS = [
  { name: 'openai', inputId: 'openaiKeyInput', statusId: 'openaiStatus', key: 'openai' },
  { name: 'anthropic', inputId: 'anthropicKeyInput', statusId: 'anthropicStatus', key: 'anthropic' },
  { name: 'google', inputId: 'googleKeyInput', statusId: 'googleStatus', key: 'google' },
  { name: 'minimax', inputId: 'minimaxKeyInput', statusId: 'minimaxStatus', key: 'minimax' },
  { name: 'glm', inputId: 'glmKeyInput', statusId: 'glmStatus', key: 'glm' },
  { name: 'glm_coding', inputId: 'glmCodingKeyInput', statusId: 'glmCodingStatus', key: 'glm_coding' },
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
    this.discordConfig = {};
    this.agentConfig = AGENT_DEFAULTS;
    this.currentAgent = 'outo';
    this.currentSession = null;
    this.sessions = [];
    this.processing = false;
    this._sentAgent = null;

    this.activeAgents = new Set();
    this.involvedAgents = new Set();
    this.pendingAgentCalls = new Set();
    this.subAgentCards = {};
    this.callStack = [];
    this.agentTokens = {};
    this.pendingTokens = {};
    this.agentStartTimes = {};
    this.agentMeta = AGENT_DEFAULTS;

    if (window.innerWidth <= 960) {
      this.els.sidebar.classList.add('collapsed');
    }

    if (typeof marked !== 'undefined') {
      marked.use({ breaks: true, gfm: true });
    }

    this.initModules();
    this.bindEvents();
    this.init();
  }

  initModules() {
    this.ui = new UIRenderer(this);
    this.eventHandlers = new EventHandlers(this, this.ui);
    this.sessionManager = new SessionManager(this);
    this.sessionReplay = new SessionReplay(this, this.ui, this.eventHandlers);
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

    PROVIDER_KEYS.forEach(({ inputId }) => {
      const input = document.getElementById(inputId);
      if (input) {
        input.addEventListener('input', () => {
          this.populateDefaultProviderSelect();
          this.updateDefaultModels();
        });
      }
    });

    document.getElementById('newSessionBtn')?.addEventListener('click', () => this.createNewSession());
  }

  async init() {
    this.updateConnectionStatus('connecting');
    
    try {
      await Promise.all([
        this.loadProviders(),
        this.loadAgents(),
        this.sessionManager.loadSessions(),
        this.loadSkills(),
        this.loadDiscordConfig()
      ]);
      
      this.buildAgentBar();
      this.buildSidebarAgents();
      this.sessionManager.renderSessionList();
      this.checkWelcomeSetup();
      this.updateProviderStatuses();
      this.connectWebSocket();
      this.restoreActiveExecution();
    } catch (error) {
      console.error('Init error:', error);
      this.updateConnectionStatus('disconnected');
    }
  }

  async restoreActiveExecution() {
    try {
      const res = await fetch('/api/executions/active');
      const executions = await res.json();
      if (!executions || executions.length === 0) return;

      const active = executions[0];
      if (active.status !== 'running') return;

      this.currentSession = active.session_id;
      this.hideWelcome();
      this.setProcessing(true);
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify({
          type: 'reconnect',
          session_id: active.session_id
        }));
        this.logActivity('Restored active session');
      }
    } catch (err) {
      console.error('Failed to restore execution:', err);
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
      this.restoreActiveExecution();
    };

    this.ws.onclose = () => {
      this.updateConnectionStatus('disconnected');
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
        if (event.type === 'execution_state') {
          this.handleExecutionStateRestore(event.data);
          return;
        }
        if (event.type === 'execution_started') {
          return;
        }
        this.eventHandlers.handleEvent(event);
      } catch (err) {
        console.error('Failed to parse event:', err);
      }
    };
  }

  handleExecutionStateRestore(stateData) {
    if (stateData && stateData.session_id) {
      this.currentSession = stateData.session_id;
    }
    this.setProcessing(true);
    this.subAgentCards = {};
    this.callStack = [];
    this.agentTokens = {};
    this.pendingTokens = {};
    this.pendingAgentCalls.clear();
    this.agentStartTimes = {};
    this.hasStreamedTopLevel = false;
    this.currentBubble = null;
    this.currentFinishEl = null;
    this.contentStreamEl = null;
    this.currentTextSegment = null;
    this.currentSegmentText = '';
    this.activeAgents.clear();
    this.involvedAgents.clear();
    this.logActivity('Reconnected to running execution');
  }

  loadSessionData(sessionId) {
    this.sessionReplay.loadSessionData(sessionId);
  }

  async loadProviders() {
    try {
      const res = await fetch('/api/providers');
      this.providerConfig = await res.json();
    } catch (err) {
      console.error('Failed to load providers:', err);
    }
  }

  async loadDiscordConfig() {
    try {
      const res = await fetch('/api/discord');
      this.discordConfig = await res.json();
    } catch (err) {
      console.error('Failed to load Discord config:', err);
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
        this.agentMeta = merged;
      }
    } catch (err) {
      console.error('Failed to load agents:', err);
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

  loadSession(sessionId) {
    return this.sessionManager.loadSession(sessionId);
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
    
    const providers = ['openai', 'anthropic', 'google', 'minimax', 'glm', 'glm_coding', 'kimi'];
    const availableProviders = [];
    
    providers.forEach(key => {
      const input = document.getElementById(`${key}KeyInput`);
      const apiKey = input?.value?.trim() || '';
      const config = this.providerConfig[key] || {};
      
      if (apiKey || config.api_key) {
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
      glm_coding: 'GLM Coding Plan',
      kimi: 'Kimi'
    };
    
    availableProviders.forEach(key => {
      const opt = document.createElement('option');
      opt.value = key;
      opt.textContent = displayNames[key] || key;
      sel.appendChild(opt);
    });
    
    const defaultProvider = this.providerConfig.default_provider;
    if (defaultProvider && availableProviders.includes(defaultProvider)) {
      sel.value = defaultProvider;
    } else {
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
    
    const config = this.providerConfig[providerName];
    if (config && config.model) {
      sel.value = config.model;
    }
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
    this.sessionManager.renderSessionList();
  }

  checkWelcomeSetup() {
    if (!this.els.welcomeSetup) return;
    
    const providerKeys = ['openai', 'anthropic', 'google', 'minimax', 'glm', 'glm_coding', 'kimi'];
    const configured = providerKeys.filter(key => {
      const val = this.providerConfig[key];
      return val && (val.api_key || val.enabled);
    }).length;
    
    if (configured === 0) {
      this.els.welcomeSetup.innerHTML = '<button class="welcome-setup-btn" id="welcomeSetupBtn">Set up API keys</button>';
      document.getElementById('welcomeSetupBtn')?.addEventListener('click', () => this.openSettings());
    } else {
      this.els.welcomeSetup.innerHTML = '';
    }
  }

  updateProviderStatuses() {
    PROVIDER_KEYS.forEach(({ name, statusId }) => {
      const statusEl = document.getElementById(statusId);
      if (!statusEl) return;
      const config = this.providerConfig[name];
      if (config && (config.api_key || config.enabled)) {
        statusEl.textContent = '✓';
        statusEl.className = 'key-status active';
      } else {
        statusEl.textContent = '';
        statusEl.className = 'key-status';
      }
    });
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
    this.messageContainer = null;
    
    const chatArea = this.els.chatArea;
    
    chatArea.querySelectorAll('.message').forEach(el => el.remove());
    chatArea.querySelectorAll('.agent-card').forEach(el => el.remove());
    chatArea.querySelectorAll('.tool-card').forEach(el => el.remove());
    chatArea.querySelectorAll('.message-container').forEach(el => el.remove());
    
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
    this.currentFinishEl = null;
    this.contentStreamEl = null;
    this.currentTextSegment = null;
    this.currentSegmentText = '';
    this.hasStreamedTopLevel = false;
    this.agentTokens = {};
    this.subAgentCards = {};
    this.callStack = [];
    this.pendingTokens = {};
    this.pendingAgentCalls.clear();
    this.agentStartTimes = {};
    this.activeAgents.clear();
    this.involvedAgents.clear();
    
    this.logActivity('Started new session');
  }

  async sendMessage() {
    const text = this.els.messageInput.value.trim();
    if (!text || this.processing) return;
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN || this.reconnecting) {
      this.showError('Not connected to server. Please wait...');
      return;
    }

    this.hideWelcome();
    this.ui.addUserMessage(text);

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
    this._sentAgent = this.currentAgent;
    this.activeAgents.clear();
    this.involvedAgents.clear();
    this.currentBubble = null;
    this.currentFinishEl = null;
    this.activityIndicator = null;
    this.agentTokens = {};
    this.subAgentCards = {};
    this.callStack = [];
    this.pendingTokens = {};
    this.pendingAgentCalls.clear();
    this.agentStartTimes = {};
    this.clearActivityLog();
    this.eventHandlers.reset();
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

  ensureAgentBubble(agentName) {
    if (this.currentBubble) return this.currentBubble;

    const bubbleData = this.ui.createAgentBubbleElement(agentName);
    this.els.chatArea.appendChild(bubbleData.element);
    this.currentBubble = bubbleData.element;
    this.activityIndicator = bubbleData.activityIndicator;
    this.currentFinishEl = bubbleData.finishContent;
    this.involvedAgents.add(agentName);
    return this.currentBubble;
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

  addActivityChip(type, text) {
    const activity = this.currentActivityEl;
    if (!activity) return;
    const existing = activity.querySelector('.activity-chip.' + type);
    if (existing) {
      if (text === null || text === '') {
        existing.remove();
      } else {
        existing.textContent = text;
      }
      return;
    }
    if (text === null || text === '') return;
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

  updateUIState() {
    const isConnected = this.ws && this.ws.readyState === WebSocket.OPEN;
    this.els.sendBtn.disabled = this.processing || !isConnected;
    this.els.messageInput.disabled = this.processing;
  }

  scrollToBottom(force = false) {
    if (force || !this.userScrolledUp) {
      this.els.chatArea.scrollTop = this.els.chatArea.scrollHeight;
    }
  }

  autoResizeTextarea() {
    const textarea = this.els.messageInput;
    textarea.style.height = 'auto';
    textarea.style.height = Math.min(textarea.scrollHeight, 200) + 'px';
  }

  handleFileSelect(e) {
    const files = e.target.files;
    if (!files.length) return;

    for (const file of files) {
      const reader = new FileReader();
      reader.onload = (ev) => {
        this.pendingAttachments.push({
          name: file.name,
          type: file.type,
          data: ev.target.result
        });
        this.renderAttachmentPreview();
      };
      reader.readAsDataURL(file);
    }
    e.target.value = '';
  }

  renderAttachmentPreview() {
    const preview = this.els.attachmentPreview;
    if (!preview) return;
    
    preview.innerHTML = '';
    if (this.pendingAttachments.length === 0) {
      preview.classList.add('hidden');
      return;
    }
    
    preview.classList.remove('hidden');
    this.pendingAttachments.forEach((att, idx) => {
      const item = document.createElement('div');
      item.className = 'attachment-item';
      item.innerHTML = `<span class="attachment-name">${att.name}</span><button class="attachment-remove" data-idx="${idx}">×</button>`;
      item.querySelector('.attachment-remove').addEventListener('click', () => {
        this.pendingAttachments.splice(idx, 1);
        this.renderAttachmentPreview();
      });
      preview.appendChild(item);
    });
  }

  clearActivityLog() {
    if (!this.els.activityLog) return;
    this.els.activityLog.innerHTML = '<div class="activity-empty">No activity yet</div>';
  }

  logActivity(text, type = '') {
    if (!this.els.activityLog) return;
    const entry = document.createElement('div');
    entry.className = 'activity-entry ' + type;
    entry.textContent = text;
    const empty = this.els.activityLog.querySelector('.activity-empty');
    if (empty) empty.remove();
    this.els.activityLog.appendChild(entry);
    this.els.activityLog.scrollTop = this.els.activityLog.scrollHeight;
  }

  addLogEntry(icon, text, type = null, detail = null) {
    if (!this.els.activityLog) return;
    const entry = document.createElement('div');
    entry.className = 'activity-entry ' + (type || '');
    let html = `<span class="log-icon">${icon}</span><span class="log-text">${text}</span>`;
    if (detail) {
      html += `<span class="log-detail">${detail}</span>`;
    }
    entry.innerHTML = html;
    const empty = this.els.activityLog.querySelector('.activity-empty');
    if (empty) empty.remove();
    this.els.activityLog.appendChild(entry);
    this.els.activityLog.scrollTop = this.els.activityLog.scrollHeight;
  }

  updateConnectionStatus(status) {
    const el = this.els.connectionStatus;
    if (!el) return;
    el.className = 'connection-status ' + status;
    const text = { connecting: 'Connecting...', connected: 'Connected', disconnected: 'Disconnected' };
    el.textContent = text[status] || status;
  }

  openSettings() {
    this.syncSettingsInputs();
    this.populateDefaultProviderSelect();
    this.updateDefaultModels();
    this.els.settingsModal.classList.remove('hidden');
  }

  syncSettingsInputs() {
    PROVIDER_KEYS.forEach(({ name, inputId }) => {
      const input = document.getElementById(inputId);
      if (!input) return;
      const config = this.providerConfig[name];
      if (config && config.api_key) {
        input.value = config.api_key;
      }
    });
    const defaultProvider = this.providerConfig.default_provider;
    if (defaultProvider && this.els.defaultProviderSelect) {
      this.els.defaultProviderSelect.value = defaultProvider;
    }
    const defaultModel = this.providerConfig.default_model;
    if (defaultModel && this.els.defaultModelSelect) {
      this.els.defaultModelSelect.value = defaultModel;
    }

    const discordToken = this.discordConfig.token;
    const discordTokenInput = document.getElementById('discordTokenInput');
    if (discordTokenInput) {
      discordTokenInput.value = discordToken || '';
    }
    const discordEnabled = document.getElementById('discordEnabled');
    if (discordEnabled) {
      discordEnabled.value = String(this.discordConfig.enabled || false);
    }
    const discordStatus = document.getElementById('discordStatus');
    if (discordStatus) {
      if (this.discordConfig.enabled && this.discordConfig.token) {
        discordStatus.textContent = '✓';
        discordStatus.className = 'key-status active';
      } else {
        discordStatus.textContent = '';
        discordStatus.className = 'key-status';
      }
    }
  }

  closeSettings() {
    this.els.settingsModal.classList.add('hidden');
  }

  async openSkills() {
    if (this.els.skillsModal) {
      await this.loadSkills();
      this.renderSkillsList();
      this.els.skillsModal.classList.remove('hidden');
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

  closeSkills() {
    if (this.els.skillsModal) {
      this.els.skillsModal.classList.add('hidden');
    }
  }

  async saveSettings() {
    const providerKeys = ['openai', 'anthropic', 'google', 'minimax', 'glm', 'glm_coding', 'kimi'];
    
    const newConfig = { ...this.providerConfig };
    
    providerKeys.forEach(key => {
      const input = document.getElementById(`${key}KeyInput`);
      const apiKey = input?.value?.trim() || '';
      if (!newConfig[key]) {
        newConfig[key] = { enabled: false, api_key: '', model: '' };
      }
      if (apiKey) {
        newConfig[key].api_key = apiKey;
        newConfig[key].enabled = true;
      }
    });

    const defaultProvider = this.els.defaultProviderSelect?.value;
    const defaultModel = this.els.defaultModelSelect?.value;
    if (defaultProvider) newConfig.default_provider = defaultProvider;
    if (defaultModel) newConfig.default_model = defaultModel;

    try {
      const res = await fetch('/api/providers', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newConfig)
      });

      if (res.ok) {
        this.showSaveFeedback('Settings saved!');
        await this.loadProviders();
        this.checkWelcomeSetup();
        this.updateProviderStatuses();
        this.closeSettings();
      } else {
        this.showSaveFeedback('Failed to save settings', true);
      }
    } catch (err) {
      this.showSaveFeedback('Error: ' + err.message, true);
    }

    const discordToken = document.getElementById('discordTokenInput')?.value?.trim() || '';
    const discordEnabled = document.getElementById('discordEnabled')?.value === 'true';

    try {
      await fetch('/api/discord', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          enabled: discordEnabled,
          token: discordToken
        })
      });
      await this.loadDiscordConfig();
    } catch (err) {
      console.error('Failed to save Discord config:', err);
    }
  }

  showSaveFeedback(message, isError = false) {
    const el = this.els.saveFeedback;
    if (!el) return;
    el.textContent = message;
    el.className = 'save-feedback ' + (isError ? 'error' : 'success');
    el.classList.remove('hidden');
    setTimeout(() => el.classList.add('hidden'), 3000);
  }

  toggleSidebar() {
    this.els.sidebar.classList.toggle('collapsed');
  }

  async syncSkills() {
    try {
      const res = await fetch('/api/skills/sync', { method: 'POST' });
      if (res.ok) {
        await this.loadSkills();
        this.showSaveFeedback('Skills synced!');
      }
    } catch (err) {
      this.showSaveFeedback('Failed to sync skills', true);
    }
  }

  async installSkill() {
    const input = document.getElementById('skillUrlInput');
    if (!input || !input.value.trim()) return;
    
    try {
      const res = await fetch('/api/skills/install', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: input.value.trim() })
      });
      
      if (res.ok) {
        await this.loadSkills();
        this.showSaveFeedback('Skill installed!');
        input.value = '';
      } else {
        this.showSaveFeedback('Failed to install skill', true);
      }
    } catch (err) {
      this.showSaveFeedback('Error: ' + err.message, true);
    }
  }
}

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
  window.outobot = new OutObotChat();
});
