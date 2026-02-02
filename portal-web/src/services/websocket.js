class WebSocketService {
  constructor() {
    this.ws = null;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.reconnectDelay = 3000;
    this.listeners = new Map();
    this.watchedProjects = new Set();
    this.heartbeatInterval = null;
  }

  /**
   * Derives WebSocket URL from API URL
   * Converts http:// to ws:// and https:// to wss://
   */
  getWebSocketUrl() {
    // Use explicit WS URL if provided
    if (import.meta.env.VITE_WS_URL) {
      return import.meta.env.VITE_WS_URL;
    }

    // Derive from API URL
    const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
    
    // Convert http(s):// to ws(s)://
    if (apiUrl.startsWith('https://')) {
      return apiUrl.replace('https://', 'wss://');
    }
    return apiUrl.replace('http://', 'ws://');
  }

  connect(token) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      return;
    }

    const wsUrl = this.getWebSocketUrl();

    this.ws = new WebSocket(`${wsUrl.replace(/\/$/, '')}/ws/${token}`);

    this.ws.onopen = () => {
      this.reconnectAttempts = 0;

      this.watchedProjects.forEach((projectId) => {
        this.watchProject(projectId);
      });

      this.startHeartbeat();
    };

    this.ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);

        const listeners = this.listeners.get(message.type) || [];
        listeners.forEach((callback) => callback(message));

        const globalListeners = this.listeners.get('*') || [];
        globalListeners.forEach((callback) => callback(message));
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    this.ws.onclose = () => {
      this.stopHeartbeat();
      this.attemptReconnect();
    };
  }

  disconnect() {
    this.stopHeartbeat();
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  attemptReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      return;
    }

    this.reconnectAttempts += 1;

    setTimeout(() => {
      const token = localStorage.getItem('token');
      if (token) {
        this.connect(token);
      }
    }, this.reconnectDelay);
  }

  startHeartbeat() {
    this.heartbeatInterval = setInterval(() => {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.send({ type: 'ping' });
      }
    }, 30000);
  }

  stopHeartbeat() {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
  }

  send(message) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    }
  }

  watchProject(projectId) {
    this.watchedProjects.add(projectId);
    this.send({
      type: 'watch_project',
      project_id: projectId,
    });
  }

  unwatchProject(projectId) {
    this.watchedProjects.delete(projectId);
    this.send({
      type: 'unwatch_project',
      project_id: projectId,
    });
  }

  on(messageType, callback) {
    if (!this.listeners.has(messageType)) {
      this.listeners.set(messageType, []);
    }
    this.listeners.get(messageType).push(callback);
  }

  off(messageType, callback) {
    if (this.listeners.has(messageType)) {
      const listeners = this.listeners.get(messageType);
      const index = listeners.indexOf(callback);
      if (index > -1) {
        listeners.splice(index, 1);
      }
    }
  }
}

const wsService = new WebSocketService();

export default wsService;