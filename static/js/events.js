class EventHandlers {
  constructor(chat, ui) {
    this.chat = chat;
    this.ui = ui;
    this.scrollThrottle = null;
    this.activityText = '';
  }

  reset() {
    this.scrollThrottle = null;
    this.activityText = '';
  }

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
      case 'memory_context':
        this.handleMemoryContext(agent, cid, data);
        break;
      case 'memory_store':
        this.handleMemoryStore(agent, cid, data);
        break;
      case 'user_message':
        this.handleUserMessage(agent, cid, data);
        break;
      case 'summarized':
        this.handleSummarized(agent, cid, data);
        break;
    }
  }

  updateActivityIndicator(text) {
    if (!this.chat.activityIndicator) return;
    const textEl = this.chat.activityIndicator.querySelector('.activity-text');
    if (textEl) {
      textEl.textContent = text;
    }
  }

  handleToken(agent, cid, data) {
    const content = data.content || '';
    this.chat.ensureAgentBubble(agent);
    this.activityText += content;
    this.updateActivityIndicator(this.activityText || 'Processing...');
    this.chat.agentTokens[cid] = (this.chat.agentTokens[cid] || '') + content;
    this.scheduleScroll();
  }

  handleAgentCall(agent, cid, data) {
    const caller = data.from || agent;
    const target = data.agent_name || agent;
    this.chat.ensureAgentBubble(agent);
    this.updateActivityIndicator('Delegating to ' + target + '...');
    this.chat.addLogEntry(
      this.ui.getAgentIcon(caller),
      '<strong>' + this.ui.getAgentLabel(caller) + '</strong> → <strong>' + this.ui.getAgentLabel(target) + '</strong>',
      null,
      data.message ? this.ui.truncateText(data.message, 120) : null
    );
    this.scheduleScroll();
  }

  handleAgentReturn(agent, cid, data) {
    this.chat.addLogEntry(
      this.ui.getAgentIcon(agent),
      '<strong>' + this.ui.getAgentLabel(agent) + '</strong> done',
      null,
      data.result ? this.ui.truncateText(data.result, 120) : null
    );
  }

  handleToolCall(agent, cid, data) {
    const toolName = data.tool_name || 'tool';
    this.chat.ensureAgentBubble(agent);
    this.updateActivityIndicator('Running ' + toolName + '...');
    this.chat.addLogEntry(
      '⚡',
      '<strong>' + this.ui.getAgentLabel(agent) + '</strong> → ' + toolName + '()',
      null,
      data.arguments ? JSON.stringify(data.arguments) : null
    );
    this.scheduleScroll();
  }

  handleToolResult(agent, cid, data) {
    this.chat.addLogEntry(
      '✅',
      '<strong>' + this.ui.getAgentLabel(agent) + '</strong> tool result',
      null,
      data.result ? this.ui.truncateText(data.result, 120) : null
    );
  }

  handleThinking(agent, cid, data) {
    this.chat.ensureAgentBubble(agent);
    this.updateActivityIndicator('Thinking...');
    this.chat.addLogEntry(
      '💭',
      '<strong>' + this.ui.getAgentLabel(agent) + '</strong> thinking',
      null,
      data.content ? this.ui.truncateText(data.content, 120) : null
    );
  }

  handleError(agent, cid, data) {
    if (this.chat.activityIndicator) {
      this.chat.activityIndicator.remove();
      this.chat.activityIndicator = null;
    }
    this.chat.subAgentCards = {};
    this.chat.callStack = [];
    this.chat.pendingTokens = {};
    this.chat.pendingAgentCalls.clear();
    this.chat.showError(data.message || 'An error occurred.');
    this.chat.deactivateAllAgents();
    this.chat.setProcessing(false);
    this.chat.addLogEntry('❌', data.message || 'Error', 'log-error');
    this.chat.scrollToBottom();
  }

  handleFinish(agent, cid, data) {
    // Only process finish for the top-level (starting) agent.
    // Sub-agent finish events are internal and should not render in the main bubble.
    if (agent !== this.chat._sentAgent) {
      return;
    }

    if (this.chat.subAgentCards[cid]) {
      delete this.chat.subAgentCards[cid];
    }
    this.chat.ensureAgentBubble(agent);

    if (this.chat.activityIndicator) {
      this.chat.activityIndicator.remove();
      this.chat.activityIndicator = null;
    }

    const output = data.output || data.message || '';
    const finishEl = this.chat.currentFinishEl;
    if (output && finishEl) {
      finishEl.innerHTML = this.ui.renderMarkdown(output);
    }

    this.chat.subAgentCards = {};
    this.chat.callStack = [];
    this.chat.pendingTokens = {};
    this.chat.pendingAgentCalls.clear();

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

  handleMemoryContext(agent, cid, data) {
    this.chat.ensureAgentBubble(agent);
    this.chat.addLogEntry(
      '🧠',
      '<strong>Memory attached</strong>',
      'log-memory',
      data.content ? this.ui.truncateText(data.content, 150) : null
    );
  }

  handleMemoryStore(agent, cid, data) {
    const parts = [];
    if (data.user_message) parts.push('User: ' + this.ui.truncateText(data.user_message, 80));
    if (data.assistant_message) parts.push('Agent: ' + this.ui.truncateText(data.assistant_message, 80));
    this.chat.addLogEntry(
      '💾',
      '<strong>Memory stored</strong>',
      'log-memory',
      parts.length ? parts.join(' | ') : null
    );
  }

  handleUserMessage(agent, cid, data) {
    const message = data.message || '';
    const sender = data.sender || agent;
    this.chat.ensureAgentBubble(agent);
    this.chat.addLogEntry(
      '💬',
      '<strong>' + this.ui.getAgentLabel(sender) + '</strong> → user',
      'log-message',
      message ? this.ui.truncateText(message, 150) : null
    );
    this.scheduleScroll();
  }

  handleSummarized(agent, cid, data) {
    this.chat.ensureAgentBubble(agent);
    const parts = [];
    if (data.message_count) parts.push(data.message_count + ' messages summarized');
    if (data.tokens_before && data.tokens_after) {
      parts.push(data.tokens_before + ' → ' + data.tokens_after + ' tokens');
    }
    this.chat.addLogEntry(
      '📝',
      '<strong>Context summarized</strong>',
      'log-memory',
      parts.length ? parts.join(' | ') : null
    );
  }

  scheduleScroll() {
    if (!this.scrollThrottle) {
      this.scrollThrottle = setTimeout(() => {
        this.chat.scrollToBottom();
        this.scrollThrottle = null;
      }, 50);
    }
  }
}

window.EventHandlers = EventHandlers;
