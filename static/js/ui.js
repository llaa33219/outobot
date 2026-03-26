/**
 * UI Rendering Functions for OutObot
 * Contains all functions for rendering messages, bubbles, and cards
 */

class UIRenderer {
  constructor(chat) {
    this.chat = chat;
  }

  formatTime() {
    return new Date().toLocaleTimeString([], { hour12: false });
  }

  escapeHTML(str) {
    if (!str) return '';
    return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#039;');
  }

  truncateText(text, maxLen) {
    if (!text) return '';
    return text.length > maxLen ? text.substring(0, maxLen) + '...' : text;
  }

  getAgentIcon(agentName) {
    const meta = this.chat.agentMeta[agentName] || {};
    return meta.icon || '🔆';
  }

  getAgentLabel(agentName) {
    const meta = this.chat.agentMeta[agentName] || {};
    return meta.label || agentName;
  }

  getAgentColor(agentName) {
    const meta = this.chat.agentMeta[agentName] || {};
    return meta.color || '#6366f1';
  }

  _splitReasoningTags(text) {
    const pattern = /<(think|reasoning|thought)>([\s\S]*?)<\/\1>/gi;
    const segments = [];
    let lastIndex = 0;
    let match;
    while ((match = pattern.exec(text)) !== null) {
      if (match.index > lastIndex) {
        const before = text.slice(lastIndex, match.index);
        if (before.trim()) segments.push({ type: 'text', content: before });
      }
      segments.push({ type: 'reasoning', content: match[2] });
      lastIndex = match.index + match[0].length;
    }
    if (lastIndex < text.length) {
      const remaining = text.slice(lastIndex);
      const unclosed = remaining.match(/<(think|reasoning|thought)>([\s\S]*)$/i);
      if (unclosed) {
        const before = remaining.slice(0, unclosed.index);
        if (before.trim()) segments.push({ type: 'text', content: before });
        segments.push({ type: 'reasoning', content: unclosed[2] });
      } else if (remaining.trim()) {
        segments.push({ type: 'text', content: remaining });
      }
    }
    return segments.length > 0 ? segments : [{ type: 'text', content: text }];
  }

  _renderMarkdownInner(text) {
    if (typeof marked !== 'undefined') {
      try {
        let html = marked.parse(text || '');
        if (typeof hljs !== 'undefined') {
          const temp = document.createElement('div');
          temp.innerHTML = html;
          temp.querySelectorAll('pre code').forEach((block) => {
            hljs.highlightElement(block);
          });
          html = temp.innerHTML;
        }
        return html;
      } catch (e) {
        console.warn('marked.parse failed, using fallback:', e);
      }
    }
    return this.escapeHTML(text || '');
  }

  renderMarkdown(text) {
    const segments = this._splitReasoningTags(text);
    let html = '';
    for (const seg of segments) {
      if (seg.type === 'reasoning') {
        html += '<details class="reasoning-block"><summary class="reasoning-summary">' +
          '🧠 Reasoning</summary><div class="reasoning-content">' +
          this._renderMarkdownInner(seg.content) + '</div></details>';
      } else {
        html += this._renderMarkdownInner(seg.content);
      }
    }
    return html;
  }

  // Render user message bubble
  renderUserMessage(text, container) {
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
        <div class="message-content">${this.renderMarkdown(text)}</div>
      </div>
    `;
    (container || this.chat.els.chatArea).appendChild(msg);
    this.chat.scrollToBottom(true);
    return msg;
  }

  // Add user message during live streaming (appends to chatArea directly or to messageContainer if set for replay)
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
    const container = this.chat.messageContainer || this.chat.els.chatArea;
    container.appendChild(msg);
    this.chat.scrollToBottom(true);
    return msg;
  }

  // Create agent bubble element (not appended yet)
  createAgentBubbleElement(agentName) {
    const meta = this.chat.agentMeta[agentName] || { icon: '🔆', label: agentName, color: '#6366f1' };
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

    return {
      element: msg,
      activity,
      contentStream,
      textSegment,
      thinking
    };
  }

  // Create delegation card for agent→agent calls
  createDelegationCard(caller, target, message) {
    const callerMeta = this.chat.agentMeta[caller] || { icon: '🔆', label: caller, color: '#6366f1' };
    const targetMeta = this.chat.agentMeta[target] || { icon: '🔆', label: target, color: '#6366f1' };

    let depth = 0;
    if (this.chat.subAgentCards[caller]) {
      depth = (parseInt(this.chat.subAgentCards[caller].cardEl.dataset.depth) || 0) + 1;
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

  // Create tool card
  createToolCard(agentName, cardKey, toolName, args) {
    const meta = this.chat.agentMeta[agentName] || { icon: '🔆', label: agentName, color: '#6366f1' };

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

    if (this.chat.subAgentCards[cardKey]) {
      this.chat.subAgentCards[cardKey].contentStreamEl.appendChild(card);
    } else if (this.chat.contentStreamEl) {
      this.chat.contentStreamEl.appendChild(card);
    }

    return card;
  }

  // Render flat mode agent message
  renderAgentMessage(content, agentName, container) {
    const bubble = this.createAgentBubbleElement(agentName);
    bubble.thinking.remove();
    bubble.textSegment.innerHTML = this.renderMarkdown(content);
    (container || this.chat.els.chatArea).appendChild(bubble.element);
    this.chat.scrollToBottom(true);
    return bubble.element;
  }

  // Render flat mode loop-internal message
  renderLoopInternalMessage(caller, agent, content, container) {
    const callerMeta = this.chat.agentMeta[caller] || { icon: '🔆', label: caller, color: '#6366f1' };
    const agentMeta = this.chat.agentMeta[agent] || { icon: '🔆', label: agent, color: '#6366f1' };

    const card = document.createElement('div');
    card.className = 'interaction-card agent-card';
    card.style.setProperty('--card-color', agentMeta.color);

    const header = document.createElement('div');
    header.className = 'ic-header';
    header.innerHTML =
      '<span class="ic-toggle">▼</span>' +
      '<span class="ic-header-text">' +
        '<span style="color:' + callerMeta.color + '">' + callerMeta.icon + ' ' + this.escapeHTML(callerMeta.label) + '</span>' +
        ' <span class="ic-arrow">→</span> ' +
        '<span style="color:' + agentMeta.color + '">' + agentMeta.icon + ' ' + this.escapeHTML(agentMeta.label) + '</span>' +
      '</span>' +
      '<span class="ic-status done">Done</span>';
    header.addEventListener('click', () => card.classList.toggle('collapsed'));

    const body = document.createElement('div');
    body.className = 'ic-body';

    const bodyInner = document.createElement('div');
    bodyInner.className = 'ic-body-inner';

    const resultSection = document.createElement('div');
    resultSection.className = 'ic-section ic-result-section visible';
    const resultLabel = document.createElement('div');
    resultLabel.className = 'ic-section-label';
    resultLabel.textContent = '✦ Result';
    const resultEl = document.createElement('div');
    resultEl.className = 'ic-content ic-result';
    resultEl.innerHTML = this.renderMarkdown(content);
    resultSection.appendChild(resultLabel);
    resultSection.appendChild(resultEl);

    bodyInner.appendChild(resultSection);
    body.appendChild(bodyInner);

    card.appendChild(header);
    card.appendChild(body);

    (container || this.chat.els.chatArea).appendChild(card);
    this.chat.scrollToBottom(true);
    return card;
  }
}

// Export for use in other modules
window.UIRenderer = UIRenderer;
