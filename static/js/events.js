/**
 * Event Handlers for OutObot
 * Contains handleEvent and all event type handlers
 */

class EventHandlers {
  constructor(chat, ui) {
    this.chat = chat;
    this.ui = ui;
    this.scrollThrottle = null;
  }

  // Main event dispatcher
  handleEvent(event) {
    const { type, agent_name, data, call_id } = event;
    const agent = agent_name || 'outo';
    const cid = call_id || agent;

    switch (type) {
      case 'token':
        this.handleToken(agent, cid, data);
        break;
      case 'agent_call':
        this.handleAgentCall(agent, cid, data);
        break;
      case 'agent_return':
        this.handleAgentReturn(agent, cid, data);
        break;
      case 'tool_call':
        this.handleToolCall(agent, cid, data);
        break;
      case 'tool_result':
        this.handleToolResult(agent, cid, data);
        break;
      case 'thinking':
        this.handleThinking(agent, cid, data);
        break;
      case 'error':
        this.handleError(agent, cid, data);
        break;
      case 'finish':
        this.handleFinish(agent, cid, data);
        break;
      case 'forward':
        this.handleForward(agent, data);
        break;
      default:
        break;
    }
  }

  handleToken(agent, cid, data) {
    this.chat.agentTokens[cid] = (this.chat.agentTokens[cid] || '') + (data.content || '');
    
    if (this.chat.subAgentCards[cid]) {
      const card = this.chat.subAgentCards[cid];
      this.ensureCardTextSegment(card);
      card.currentSegmentText += data.content || '';
      card.currentTextSegment.textContent = card.currentSegmentText;
      card.contentStreamEl.scrollTop = card.contentStreamEl.scrollHeight;
    } else if (this.chat.pendingAgentCalls.has(cid)) {
      this.chat.pendingTokens[cid] = (this.chat.pendingTokens[cid] || '') + (data.content || '');
    } else {
      this.chat.ensureAgentBubble(agent);
      this.ensureTextSegment();
      this.chat.currentSegmentText += data.content || '';
      this.chat.currentTextSegment.textContent = this.chat.currentSegmentText;
      this.chat.hasStreamedTopLevel = true;
    }
    
    if (!this.scrollThrottle) {
      this.scrollThrottle = setTimeout(() => {
        this.chat.scrollToBottom();
        this.scrollThrottle = null;
      }, 50);
    }
  }

  handleAgentCall(agent, cid, data) {
    const caller = data.from || agent;
    const target = data.agent_name || agent;
    const parentCallId = this.chat.callStack.length > 0
      ? this.chat.callStack[this.chat.callStack.length - 1]
      : null;

    this.chat.ensureAgentBubble(caller);
    
    if (parentCallId && this.chat.subAgentCards[parentCallId]) {
      this._finalizeCardTextSegment(this.chat.subAgentCards[parentCallId]);
    } else {
      this.finalizeCurrentTextSegment();
    }
    
    this.chat.involvedAgents.add(caller);
    this.chat.involvedAgents.add(target);
    this.chat.setAgentActive(caller, true);
    this.chat.setAgentActive(target, true);
    this.chat.addActivityChip('agent-call', this.ui.getAgentIcon(caller) + ' → ' + this.ui.getAgentIcon(target) + ' ' + this.ui.getAgentLabel(target));
    this.chat.agentTokens[cid] = '';
    this.chat.agentStartTimes[cid] = Date.now();
    this.chat.pendingAgentCalls.add(cid);
    
    if (parentCallId && this.chat.subAgentCards[parentCallId]) {
      this.chat.subAgentCards[parentCallId].cardEl.classList.add('delegating');
      this.chat.subAgentCards[parentCallId].cardEl.classList.remove('active-focus');
    }
    
    const card = this.ui.createDelegationCard(caller, target, data.message || '');
    card.callerName = caller;
    card.callId = cid;
    card.parentCallId = parentCallId;
    card.cardEl.classList.add('active-focus');
    this.chat.subAgentCards[cid] = card;
    this._flushPendingTokens(cid);
    this.chat.pendingAgentCalls.delete(cid);
    
    this.chat.callStack.push(cid);
    
    this.chat.addLogEntry(this.ui.getAgentIcon(caller), '<strong>' + this.ui.getAgentLabel(caller) + '</strong> → <strong>' + this.ui.getAgentLabel(target) + '</strong> called', null, data.message ? this.ui.truncateText(data.message, 120) : null);
    this.chat.scrollToBottom();
  }

