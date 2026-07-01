import assert from "node:assert/strict";
import {
  parseMotionBindingsText,
  sanitizeMotionBindings,
  serializeMotionBindings
} from "./motion-bindings.js";

function testSanitizeMotionBindingsNormalizesEntries() {
  assert.deepEqual(
    sanitizeMotionBindings({
      happy: { group: "Idle", index: "5" },
      sad: { group: "TapBody", index: -1 }
    }),
    {
      happy: { group: "Idle", index: 5 },
      sad: { group: "TapBody", index: 0 }
    }
  );
}

function testParseMotionBindingsTextRejectsArrays() {
  assert.throws(
    () => parseMotionBindingsText("[]"),
    /Motion bindings must be a JSON object/
  );
}

function testSerializeMotionBindingsFormatsJson() {
  assert.equal(
    serializeMotionBindings({ happy: { group: "Idle", index: 5 } }),
    '{\n  "happy": {\n    "group": "Idle",\n    "index": 5\n  }\n}'
  );
}

testSanitizeMotionBindingsNormalizesEntries();
testParseMotionBindingsTextRejectsArrays();
testSerializeMotionBindingsFormatsJson();
console.log("motion-bindings tests passed");
