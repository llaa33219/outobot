/**
 * Session Replay Logic for OutObot
 * Handles replaying session events to reconstruct a conversation
 */

class SessionReplay {
  constructor(chat, ui, eventHandlers) {
    this.chat = chat;
    this.ui = ui;
    this.eventHandlers = eventHandlers;
  }

  /**
   * Replay a session from events array
   * Events are processed in order with delays to simulate real-time streaming
   */
  replaySession(events) {
    // Reset all state
    this.chat.subAgentCards = {};
    this.chat.callStack = [];
    this.chat.agentTokens = {};
    this.chat.pendingTokens = {};
    this.chat.pendingAgentCalls.clear();
    this.chat.agentStartTimes = {};
    this.chat.hasStreamedTopLevel = false;
    this.chat.messageContainer = null;
    this.chat.isReplaying = true;

    // Track whether we've created the agent bubble
    let agentBubbleCreated = false;

    // Process events sequentially with delays
    let eventIndex = 0;
    const processNextEvent = () => {
      if (eventIndex >= events.length) {
        this.chat.isReplaying = false;
        this.chat.addLogEntry('📜', `Replayed ${events.length} events`);
        return;
      }

      const event = events[eventIndex];
      const delay = this.calculateDelay(event, eventIndex, events);

      setTimeout(() => {
        // Special handling for forward event (user message)
        if (event.type === 'forward') {
          // User message goes to chatArea (like live chat)
          this.ui.renderUserMessage(event.data.content, null);
        } else {
          // For all other events, ensure agent bubble exists before processing
          if (!agentBubbleCreated) {
            this.chat.ensureAgentBubble('outo');
            agentBubbleCreated = true;
          }
          this.eventHandlers.handleEvent(event);
        }

        this.chat.scrollToBottom();
        eventIndex++;
        processNextEvent();
      }, delay);
    };

    // Start processing after a short initial delay
    setTimeout(processNextEvent, 100);
  }

  /**
   * Calculate delay before processing next event
   * Creates natural pacing during replay
   */
  calculateDelay(event, index, events) {
    const baseDelay = 60;

    // Token events get faster subsequent delays (streaming effect)
    if (event.type === 'token') {
      return 20;
    }

    // Agent call/return gets longer delay (significant events)
    if (event.type === 'agent_call' || event.type === 'agent_return') {
      return 150;
    }

    // Tool events get medium delay
    if (event.type === 'tool_call' || event.type === 'tool_result') {
      return 100;
    }

    // Finish event gets longer delay (let user read final response)
    if (event.type === 'finish') {
      return 300;
    }

    // Thinking and other events
    return baseDelay;
  }

  /**
   * Load session data and start replay
   */
  async loadSessionData(sessionId) {
    this.chat.currentSession = sessionId;

    // Reset live chat state
    this.chat.currentBubble = null;
    this.chat.currentContentEl = null;
    this.chat.currentActivityEl = null;
    this.chat.contentStreamEl = null;
    this.chat.currentTextSegment = null;
    this.chat.currentSegmentText = '';
    this.chat.hasStreamedTopLevel = false;
    this.chat.agentTokens = {};
    this.chat.subAgentCards = {};
    this.chat.callStack = [];
    this.chat.pendingTokens = {};
    this.chat.pendingAgentCalls.clear();
    this.chat.agentStartTimes = {};

    // Clear chat area
    this.chat.els.chatArea.querySelectorAll('.message, .agent-card, .tool-card, .interaction-card').forEach(el => el.remove());

    // Hide welcome
    const welcome = this.chat.els.chatArea.querySelector('.welcome');
    if (welcome) {
      welcome.remove();
      this.chat.els.welcome = null;
    }

    // Fetch session data
    const data = await this.chat.loadSession(sessionId);
    if (!data || !data.messages) {
      this.chat.logActivity('Failed to load session', 'error');
      return;
    }

    // If session has events, use replay mode
    if (data.events && data.events.length > 0) {
      // Migrate old event format if needed
      const migratedEvents = this.migrateEvents(data.events);
      this.replaySession(migratedEvents);
    } else {
      // Fallback to flat message rendering for legacy sessions
      this.renderFlatSession(data.messages);
    }

    this.chat.scrollToBottom();
    this.chat.logActivity(`Loaded session ${sessionId.substring(0, 8)}...`);
  }

  /**
   * Migrate old event format to new format
   */
  migrateEvents(events) {
    return events.map(event => {
      if (event.type === 'agent_call' && event.data) {
        const data = { ...event.data };
        if (!data.from && event.agent_name) {
          data.from = event.agent_name;
        }
        if (!data.agent_name && data.target) {
          data.agent_name = data.target;
        }
        if (data.agent_name === event.agent_name && data.from && data.from !== event.agent_name) {
          return {
            ...event,
            data: {
              ...data,
              from: event.agent_name,
              agent_name: data.from
            }
          };
        }
        return {
          ...event,
          data
        };
      }

      if (event.type === 'finish') {
        if (event.output !== undefined && event.data === undefined) {
          return {
            type: event.type,
            agent_name: event.agent_name || 'outo',
            data: {
              message: event.output,
              output: event.output,
              session_id: event.session_id
            }
          };
        }
      }
      return event;
    });
  }

  renderFlatSession(messages) {
    this.chat.isReplaying = true;
    messages.forEach(msg => {
      const cat = msg.category;
      if (cat === 'user' || (msg.sender === 'You')) {
        this.ui.renderUserMessage(msg.content, null);
      } else if (cat === 'top-level') {
        this.ui.renderAgentMessage(msg.content, msg.sender, null);
      } else if (cat === 'loop-internal') {
        this.ui.renderLoopInternalMessage(msg.caller || msg.sender, msg.sender, msg.content, null);
      } else {
        this.ui.renderAgentMessage(msg.content, msg.sender, null);
      }
    });
    this.chat.isReplaying = false;
  }
}

// Export for use in other modules
window.SessionReplay = SessionReplay;
