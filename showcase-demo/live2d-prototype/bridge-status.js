export function createBridgeStatus(url = "") {
  return {
    url,
    connection: "idle",
    messageCount: 0,
    lastEvent: "none",
    lastPayload: null,
    lastUpdatedAt: "",
    error: ""
  };
}

export function updateBridgeStatus(status, event = {}) {
  const nextStatus = {
    ...createBridgeStatus(status?.url || ""),
    ...status,
    lastUpdatedAt: event.at || new Date().toISOString()
  };

  if (event.kind === "connecting") {
    return { ...nextStatus, url: event.url || nextStatus.url, connection: "connecting", error: "" };
  }
  if (event.kind === "open") {
    return { ...nextStatus, connection: "connected", error: "" };
  }
  if (event.kind === "message") {
    return {
      ...nextStatus,
      connection: "connected",
      messageCount: nextStatus.messageCount + 1,
      lastEvent: event.message?.type || "unknown",
      lastPayload: event.message?.payload ?? null,
      error: ""
    };
  }
  if (event.kind === "error") {
    return { ...nextStatus, connection: "error", error: String(event.error || "unknown error") };
  }
  if (event.kind === "close") {
    return { ...nextStatus, connection: "closed" };
  }

  return nextStatus;
}

export function renderBridgeStatus(status) {
  return JSON.stringify(
    {
      connection: status.connection,
      url: status.url,
      messageCount: status.messageCount,
      lastEvent: status.lastEvent,
      lastUpdatedAt: status.lastUpdatedAt,
      error: status.error,
      lastPayload: status.lastPayload
    },
    null,
    2
  );
}
