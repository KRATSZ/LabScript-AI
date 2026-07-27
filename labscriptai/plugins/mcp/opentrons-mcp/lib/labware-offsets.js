import { requestRobotJson } from "./http.js";

function locationSequenceKey(locationSequence) {
  if (locationSequence === "anyLocation" || locationSequence == null) {
    return "anyLocation";
  }
  return JSON.stringify(locationSequence);
}

export function dedupeLabwareOffsets(offsets) {
  const byKey = new Map();
  for (const offset of offsets || []) {
    const definitionUri = offset?.definitionUri;
    if (!definitionUri) {
      continue;
    }
    const key = `${definitionUri}::${locationSequenceKey(offset.locationSequence)}`;
    const existing = byKey.get(key);
    if (
      !existing ||
      new Date(offset.createdAt || 0).getTime() > new Date(existing.createdAt || 0).getTime()
    ) {
      byKey.set(key, offset);
    }
  }
  return [...byKey.values()];
}

export function selectOffsetsForRun(offsets) {
  return dedupeLabwareOffsets(offsets).filter(offset =>
    Array.isArray(offset.locationSequence),
  );
}

export function prepareOffsetsForRunCreate(offsets) {
  return selectOffsetsForRun(offsets).map(offset => ({
    definitionUri: offset.definitionUri,
    locationSequence: offset.locationSequence,
    vector: offset.vector,
  }));
}

export async function fetchRobotLabwareOffsets(robotIp) {
  const response = await requestRobotJson("GET", robotIp, "/labwareOffsets");
  return response?.data ?? [];
}

export async function resolveRunLabwareOffsets(robotIp, explicitOffsets = undefined) {
  if (explicitOffsets !== undefined) {
    const prepared = prepareOffsetsForRunCreate(explicitOffsets);
    return prepared.length > 0 ? prepared : null;
  }
  const offsets = await fetchRobotLabwareOffsets(robotIp);
  const prepared = prepareOffsetsForRunCreate(offsets);
  return prepared.length > 0 ? prepared : null;
}

export function buildProtocolRunCreateBody({
  protocolId,
  runTimeParameters = null,
  labwareOffsets = null,
}) {
  return {
    data: {
      protocolId,
      ...(runTimeParameters ? { runTimeParameterValues: runTimeParameters } : {}),
      ...(labwareOffsets ? { labwareOffsets } : {}),
    },
  };
}
