function resolveAssetUrl(modelUrl, relativePath) {
  return new URL(relativePath, new URL(modelUrl, window.location.href)).toString();
}

export async function inspectModelPackage(modelUrl) {
  const response = await fetch(modelUrl, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`Model JSON request failed: ${response.status} ${response.statusText}`);
  }

  const model = await response.json();
  const references = model.FileReferences || {};
  const textures = references.Textures || [];
  const motions = references.Motions || {};
  const expressions = Array.isArray(references.Expressions) ? references.Expressions : [];
  const expressionNames = expressions
    .map((entry) => entry?.Name)
    .filter((name) => typeof name === "string" && name.length > 0);
  const motionCount = Object.values(motions).reduce((count, group) => count + group.length, 0);
  const motionGroupCounts = Object.fromEntries(
    Object.entries(motions).map(([group, entries]) => [
      group,
      Array.isArray(entries) ? entries.length : 0
    ])
  );

  return {
    version: model.Version || "unknown",
    moc: references.Moc || "",
    textureCount: textures.length,
    firstTextureUrl: textures[0] ? resolveAssetUrl(modelUrl, textures[0]) : "",
    physics: references.Physics || "",
    pose: references.Pose || "",
    expressionCount: expressions.length,
    expressionNames,
    motionGroups: Object.keys(motions),
    motionGroupCounts,
    motionCount,
    lipSyncIds: findGroupIds(model.Groups, "LipSync"),
    eyeBlinkIds: findGroupIds(model.Groups, "EyeBlink")
  };
}

function findGroupIds(groups = [], name) {
  const group = groups.find((item) => item.Name === name);
  return group ? group.Ids || [] : [];
}
