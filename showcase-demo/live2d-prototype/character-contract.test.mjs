import assert from "node:assert/strict";
import {
  CHARACTER_CONTRACT_VERSION,
  CANONICAL_CHARACTER_ACTIONS,
  CANONICAL_CHARACTER_EXPRESSIONS,
  CANONICAL_CHARACTER_STATES,
  normalizeCharacterAction,
  normalizeCharacterExpression,
  validateCharacterProfile
} from "./character-contract.js";

function testContractVersionIsStable() {
  assert.equal(CHARACTER_CONTRACT_VERSION, 1);
}

function testContractDefinesStableSemanticStates() {
  assert.deepEqual(CANONICAL_CHARACTER_STATES, [
    "idle",
    "listening",
    "thinking",
    "speaking",
    "happy",
    "sad",
    "comfort",
    "error"
  ]);
}

function testContractDefinesStableSemanticActions() {
  assert.deepEqual(CANONICAL_CHARACTER_ACTIONS, [
    "idle",
    "greet",
    "listen",
    "think",
    "reply",
    "comfort",
    "sad",
    "happy",
    "speak"
  ]);
}

function testContractDefinesStableSemanticExpressions() {
  assert.deepEqual(CANONICAL_CHARACTER_EXPRESSIONS, [
    "neutral",
    "happy",
    "sad",
    "thinking",
    "soft",
    "engaged"
  ]);
}

function testSemanticAliasesNormalizeToContractTerms() {
  assert.equal(normalizeCharacterAction("listening"), "listen");
  assert.equal(normalizeCharacterAction("speaking"), "speak");
  assert.equal(normalizeCharacterAction("unknown", "idle"), "idle");
  assert.equal(normalizeCharacterExpression("think"), "thinking");
  assert.equal(normalizeCharacterExpression("reply"), "engaged");
  assert.equal(normalizeCharacterExpression("missing", "neutral"), "neutral");
}

function testProfileValidationAcceptsMinimumProfileV1() {
  const result = validateCharacterProfile({
    schemaVersion: 1,
    displayName: "Hiyori",
    mappings: {
      actions: {
        idle: { group: "Idle", index: 0 },
        speak: { group: "TapBody", index: 0 }
      },
      expressions: {
        neutral: "default",
        happy: "happy"
      }
    }
  });

  assert.equal(result.valid, true);
  assert.deepEqual(result.errors, []);
  assert.deepEqual(result.warnings, []);
}

function testProfileValidationRejectsBrokenProfile() {
  const result = validateCharacterProfile({
    schemaVersion: 2,
    displayName: "",
    mappings: {
      actions: {
        idle: { group: "", index: -1 },
        wave: { group: "TapBody", index: 0 }
      },
      expressions: {
        wow: "surprised"
      }
    }
  });

  assert.equal(result.valid, false);
  assert.deepEqual(result.errors, [
    "schemaVersion must be 1",
    "displayName is required",
    "mappings.actions.idle.group is required",
    "mappings.actions.idle.index must be a non-negative integer",
    "mappings.actions.wave is not a contract action",
    "mappings.expressions.wow is not a contract expression"
  ]);
}

testContractVersionIsStable();
testContractDefinesStableSemanticStates();
testContractDefinesStableSemanticActions();
testContractDefinesStableSemanticExpressions();
testSemanticAliasesNormalizeToContractTerms();
testProfileValidationAcceptsMinimumProfileV1();
testProfileValidationRejectsBrokenProfile();
console.log("character-contract tests passed");
