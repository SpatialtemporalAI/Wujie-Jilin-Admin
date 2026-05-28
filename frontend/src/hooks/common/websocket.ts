import { ref } from 'vue';

const WS_BASE_URL = `${window.location.protocol === 'https:' ? 'wss' : 'ws'}://${window.location.host}`;

let ws: WebSocket | null = null;
const connected = ref(false);
const lastMessage = ref<any>(null);

export function useWebSocketNotification() {
  function connect(token: string) {
    if (ws) {
      disconnect();
    }

    const wsUrl = `${WS_BASE_URL}/admin/ws/notifications?token=${token}`;
    ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      connected.value = true;
      console.log('[WebSocket] 连接已建立');
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        lastMessage.value = data;

        // 触发全局事件，供通知中心监听
        if (data.type === 'notification') {
          window.dispatchEvent(new CustomEvent('ws:notification', { detail: data.data }));
        }
      } catch (e) {
        console.warn('[WebSocket] 消息解析失败:', event.data);
      }
    };

    ws.onclose = () => {
      connected.value = false;
      ws = null;
      console.log('[WebSocket] 连接已关闭');
    };

    ws.onerror = (error) => {
      console.error('[WebSocket] 连接错误:', error);
    };
  }

  function disconnect() {
    if (ws) {
      ws.close();
      ws = null;
      connected.value = false;
    }
  }

  function sendPing() {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ type: 'ping' }));
    }
  }

  return {
    connected,
    lastMessage,
    connect,
    disconnect,
    sendPing
  };
}
