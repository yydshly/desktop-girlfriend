import assert from "node:assert/strict";
import { createBridgeStatus, updateBridgeStatus } from "./bridge-status.js";

function testBridgeStatusRecordsLifecycleAndMessages() {
  let status = createBridgeStatus("ws://127.0.0.1:8879");

  status = updateBridgeStatus(status, {
    kind: "open",
    at: "2026-07-01T10:00:00.000Z"
  });
  status = updateBridgeStatus(status, {
    kind: "message",
    message: { type: "avatar.state", payload: { state: "happy" } },
    at: "2026-07-01T10:00:01.000Z"
  });

  assert.equal(status.connection, "connected");
  assert.equal(status.messageCount, 1);
  assert.equal(status.lastEvent, "avatar.state");
  assert.equal(status.lastUpdatedAt, "2026-07-01T10:00:01.000Z");
  assert.deepEqual(status.lastPayload, { state: "happy" });
}

function testBridgeStatusRecordsErrorAndClose() {
  let status = createBridgeStatus("ws://127.0.0.1:8879");

  status = updateBridgeStatus(status, {
    kind: "error",
    error: "socket failed",
    at: "2026-07-01T10:00:02.000Z"
  });
  status = updateBridgeStatus(status, {
    kind: "close",
    at: "2026-07-01T10:00:03.000Z"
  });

  assert.equal(status.connection, "closed");
  assert.equal(status.error, "socket failed");
  assert.equal(status.lastUpdatedAt, "2026-07-01T10:00:03.000Z");
}

testBridgeStatusRecordsLifecycleAndMessages();
testBridgeStatusRecordsErrorAndClose();
console.log("bridge-status tests passed");
