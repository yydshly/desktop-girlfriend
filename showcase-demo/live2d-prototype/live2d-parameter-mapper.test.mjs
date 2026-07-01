import assert from "node:assert/strict";
import {
  getLive2DParameterIds,
  mapStateToLive2DCommands,
  resolveLive2DParameterAliases
} from "./live2d-parameter-mapper.js";

function testMapperUsesDefaultParameterAliases() {
  const command = mapStateToLive2DCommands(
    { emotion: "engaged", mouth: 0.5, intensity: 0.5 },
    { x: 0.2, y: -0.1 }
  );

  assert.equal(command.parameters.ParamMouthOpenY, 0.5);
  assert.ok("ParamAngleX" in command.parameters);
  assert.ok("ParamEyeBallX" in command.parameters);
  assert.equal(command.parameterDiagnostics.mouthOpen.id, "ParamMouthOpenY");
  assert.equal(command.parameterDiagnostics.mouthOpen.source, "default");
}

function testMapperUsesProfileParameterAliasesRangesAndInvert() {
  const command = mapStateToLive2DCommands(
    { emotion: "engaged", mouth: 0.5, intensity: 0.5 },
    { x: 0.5, y: 0.25 },
    {
      parameters: {
        mouthOpen: { id: "ParamCustomMouth", min: -1, max: 1, scale: 2, invert: true, source: "profile" },
        headX: { id: "ParamCustomHeadX", min: -20, max: 20, scale: 0.5, invert: false, source: "profile" },
        eyeX: { id: "ParamCustomEyeX", min: -0.5, max: 0.5, scale: 1, invert: false, source: "profile" }
      }
    }
  );

  assert.equal(command.parameters.ParamCustomMouth, -1);
  assert.ok(command.parameters.ParamCustomHeadX <= 20);
  assert.equal(command.parameters.ParamCustomEyeX, 0.5);
  assert.equal(command.parameters.ParamMouthOpenY, undefined);
  assert.equal(command.parameterDiagnostics.mouthOpen.source, "profile");
  assert.equal(command.parameterDiagnostics.mouthOpen.id, "ParamCustomMouth");
}

function testResolveAliasesReportsMissingParameterWarnings() {
  const aliases = resolveLive2DParameterAliases({
    mouthOpen: { id: "", source: "profile" }
  });

  assert.match(aliases.warnings.join("; "), /parameter mouthOpen has no id/);
  assert.equal(aliases.aliases.mouthOpen.id, "ParamMouthOpenY");
}

function testParameterIdsRemainBackwardCompatible() {
  assert.equal(getLive2DParameterIds().mouthOpenY, "ParamMouthOpenY");
  assert.equal(getLive2DParameterIds().angleX, "ParamAngleX");
}

testMapperUsesDefaultParameterAliases();
testMapperUsesProfileParameterAliasesRangesAndInvert();
testResolveAliasesReportsMissingParameterWarnings();
testParameterIdsRemainBackwardCompatible();
console.log("live2d-parameter-mapper tests passed");
