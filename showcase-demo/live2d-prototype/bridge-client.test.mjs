import assert from "node:assert/strict";
import { createBridgeClient } from "./bridge-client.js";

class FakeWebSocket {
  static instances = [];

  constructor(url) {
    this.url = url;
    this.listeners = {};
    this.closeCount = 0;
    FakeWebSocket.instances.push(this);
  }

  addEventListener(type, handler) {
    this.listeners[type] = handler;
  }

  emit(type, event = {}) {
    this.listeners[type]?.(event);
  }

  close() {
    this.closeCount += 1;
  }

  send(data) {
    this.sent = this.sent || [];
    this.sent.push(data);
  }
}

function createFakeTimers() {
  const timers = [];
  return {
    timers,
    setTimeout(callback, delay) {
      timers.push({ callback, delay });
      return timers.length;
    },
    clearTimeout(id) {
      timers[id - 1] = null;
    }
  };
}

function resetFakeWebSocket() {
  FakeWebSocket.instances = [];
}

function testBridgeClientForwardsLifecycleAndMessages() {
  resetFakeWebSocket();
  const events = [];
  const messages = [];
  const timers = createFakeTimers();
  const client = createBridgeClient({
    WebSocketClass: FakeWebSocket,
    setTimeout: timers.setTimeout,
    clearTimeout: timers.clearTimeout,
    onEvent: events.push.bind(events),
    onMessage: messages.push.bind(messages)
  });

  client.connect("ws://127.0.0.1:8879");
  const socket = FakeWebSocket.instances[0];
  socket.emit("open");
  socket.emit("message", {
    data: JSON.stringify({ type: "avatar.state", payload: { state: "happy" } })
  });

  assert.deepEqual(events.map((event) => event.kind), ["connecting", "open", "message"]);
  assert.deepEqual(messages, [{ type: "avatar.state", payload: { state: "happy" } }]);
}

function testBridgeClientManualDisconnectDoesNotReconnect() {
  resetFakeWebSocket();
  const events = [];
  const timers = createFakeTimers();
  const client = createBridgeClient({
    WebSocketClass: FakeWebSocket,
    setTimeout: timers.setTimeout,
    clearTimeout: timers.clearTimeout,
    onEvent: events.push.bind(events),
    onMessage: () => {}
  });

  client.connect("ws://127.0.0.1:8879", { reconnect: true });
  const socket = FakeWebSocket.instances[0];
  client.disconnect();
  socket.emit("close");

  assert.equal(socket.closeCount, 1);
  assert.equal(timers.timers.filter(Boolean).length, 0);
  assert.deepEqual(events.map((event) => event.kind), ["connecting", "close"]);
}

function testBridgeClientReconnectsAfterUnexpectedClose() {
  resetFakeWebSocket();
  const timers = createFakeTimers();
  const client = createBridgeClient({
    WebSocketClass: FakeWebSocket,
    setTimeout: timers.setTimeout,
    clearTimeout: timers.clearTimeout,
    onEvent: () => {},
    onMessage: () => {}
  });

  client.connect("ws://127.0.0.1:8879", { reconnect: true });
  FakeWebSocket.instances[0].emit("close");
  assert.equal(timers.timers.filter(Boolean).length, 1);
  assert.equal(timers.timers.filter(Boolean)[0].delay, 1200);

  timers.timers.filter(Boolean)[0].callback();
  assert.equal(FakeWebSocket.instances.length, 2);
  assert.equal(FakeWebSocket.instances[1].url, "ws://127.0.0.1:8879");
}

function testBridgeClientSendsRuntimeStatusEvent() {
  resetFakeWebSocket();
  const client = createBridgeClient({
    WebSocketClass: FakeWebSocket,
    onEvent: () => {},
    onMessage: () => {}
  });

  client.connect("ws://127.0.0.1:8879");
  const socket = FakeWebSocket.instances[0];
  socket.emit("open");
  const sent = client.sendStatus("live2d.runtime_ready", {
    modelUrl: "./model.model3.json"
  });

  assert.equal(sent, true);
  const message = JSON.parse(socket.sent[0]);
  assert.equal(message.type, "live2d.runtime_ready");
  assert.equal(message.modelUrl, "./model.model3.json");
  assert.equal(typeof message.timestamp, "string");
  assert.deepEqual(message.details, {});
}

function testBridgeClientDoesNotSendStatusBeforeOpen() {
  resetFakeWebSocket();
  const client = createBridgeClient({
    WebSocketClass: FakeWebSocket,
    onEvent: () => {},
    onMessage: () => {}
  });

  client.connect("ws://127.0.0.1:8879");

  assert.equal(client.sendStatus("live2d.runtime_ready"), false);
}

testBridgeClientForwardsLifecycleAndMessages();
testBridgeClientManualDisconnectDoesNotReconnect();
testBridgeClientReconnectsAfterUnexpectedClose();
testBridgeClientSendsRuntimeStatusEvent();
testBridgeClientDoesNotSendStatusBeforeOpen();
console.log("bridge-client tests passed");
