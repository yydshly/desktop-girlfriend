import assert from "node:assert/strict";
import { inspectModelPackage } from "./model-package-inspector.js";

globalThis.window = {
  location: {
    href: "http://127.0.0.1:8786/live2d-prototype/"
  }
};

globalThis.fetch = async () => ({
  ok: true,
  status: 200,
  statusText: "OK",
  async json() {
    return {
      Version: 3,
      FileReferences: {
        Moc: "Model.moc3",
        Textures: ["textures/texture_00.png"],
        Physics: "Model.physics3.json",
        Expressions: [
          { Name: "smile", File: "expressions/smile.exp3.json" },
          { Name: "sad", File: "expressions/sad.exp3.json" }
        ],
        Motions: {
          Idle: [{ File: "motions/idle_0.motion3.json" }, { File: "motions/idle_1.motion3.json" }],
          TapBody: [{ File: "motions/tap.motion3.json" }]
        }
      },
      Groups: [
        { Name: "LipSync", Ids: ["ParamMouthOpenY"] },
        { Name: "EyeBlink", Ids: ["ParamEyeLOpen", "ParamEyeROpen"] }
      ]
    };
  }
});

async function testInspectModelPackageReportsMotionGroupCounts() {
  const info = await inspectModelPackage("./assets/models/custom/Model.model3.json");

  assert.equal(info.motionCount, 3);
  assert.deepEqual(info.motionGroups, ["Idle", "TapBody"]);
  assert.deepEqual(info.motionGroupCounts, { Idle: 2, TapBody: 1 });
  assert.deepEqual(info.lipSyncIds, ["ParamMouthOpenY"]);
  assert.equal(info.expressionCount, 2);
  assert.deepEqual(info.expressionNames, ["smile", "sad"]);
}

await testInspectModelPackageReportsMotionGroupCounts();
console.log("model-package-inspector tests passed");
