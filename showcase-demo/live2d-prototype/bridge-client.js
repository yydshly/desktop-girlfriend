export function createBridgeClient({
  WebSocketClass = globalThis.WebSocket,
  setTimeout = globalThis.setTimeout.bind(globalThis),
  clearTimeout = globalThis.clearTimeout.bind(globalThis),
  reconnectDelayMs = 1200,
  onEvent = () => {},
  onMessage = () => {}
} = {}) {
  let socket = null;
  let reconnectTimer = null;
  let reconnectEnabled = false;
  let connectionId = 0;

  function connect(url, { reconnect = false } = {}) {
    reconnectEnabled = reconnect;
    onEvent({ kind: "connecting", url });
    const nextConnectionId = connectionId + 1;
    connectionId = nextConnectionId;
    clearReconnectTimer();
    if (socket) {
      socket.close();
    }
    socket = new WebSocketClass(url);
    socket.addEventListener("open", () => {
      onEvent({ kind: "open" });
    });
    socket.addEventListener("message", (event) => {
      const message = JSON.parse(event.data);
      onEvent({ kind: "message", message });
      onMessage(message);
    });
    socket.addEventListener("error", () => {
      onEvent({ kind: "error", error: "WebSocket error" });
    });
    socket.addEventListener("close", () => {
      onEvent({ kind: "close" });
      if (nextConnectionId !== connectionId) {
        return;
      }
      socket = null;
      if (!reconnectEnabled) {
        return;
      }
      clearReconnectTimer();
      reconnectTimer = setTimeout(() => {
        connect(url, { reconnect: true });
      }, reconnectDelayMs);
    });
  }

  function disconnect() {
    reconnectEnabled = false;
    clearReconnectTimer();
    if (socket) {
      socket.close();
    }
  }

  function clearReconnectTimer() {
    if (reconnectTimer) {
      clearTimeout(reconnectTimer);
      reconnectTimer = null;
    }
  }

  return {
    connect,
    disconnect
  };
}
