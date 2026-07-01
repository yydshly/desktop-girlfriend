export const CHARACTER_CONTRACT_VERSION = 1;

export const CANONICAL_CHARACTER_STATES = Object.freeze([
  "idle",
  "listening",
  "thinking",
  "speaking",
  "happy",
  "sad",
  "comfort",
  "error"
]);

export const CANONICAL_CHARACTER_ACTIONS = Object.freeze([
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

export const CANONICAL_CHARACTER_EXPRESSIONS = Object.freeze([
  "neutral",
  "happy",
  "sad",
  "thinking",
  "soft",
  "engaged"
]);

const ACTION_ALIASES = Object.freeze({
  listening: "listen",
  thinking: "think",
  speaking: "speak"
});

const EXPRESSION_ALIASES = Object.freeze({
  think: "thinking",
  reply: "engaged",
  comfort: "soft"
});

const ACTION_SET = new Set(CANONICAL_CHARACTER_ACTIONS);
const EXPRESSION_SET = new Set(CANONICAL_CHARACTER_EXPRESSIONS);

export function normalizeCharacterAction(action, fallback = "idle") {
  const value = String(action || "").trim();
  const normalized = ACTION_ALIASES[value] || value;
  return ACTION_SET.has(normalized) ? normalized : fallback;
}

export function normalizeCharacterExpression(expression, fallback = "neutral") {
  const value = String(expression || "").trim();
  const normalized = EXPRESSION_ALIASES[value] || value;
  return EXPRESSION_SET.has(normalized) ? normalized : fallback;
}

export function validateCharacterProfile(profile = {}) {
  const errors = [];
  const warnings = [];

  if (profile.schemaVersion !== CHARACTER_CONTRACT_VERSION) {
    errors.push(`schemaVersion must be ${CHARACTER_CONTRACT_VERSION}`);
  }
  if (typeof profile.displayName !== "string" || !profile.displayName.trim()) {
    errors.push("displayName is required");
  }

  const mappings = profile.mappings || {};
  validateActionMappings(mappings.actions || {}, errors);
  validateExpressionMappings(mappings.expressions || {}, errors);

  return {
    valid: errors.length === 0,
    errors,
    warnings
  };
}

function validateActionMappings(actions, errors) {
  for (const [action, binding] of Object.entries(actions)) {
    if (!ACTION_SET.has(action)) {
      errors.push(`mappings.actions.${action} is not a contract action`);
      continue;
    }
    if (typeof binding?.group !== "string" || !binding.group.trim()) {
      errors.push(`mappings.actions.${action}.group is required`);
    }
    const index = Number(binding?.index);
    if (!Number.isInteger(index) || index < 0) {
      errors.push(`mappings.actions.${action}.index must be a non-negative integer`);
    }
  }
}

function validateExpressionMappings(expressions, errors) {
  for (const expression of Object.keys(expressions)) {
    if (!EXPRESSION_SET.has(expression)) {
      errors.push(`mappings.expressions.${expression} is not a contract expression`);
    }
  }
}
