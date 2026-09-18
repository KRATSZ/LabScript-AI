import type { ProtocolAnalysisOutput } from '@opentrons/shared-data'

/**
 * Ensures array fields exist so visualization code (step-generation) never hits
 * undefined.reduce / undefined.filter on partial or legacy JSON.
 */
export function normalizeAnalysisOutput(
  input: ProtocolAnalysisOutput
): ProtocolAnalysisOutput {
  return {
    ...input,
    commands: input.commands ?? [],
    errors: input.errors ?? [],
    labware: input.labware ?? [],
    modules: input.modules ?? [],
    pipettes: input.pipettes ?? [],
    liquids: input.liquids ?? [],
    files: input.files ?? [],
    runTimeParameters: input.runTimeParameters ?? [],
  }
}
