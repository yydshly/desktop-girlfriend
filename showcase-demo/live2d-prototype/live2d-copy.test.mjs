import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const html = readFileSync(new URL("./index.html", import.meta.url), "utf8");

function testPrototypePageUsesReadableChineseCopy() {
  [
    "Live2D 主线原型",
    "模型驱动原型",
    "模型资产",
    "设置模型路径",
    "状态控制",
    "待机",
    "开心",
    "思考",
    "动作序列",
    "打招呼",
    "桥接状态",
    "连接",
    "断开"
  ].forEach((text) => {
    assert.ok(html.includes(text), `missing readable copy: ${text}`);
  });
}

function testPrototypePageDoesNotContainKnownMojibakeMarkers() {
  ["涓", "荤", "妯", "璺", "鐘", "鏂", "鎵", "鍔"].forEach((marker) => {
    assert.equal(html.includes(marker), false, `contains mojibake marker: ${marker}`);
  });
}

testPrototypePageUsesReadableChineseCopy();
testPrototypePageDoesNotContainKnownMojibakeMarkers();
console.log("live2d-copy tests passed");
