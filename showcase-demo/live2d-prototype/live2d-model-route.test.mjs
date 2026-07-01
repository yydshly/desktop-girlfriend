import assert from "node:assert/strict";
import {
  resolveModelUrlFromRoute,
  modelIdToModelJsonUrl
} from "./live2d-model-route.js";

function testModelIdToModelJsonUrl() {
  assert.equal(
    modelIdToModelJsonUrl("custom/Xiaoyun"),
    "./assets/models/custom/Xiaoyun/Xiaoyun.model3.json"
  );
  assert.equal(
    modelIdToModelJsonUrl("sample/Hiyori"),
    "./assets/models/sample/Hiyori/Hiyori.model3.json"
  );
}

function testResolveModelUrlFromRouteFallsBackToDefault() {
  assert.equal(
    resolveModelUrlFromRoute(new URLSearchParams("desktop=1"), "./default.model3.json"),
    "./default.model3.json"
  );
}

function testResolveModelUrlFromRouteUsesModelId() {
  assert.equal(
    resolveModelUrlFromRoute(
      new URLSearchParams("desktop=1&model=custom%2FXiaoyun"),
      "./default.model3.json"
    ),
    "./assets/models/custom/Xiaoyun/Xiaoyun.model3.json"
  );
}

testModelIdToModelJsonUrl();
testResolveModelUrlFromRouteFallsBackToDefault();
testResolveModelUrlFromRouteUsesModelId();
console.log("live2d-model-route tests passed");
