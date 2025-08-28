/**
 * Singleton WebSocket manager to prevent multiple connections
 */

type MessageHandler = (data: any) => void;

class WebSocketManager {
  private static instance: WebSocketManager;
  private ws: WebSocket | null = null;
  private handlers: Set<MessageHandler> = new Set();
  private baseUrl: string;
  private reconnectTimer: NodeJS.Timeout | null = null;
  private pingInterval: NodeJS.Timeout | null = null;
  private isIntentionallyClosed: boolean = false;

  private constructor() {
    const apiUrl = typeof window !== 'undefined'
      ? (window.location.hostname.includes('phala.network')
        ? `https://${window.location.hostname.replace('-3000', '-8001')}`
        : 'http://localhost:8001')
      : process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';
    
    this.baseUrl = apiUrl.replace('https', 'wss').replace('http', 'ws') + '/ws';
  }

  static getInstance(): WebSocketManager {
    if (!WebSocketManager.instance) {
      WebSocketManager.instance = new WebSocketManager();
    }
    return WebSocketManager.instance;
  }

  connect(): void {
    // Check if we're in a browser environment
    if (typeof window === 'undefined') {
      return;
    }

    // Don't create new connection if one exists
    if (this.ws && (this.ws.readyState === WebSocket.CONNECTING || 
        this.ws.readyState === WebSocket.OPEN)) {
      return;
    }

    // Clear any existing reconnect timer
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }

    try {
      this.ws = new WebSocket(this.baseUrl);
      
      this.ws.onopen = () => {
        console.log('Connected to Kurtosis WebSocket');
        this.isIntentionallyClosed = false;
        
        // Clear old ping interval if exists
        if (this.pingInterval) {
          clearInterval(this.pingInterval);
        }
        
        // Setup ping to keep connection alive
        this.pingInterval = setInterval(() => {
          if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({ type: 'ping' }));
          }
        }, 30000);
      };

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          console.log('WebSocket message:', data);
          // Notify all registered handlers
          this.handlers.forEach(handler => {
            try {
              handler(data);
            } catch (e) {
              console.error('Error in WebSocket handler:', e);
            }
          });
        } catch (e) {
          console.error('Failed to parse WebSocket message:', e);
        }
      };

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error);
      };

      this.ws.onclose = () => {
        console.log('Disconnected from Kurtosis WebSocket');
        
        // Clear ping interval
        if (this.pingInterval) {
          clearInterval(this.pingInterval);
          this.pingInterval = null;
        }
        
        // Only reconnect if not intentionally closed and we have active handlers
        if (!this.isIntentionallyClosed && this.handlers.size > 0 && !this.reconnectTimer) {
          this.reconnectTimer = setTimeout(() => {
            console.log('Attempting to reconnect WebSocket...');
            this.reconnectTimer = null;
            if (this.handlers.size > 0) {
              this.connect();
            }
          }, 3000);
        }
      };
    } catch (error) {
      console.error('Failed to create WebSocket:', error);
    }
  }

  subscribe(handler: MessageHandler): () => void {
    this.handlers.add(handler);
    
    // Connect if not already connected
    if (!this.ws || this.ws.readyState === WebSocket.CLOSED) {
      this.connect();
    }
    
    // Return unsubscribe function
    return () => {
      this.handlers.delete(handler);
      
      // If no more handlers, close connection
      if (this.handlers.size === 0) {
        this.disconnect();
      }
    };
  }

  disconnect(): void {
    this.isIntentionallyClosed = true;
    
    // Clear timers
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    
    if (this.pingInterval) {
      clearInterval(this.pingInterval);
      this.pingInterval = null;
    }
    
    // Close WebSocket
    if (this.ws && this.ws.readyState !== WebSocket.CLOSED) {
      this.ws.close();
      this.ws = null;
    }
  }

  getState(): number {
    return this.ws?.readyState ?? WebSocket.CLOSED;
  }
}

export const wsManager = WebSocketManager.getInstance();