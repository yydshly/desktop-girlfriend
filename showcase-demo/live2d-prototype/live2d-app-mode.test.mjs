import assert from "node:assert/strict";
import { getLive2DAppMode, shouldMountDebugPanel } from "./live2d-app-mode.js";

function testDesktopRouteUsesDesktopMode() {
  const mode = getLive2DAppMode(new URLSearchParams("desktop=1"));

  assert.equal(mode, "desktop");
  assert.equal(shouldMountDebugPanel(mode), false);
}

function testDefaultRouteUsesShowcaseMode() {
  const mode = getLive2DAppMode(new URLSearchParams(""));

  assert.equal(mode, "showcase");
  assert.equal(shouldMountDebugPanel(mode), true);
}

testDesktopRouteUsesDesktopMode();
testDefaultRouteUsesShowcaseMode();
console.log("live2d-app-mode tests passed");