  handleAgentReturn(agent, cid, data) {
    const agentName = agent;
    this.chat.setAgentActive(agentName, false);
    delete this.chat.pendingTokens[cid];
    this.chat.pendingAgentCalls.delete(cid);
    
    if (this.chat.subAgentCards[cid]) {
      const card = this.chat.subAgentCards[cid];
      const tokens = this.chat.agentTokens[cid] || '';
      if (!card.finishRendered) {
        this._finalizeAgentCard(card, tokens, data.result);
      } else if (data.result && data.result.trim() && !card.resultSection.classList.contains('visible')) {
        card.resultEl.innerHTML = this.ui.renderMarkdown(data.result);
        card.resultSection.classList.add('visible');
      }
      const elapsed = ((Date.now() - (this.chat.agentStartTimes[cid] || Date.now())) / 1000).toFixed(1);
      card.statusEl.textContent = 'Done';
      card.statusEl.className = 'ic-status done';
      if (card.elapsedEl) card.elapsedEl.textContent = elapsed + 's';
      card.cardEl.classList.add('completed');
      card.cardEl.classList.remove('active-focus');
      const parentCallId = card.parentCallId;
      if (parentCallId && this.chat.subAgentCards[parentCallId]) {
        this.chat.subAgentCards[parentCallId].cardEl.classList.remove('delegating');
        this.chat.subAgentCards[parentCallId].cardEl.classList.add('active-focus');
      }
      setTimeout(() => { card.cardEl.classList.add('collapsed'); }, 1000);
      delete this.chat.subAgentCards[cid];
    }
    
    delete this.chat.agentStartTimes[cid];
    const retIdx = this.chat.callStack.lastIndexOf(cid);
    if (retIdx >= 0) this.chat.callStack.splice(retIdx, 1);
    this.chat.addLogEntry(this.ui.getAgentIcon(agentName), '<strong>' + this.ui.getAgentLabel(agentName) + '</strong> done', null, data.result ? this.ui.truncateText(data.result, 120) : null);
  }

  handleToolCall(agent, cid, data) {
    this.chat.ensureAgentBubble(agent);
    if (this.chat.subAgentCards[cid]) {
      this._finalizeCardTextSegment(this.chat.subAgentCards[cid]);
    } else {
      this.finalizeCurrentTextSegment();
    }
    this.chat.involvedAgents.add(agent);
    this.chat.addActivityChip('tool-call', '⚡ ' + (data.tool_name || 'tool'));
    this.ui.createToolCard(agent, cid, data.tool_name || 'tool', data.arguments || {});
    this.chat.addLogEntry('⚡', '<strong>' + this.ui.getAgentLabel(agent) + '</strong> → ' + (data.tool_name || 'tool') + '()', null, data.arguments ? JSON.stringify(data.arguments) : null);
    this.chat.scrollToBottom();
  }

  handleToolResult(agent, cid, data) {
    this.chat.addLogEntry('✅', '<strong>' + this.ui.getAgentLabel(agent) + '</strong> tool result', null, data.result ? this.ui.truncateText(data.result, 120) : null);
  }

  handleThinking(agent, cid, data) {
    this.chat.addLogEntry('💭', '<strong>' + this.ui.getAgentLabel(agent) + '</strong> thinking', null, data.content ? this.ui.truncateText(data.content, 120) : null);
  }

  handleError(agent, cid, data) {
    this.finalizeCurrentTextSegment();
    Object.keys(this.chat.subAgentCards).forEach((key) => {
      const c = this.chat.subAgentCards[key];
      if (!c.finishRendered) {
        this._finalizeAgentCard(c, this.chat.agentTokens[key] || '', null);
      }
      c.statusEl.textContent = 'Error';
      c.statusEl.className = 'ic-status done';
      c.cardEl.classList.add('completed', 'collapsed');
    });
    this.chat.subAgentCards = {};
    this.chat.callStack = [];
    this.chat.pendingTokens = {};
    this.chat.pendingAgentCalls.clear();
    this.chat.showError(data.message || 'An unknown error occurred.');
    this.chat.deactivateAllAgents();
    this.chat.setProcessing(false);
    this.chat.addLogEntry('❌', data.message || 'Error', 'log-error');
    this.chat.scrollToBottom();
  }

