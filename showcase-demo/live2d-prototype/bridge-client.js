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
  let isOpen = false;

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
      isOpen = true;
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
      isOpen = false;
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
    isOpen = false;
    if (socket) {
      socket.close();
    }
  }

  function sendStatus(type, payload = {}) {
    if (!socket || !isOpen || typeof socket.send !== "function") {
      return false;
    }
    const message = {
      type,
      timestamp: new Date().toISOString(),
      modelUrl: typeof payload.modelUrl === "string" ? payload.modelUrl : "",
      modelId: typeof payload.modelId === "string" ? payload.modelId : "",
      details: payload.details && typeof payload.details === "object" ? payload.details : {}
    };
    socket.send(JSON.stringify(message));
    onEvent({ kind: "status-sent", message });
    return true;
  }

  function clearReconnectTimer() {
    if (reconnectTimer) {
      clearTimeout(reconnectTimer);
      reconnectTimer = null;
    }
  }

  return {
    connect,
    disconnect,
    sendStatus
  };
}