  handleFinish(agent, cid, data) {
    if (this.chat.subAgentCards[cid]) {
      const card = this.chat.subAgentCards[cid];
      const tokens = this.chat.agentTokens[cid] || '';
      this._finalizeAgentCard(card, tokens, data.message);
      card.finishRendered = true;
      const subElapsed = ((Date.now() - (this.chat.agentStartTimes[cid] || Date.now())) / 1000).toFixed(1);
      if (card.elapsedEl) card.elapsedEl.textContent = subElapsed + 's';
      this.chat.setAgentActive(agent, false);
      this.chat.scrollToBottom();
      return;
    }
    
    this.chat.ensureAgentBubble(agent);
    const output = data.output || '';
    if (!this.chat.hasStreamedTopLevel && output) {
      this.ensureTextSegment();
      this.chat.currentTextSegment.innerHTML = this.ui.renderMarkdown(output);
      this.chat.currentTextSegment = null;
      this.chat.currentSegmentText = '';
    } else {
      this.finalizeCurrentTextSegment();
    }
    
    Object.keys(this.chat.subAgentCards).forEach((key) => {
      const c = this.chat.subAgentCards[key];
      if (!c.finishRendered) {
        this._finalizeAgentCard(c, this.chat.agentTokens[key] || '', null);
      }
      c.statusEl.textContent = 'Done';
      c.statusEl.className = 'ic-status done';
      c.cardEl.classList.add('completed', 'collapsed');
    });
    
    this.chat.subAgentCards = {};
    this.chat.callStack = [];
    this.chat.pendingTokens = {};
    this.chat.pendingAgentCalls.clear();
    
    if (this.chat.currentTextSegment && !this.chat.currentTextSegment.textContent.trim() && !this.chat.currentTextSegment.innerHTML.trim()) {
      this.chat.currentTextSegment.remove();
      this.chat.currentTextSegment = null;
    }
    
    const mainTokens = this.chat.agentTokens[agent] || '';
    const mainReturn = data.output || '';
    if (this.chat.hasStreamedTopLevel && mainReturn.trim() && mainReturn.trim() !== mainTokens.trim()) {
      const returnSection = document.createElement('div');
      returnSection.className = 'ic-section ic-result-section visible main-return-section';
      const returnLabel = document.createElement('div');
      returnLabel.className = 'ic-section-label';
      returnLabel.textContent = '✦ Response';
      const returnEl = document.createElement('div');
      returnEl.className = 'ic-content ic-result';
      returnEl.innerHTML = this.ui.renderMarkdown(mainReturn);
      returnSection.appendChild(returnLabel);
      returnSection.appendChild(returnEl);
      this.chat.contentStreamEl.appendChild(returnSection);
    }
    
    this.chat.addMessageTrail();
    this.chat.deactivateAllAgents();
    this.chat.setProcessing(false);
    this.chat.addLogEntry('✅', 'Response complete', 'log-finish');
    
    if (data.session_id) {
      this.chat._lastSessionId = data.session_id;
      this.chat.currentSession = data.session_id;
      if (!this.chat.sessions.includes(data.session_id)) {
        this.chat.sessions.unshift(data.session_id);
        this.chat.renderSessionList();
      }
    }
    
    this.chat.scrollToBottom();
  }

  handleForward(agent, data) {
    if (this.chat.isReplaying) {
      this.ui.addUserMessage(data.content || '');
    }
  }

  // Helper methods
  ensureTextSegment() {
    if (this.chat.currentTextSegment) return;
    if (!this.chat.contentStreamEl) return;
    const segment = document.createElement('div');
    segment.className = 'text-segment message-content';
    this.chat.contentStreamEl.appendChild(segment);
    this.chat.currentTextSegment = segment;
    this.chat.currentContentEl = segment;
    this.chat.currentSegmentText = '';
  }

  finalizeCurrentTextSegment() {
    if (!this.chat.currentTextSegment) return;
    if (this.chat.currentSegmentText.trim()) {
      this.chat.currentTextSegment.innerHTML = this.ui.renderMarkdown(this.chat.currentSegmentText);
    } else {
      this.chat.currentTextSegment.remove();
    }
    this.chat.currentTextSegment = null;
    this.chat.currentSegmentText = '';
  }

  ensureCardTextSegment(card) {
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
      card.currentTextSegment.innerHTML = this.ui.renderMarkdown(card.currentSegmentText);
    } else {
      card.currentTextSegment.remove();
    }
    card.currentTextSegment = null;
    card.currentSegmentText = '';
  }

  _finalizeAgentCard(card, tokens, result) {
    this._finalizeCardTextSegment(card);
    if (tokens && tokens.trim()) {
      card.resultEl.innerHTML = this.ui.renderMarkdown(tokens);
    }
    if (result && result.trim()) {
      card.resultEl.innerHTML = this.ui.renderMarkdown(result);
      card.resultSection.classList.add('visible');
    }
  }

  _flushPendingTokens(agent) {
    const pending = this.chat.pendingTokens[agent];
    if (!pending) return;
    const card = this.chat.subAgentCards[agent];
    if (!card) return;
    this.ensureCardTextSegment(card);
    card.currentSegmentText += pending;
    card.currentTextSegment.textContent = card.currentSegmentText;
    card.contentStreamEl.scrollTop = card.contentStreamEl.scrollHeight;
    delete this.chat.pendingTokens[agent];
  }
}

// Export for use in other modules
window.EventHandlers = EventHandlers;
