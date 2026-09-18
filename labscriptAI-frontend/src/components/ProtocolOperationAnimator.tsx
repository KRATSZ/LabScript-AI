import React, {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from 'react';
import {
  Box,
  Button,
  Chip,
  Divider,
  IconButton,
  MenuItem,
  Select,
  Stack,
  Tooltip,
  Typography,
  alpha,
  useTheme,
} from '@mui/material';
import {
  AlertCircle,
  Droplets,
  Pause,
  Play,
  RotateCcw,
  SkipBack,
  SkipForward,
} from 'lucide-react';

import '../../../web/opentrons-protocol-visualizer-web-slim/components/src/styles/global.css';
import '../../../web/opentrons-protocol-visualizer-web-slim/protocol-visualizer-web/client/src/global.css';

import {
  CenterLabwareInSlot,
  COLORS,
  DeckFromLayers,
  FixedTrashText,
  LabwareRender,
  RobotCoordinateSpaceWithRef,
  SingleSlotFixture,
  SlotLabels,
  type WellGroup,
} from '@opentrons/components';
import {
  FLEX_ROBOT_TYPE,
  OT2_ROBOT_TYPE,
  SLOT_RENDER_HEIGHT,
  SLOT_RENDER_WIDTH,
  getAddressableAreaFromSlotId,
  getCutoutIdForAddressableArea,
  getDeckDefFromRobotType,
  getLabwareViewBox,
  getPositionFromSlotId,
  isAddressableAreaStandardSlot,
} from '@opentrons/shared-data';
import {
  constructInvariantContextFromAnalysis,
  getResultingTimelineFrameFromRunCommands,
  getSlotInLocationStack,
  wellFillFromWellContents,
} from '@opentrons/step-generation';

import { getAllWellContentsAtFrame } from '../../../web/opentrons-protocol-visualizer-web-slim/protocol-visualizer-web/client/src/viz/utils/getAllWellContentsAtFrame';
import { getMissingTips } from '../../../web/opentrons-protocol-visualizer-web-slim/protocol-visualizer-web/client/src/viz/utils/getMissingTips';

import type { SelectChangeEvent } from '@mui/material';
import type {
  DeckDefinition,
  LabwareDefinition2,
  Liquid,
  ProtocolAnalysisOutput,
  RobotType,
  RunTimeCommand,
} from '@opentrons/shared-data';
import type {
  InvariantContext,
  RobotState,
} from '@opentrons/step-generation';

export interface DeckTarget {
  x: number;
  y: number;
  z: number;
  labwareId?: string;
  wellName?: string;
  slotName?: string;
  label?: string;
}

type AnimationEffect =
  | 'move'
  | 'pickup-tip'
  | 'drop-tip'
  | 'aspirate'
  | 'dispense'
  | 'air-gap'
  | 'blowout'
  | 'touch-tip'
  | 'labware'
  | 'module'
  | 'hold';

export interface AnimationEvent {
  id: string;
  commandId: string;
  commandType: string;
  label: string;
  startMs: number;
  endMs: number;
  pipetteId?: string;
  target?: DeckTarget;
  volume?: number;
  effect: AnimationEffect;
}

export interface AnimationPlaybackState {
  currentMs: number;
  durationMs: number;
  activeEventIndex: number;
  isPlaying: boolean;
  speed: number;
}

interface ProtocolOperationAnimatorProps {
  analysisOutput: ProtocolAnalysisOutput;
}

type Point2D = Pick<DeckTarget, 'x' | 'y' | 'z'>;

const SETUP_COMMAND_TYPES = new Set([
  'loadPipette',
  'loadLabware',
  'loadModule',
  'loadLiquid',
  'loadLiquidClass',
  'loadLid',
  'loadLidStack',
  'reloadLabware',
  'setTipState',
  'configureNozzleLayout',
  'home',
]);

const COMMAND_EFFECTS: Record<string, AnimationEffect> = {
  pickUpTip: 'pickup-tip',
  dropTip: 'drop-tip',
  dropTipInPlace: 'drop-tip',
  moveToWell: 'move',
  moveToSlot: 'move',
  moveToCoordinates: 'move',
  moveToAddressableArea: 'move',
  moveToAddressableAreaForDropTip: 'move',
  moveRelative: 'move',
  aspirate: 'aspirate',
  aspirateInPlace: 'aspirate',
  aspirateWhileTracking: 'aspirate',
  dispense: 'dispense',
  dispenseInPlace: 'dispense',
  dispenseWhileTracking: 'dispense',
  airGapInPlace: 'air-gap',
  blowout: 'blowout',
  blowOutInPlace: 'blowout',
  touchTip: 'touch-tip',
  moveLabware: 'labware',
};

const EFFECT_LABELS: Record<AnimationEffect, string> = {
  move: 'Move',
  'pickup-tip': 'Pick up tip',
  'drop-tip': 'Drop tip',
  aspirate: 'Aspirate',
  dispense: 'Dispense',
  'air-gap': 'Air gap',
  blowout: 'Blowout',
  'touch-tip': 'Touch tip',
  labware: 'Move labware',
  module: 'Module',
  hold: 'Hold',
};

const EFFECT_COLORS: Record<AnimationEffect, string> = {
  move: '#2563eb',
  'pickup-tip': '#0f766e',
  'drop-tip': '#64748b',
  aspirate: '#0891b2',
  dispense: '#7c3aed',
  'air-gap': '#475569',
  blowout: '#ea580c',
  'touch-tip': '#be123c',
  labware: '#16a34a',
  module: '#9333ea',
  hold: '#64748b',
};

const OT2_STANDARD_DECK_VIEW_LAYER_BLOCK_LIST = [
  'calibrationMarkings',
  'fixedBase',
  'doorStops',
  'metalFrame',
  'removalHandle',
  'removableDeckOutline',
  'screwHoles',
  'fixedTrash',
];

const clamp = (value: number, min: number, max: number): number =>
  Math.min(max, Math.max(min, value));

const easeInOut = (value: number): number =>
  value < 0.5 ? 2 * value * value : 1 - Math.pow(-2 * value + 2, 2) / 2;

const readString = (
  params: Record<string, unknown>,
  key: string
): string | undefined => {
  const value = params[key];
  return typeof value === 'string' ? value : undefined;
};

const readNumber = (
  params: Record<string, unknown>,
  key: string
): number | undefined => {
  const value = params[key];
  return typeof value === 'number' && Number.isFinite(value) ? value : undefined;
};

const getCommandParams = (command: RunTimeCommand): Record<string, unknown> =>
  command.params as Record<string, unknown>;

const getAnalysisErrorMessage = (
  analysisOutput: ProtocolAnalysisOutput
): string | null => {
  const error = analysisOutput.errors[0];
  if (error == null) return null;
  return error.detail || error.errorType || 'Protocol analysis failed.';
};

function getEventIndexAtTime(events: AnimationEvent[], currentMs: number): number {
  if (events.length === 0) return -1;
  const index = events.findIndex(
    event => currentMs >= event.startMs && currentMs < event.endMs
  );
  return index >= 0 ? index : events.length - 1;
}

function createPlaybackState(
  currentMs: number,
  isPlaying: boolean,
  speed: number,
  events: AnimationEvent[]
): AnimationPlaybackState {
  const durationMs = events[events.length - 1]?.endMs ?? 0;
  const safeMs = clamp(currentMs, 0, durationMs);
  return {
    currentMs: safeMs,
    durationMs,
    activeEventIndex: getEventIndexAtTime(events, safeMs),
    isPlaying: isPlaying && safeMs < durationMs,
    speed,
  };
}

function precomputeRobotStates(
  commands: RunTimeCommand[],
  invariantContext: InvariantContext
): Map<string, RobotState> {
  const states = new Map<string, RobotState>();
  for (let i = 0; i < commands.length; i += 1) {
    const { frame } = getResultingTimelineFrameFromRunCommands(
      commands.slice(0, i + 1),
      invariantContext
    );
    states.set(commands[i].id, frame.robotState);
  }
  return states;
}

function getLabwareOrigin(
  labwareId: string,
  robotState: RobotState,
  invariantContext: InvariantContext,
  deckDef: DeckDefinition
): Point2D | null {
  const labwareState = robotState.labware[labwareId];
  const labwareEntity = invariantContext.labwareEntities[labwareId];
  if (labwareState == null || labwareEntity == null) return null;

  const slotName = getSlotInLocationStack(labwareState.stack);
  const slotPosition = getPositionFromSlotId(slotName, deckDef);
  if (slotPosition == null) return null;

  const { minX, minY, maxX, maxY } = getLabwareViewBox(labwareEntity.def);
  return {
    x: slotPosition[0] + SLOT_RENDER_WIDTH / 2 - (minX + maxX) / 2,
    y: slotPosition[1] + SLOT_RENDER_HEIGHT / 2 - (minY + maxY) / 2,
    z: slotPosition[2],
  };
}

function getWellTarget(
  labwareId: string,
  wellName: string,
  robotState: RobotState,
  invariantContext: InvariantContext,
  deckDef: DeckDefinition
): DeckTarget | null {
  const labwareEntity = invariantContext.labwareEntities[labwareId];
  const well = labwareEntity?.def.wells[wellName];
  const origin = getLabwareOrigin(labwareId, robotState, invariantContext, deckDef);
  if (labwareEntity == null || well == null || origin == null) return null;

  const slotName = getSlotInLocationStack(robotState.labware[labwareId].stack);
  return {
    x: origin.x + well.x,
    y: origin.y + well.y,
    z: origin.z + well.z,
    labwareId,
    wellName,
    slotName,
    label: `${labwareEntity.def.metadata.displayName} ${wellName}`,
  };
}

function getSlotTarget(slotName: string, deckDef: DeckDefinition): DeckTarget | null {
  const slotPosition = getPositionFromSlotId(slotName, deckDef);
  const slotArea = getAddressableAreaFromSlotId(slotName, deckDef);
  if (slotPosition == null) return null;

  return {
    x: slotPosition[0] + (slotArea?.boundingBox.xDimension ?? SLOT_RENDER_WIDTH) / 2,
    y: slotPosition[1] + (slotArea?.boundingBox.yDimension ?? SLOT_RENDER_HEIGHT) / 2,
    z: slotPosition[2],
    slotName,
    label: slotArea?.displayName ?? `Slot ${slotName}`,
  };
}

function getAddressableAreaTarget(
  addressableAreaName: string,
  deckDef: DeckDefinition
): DeckTarget | null {
  const area = getAddressableAreaFromSlotId(addressableAreaName, deckDef);
  if (area == null) return null;

  const directPosition = getPositionFromSlotId(addressableAreaName, deckDef);
  const cutoutId = getCutoutIdForAddressableArea(
    addressableAreaName,
    deckDef.cutoutFixtures
  );
  const cutoutPosition =
    cutoutId != null
      ? deckDef.locations.cutouts.find(cutout => cutout.id === cutoutId)
          ?.position
      : null;
  const position =
    directPosition ??
    (cutoutPosition != null
      ? ([
          cutoutPosition[0] + area.offsetFromCutoutFixture[0],
          cutoutPosition[1] + area.offsetFromCutoutFixture[1],
          cutoutPosition[2] + area.offsetFromCutoutFixture[2],
        ] as const)
      : null);
  if (position == null) return null;

  return {
    x: position[0] + area.boundingBox.xDimension / 2,
    y: position[1] + area.boundingBox.yDimension / 2,
    z: position[2],
    slotName: addressableAreaName,
    label: area.displayName,
  };
}

function getPipetteTargetFromState(
  pipetteId: string | undefined,
  robotState: RobotState,
  invariantContext: InvariantContext,
  deckDef: DeckDefinition
): DeckTarget | null {
  if (pipetteId == null) return null;
  const pipette = robotState.pipettes[pipetteId];
  if (pipette?.entityId == null) return null;

  if (pipette.wellName != null) {
    return getWellTarget(
      pipette.entityId,
      pipette.wellName,
      robotState,
      invariantContext,
      deckDef
    );
  }

  const labwareOrigin = getLabwareOrigin(
    pipette.entityId,
    robotState,
    invariantContext,
    deckDef
  );
  if (labwareOrigin == null) return null;
  return {
    ...labwareOrigin,
    labwareId: pipette.entityId,
    label: invariantContext.labwareEntities[pipette.entityId]?.def.metadata.displayName,
  };
}

function getCommandTarget(
  command: RunTimeCommand,
  robotState: RobotState,
  invariantContext: InvariantContext,
  deckDef: DeckDefinition
): DeckTarget | null {
  const params = getCommandParams(command);
  const labwareId = readString(params, 'labwareId');
  const wellName = readString(params, 'wellName');
  const slotName = readString(params, 'slotName');
  const addressableAreaName = readString(params, 'addressableAreaName');
  const pipetteId = readString(params, 'pipetteId');
  const coordinates = params.coordinates;

  if (labwareId != null && wellName != null) {
    return getWellTarget(labwareId, wellName, robotState, invariantContext, deckDef);
  }

  if (slotName != null) {
    return getSlotTarget(slotName, deckDef);
  }

  if (addressableAreaName != null) {
    return getAddressableAreaTarget(addressableAreaName, deckDef);
  }

  if (
    coordinates != null &&
    typeof coordinates === 'object' &&
    'x' in coordinates &&
    'y' in coordinates &&
    'z' in coordinates
  ) {
    const point = coordinates as Record<string, unknown>;
    if (
      typeof point.x === 'number' &&
      typeof point.y === 'number' &&
      typeof point.z === 'number'
    ) {
      return {
        x: point.x,
        y: point.y,
        z: point.z,
        label: 'Deck coordinates',
      };
    }
  }

  return getPipetteTargetFromState(pipetteId, robotState, invariantContext, deckDef);
}

function getEffect(commandType: string): AnimationEffect {
  if (COMMAND_EFFECTS[commandType] != null) return COMMAND_EFFECTS[commandType];
  if (commandType.includes('Module') || commandType.includes('/')) return 'module';
  return 'hold';
}

function getDurationMs(command: RunTimeCommand, effect: AnimationEffect): number {
  const params = getCommandParams(command);
  const volume = readNumber(params, 'volume') ?? 0;

  if (effect === 'aspirate' || effect === 'dispense') {
    return clamp(900 + volume * 4, 1000, 2400);
  }
  if (effect === 'move') return 1100;
  if (effect === 'pickup-tip' || effect === 'drop-tip') return 1300;
  if (effect === 'touch-tip') return 900;
  if (effect === 'labware' || effect === 'module') return 1400;
  return 850;
}

function formatCommandLabel(
  command: RunTimeCommand,
  target: DeckTarget | null,
  effect: AnimationEffect
): string {
  const params = getCommandParams(command);
  const volume = readNumber(params, 'volume');
  const targetLabel = target?.wellName ?? target?.slotName ?? target?.label;
  const volumeLabel = volume != null ? ` ${volume} uL` : '';

  if (targetLabel != null) {
    return `${EFFECT_LABELS[effect]}${volumeLabel} at ${targetLabel}`;
  }

  return `${EFFECT_LABELS[effect]}${volumeLabel}`;
}

function buildAnimationEvents(
  commands: RunTimeCommand[],
  robotStateMap: Map<string, RobotState>,
  invariantContext: InvariantContext,
  deckDef: DeckDefinition
): AnimationEvent[] {
  const events: AnimationEvent[] = [];
  const lastTargetByPipette = new Map<string, DeckTarget>();
  let cursorMs = 0;

  commands.forEach(command => {
    if (
      typeof command.commandType !== 'string' ||
      SETUP_COMMAND_TYPES.has(command.commandType)
    ) {
      return;
    }

    const robotState = robotStateMap.get(command.id);
    if (robotState == null) return;

    const params = getCommandParams(command);
    const pipetteId = readString(params, 'pipetteId');
    const effect = getEffect(command.commandType);
    const target =
      getCommandTarget(command, robotState, invariantContext, deckDef) ??
      (pipetteId != null ? lastTargetByPipette.get(pipetteId) ?? null : null);
    const durationMs = getDurationMs(command, effect);

    events.push({
      id: `${command.id}-${events.length}`,
      commandId: command.id,
      commandType: command.commandType,
      label: formatCommandLabel(command, target, effect),
      startMs: cursorMs,
      endMs: cursorMs + durationMs,
      pipetteId,
      target: target ?? undefined,
      volume: readNumber(params, 'volume'),
      effect,
    });
    if (pipetteId != null && target != null) {
      lastTargetByPipette.set(pipetteId, target);
    }
    cursorMs += durationMs;
  });

  return events;
}

function interpolatePoint(
  from: DeckTarget | undefined,
  to: DeckTarget | undefined,
  progress: number
): DeckTarget | undefined {
  if (from == null && to == null) return undefined;
  if (from == null) return to;
  if (to == null) return from;

  const eased = easeInOut(progress);
  return {
    ...to,
    x: from.x + (to.x - from.x) * eased,
    y: from.y + (to.y - from.y) * eased,
    z: from.z + (to.z - from.z) * eased,
  };
}

function findPreviousTarget(
  events: AnimationEvent[],
  activeIndex: number,
  pipetteId?: string
): DeckTarget | undefined {
  for (let i = activeIndex - 1; i >= 0; i -= 1) {
    const event = events[i];
    if (
      event.target != null &&
      (pipetteId == null || event.pipetteId == null || event.pipetteId === pipetteId)
    ) {
      return event.target;
    }
  }
  return undefined;
}

function formatElapsed(currentMs: number, durationMs: number): string {
  const currentSeconds = Math.round(currentMs / 1000);
  const durationSeconds = Math.round(durationMs / 1000);
  return `${currentSeconds}s / ${durationSeconds}s`;
}

function getCurrentRobotState(
  events: AnimationEvent[],
  commands: RunTimeCommand[],
  robotStateMap: Map<string, RobotState>,
  activeEventIndex: number
): RobotState | null {
  const activeCommandId = events[activeEventIndex]?.commandId;
  if (activeCommandId != null) {
    const state = robotStateMap.get(activeCommandId);
    if (state != null) return state;
  }

  const lastCommand = commands[commands.length - 1];
  return lastCommand != null ? robotStateMap.get(lastCommand.id) ?? null : null;
}

interface DeckSceneProps {
  activeEvent?: AnimationEvent;
  activeTarget?: DeckTarget;
  deckDef: DeckDefinition;
  invariantContext: InvariantContext;
  liquids: Liquid[];
  robotState: RobotState;
  robotType: RobotType;
}

const DeckScene: React.FC<DeckSceneProps> = ({
  activeEvent,
  activeTarget,
  deckDef,
  invariantContext,
  liquids,
  robotState,
  robotType,
}) => {
  const { labware, liquidState, tipState } = robotState;
  const { labwareEntities } = invariantContext;
  const liquidDisplayColors = useMemo(
    () => Object.fromEntries(liquids.map(liquid => [liquid.id, liquid.displayColor ?? COLORS.blue35])),
    [liquids]
  );
  const viewBox = `${deckDef.cornerOffsetFromOrigin[0]} ${deckDef.cornerOffsetFromOrigin[1]} ${deckDef.dimensions[0]} ${deckDef.dimensions[1]}`;

  return (
    <Box
      data-testid="protocol-operation-deck"
      sx={{
        position: 'relative',
        display: 'flex',
        height: '100%',
        minHeight: 360,
        overflow: 'hidden',
        bgcolor: '#f8fafc',
        '& > svg': {
          width: '100%',
          height: '100%',
        },
      }}
    >
      <RobotCoordinateSpaceWithRef
        deckDef={deckDef}
        height="100%"
        width="100%"
        viewBox={viewBox}
        zoomed
      >
        {() => (
          <>
            {robotType === OT2_ROBOT_TYPE ? (
              <>
                <DeckFromLayers
                  robotType={robotType}
                  layerBlocklist={OT2_STANDARD_DECK_VIEW_LAYER_BLOCK_LIST}
                />
                <FixedTrashText />
              </>
            ) : (
              <>
                {deckDef.locations.addressableAreas.map(addressableArea => {
                  if (!isAddressableAreaStandardSlot(addressableArea.id, deckDef)) {
                    return null;
                  }
                  const cutoutId = getCutoutIdForAddressableArea(
                    addressableArea.id,
                    deckDef.cutoutFixtures
                  );
                  return cutoutId != null ? (
                    <SingleSlotFixture
                      key={addressableArea.id}
                      cutoutId={cutoutId}
                      deckDefinition={deckDef}
                      fixtureBaseColor={COLORS.grey35}
                      showExpansion={cutoutId === 'cutoutA1'}
                      slotClipColor={COLORS.grey60}
                    />
                  ) : null;
                })}
              </>
            )}

            {Object.entries(labware).map(([labwareId, labwareState]) => {
              const labwareEntity = labwareEntities[labwareId];
              const slotName = getSlotInLocationStack(labwareState.stack);
              const slotPosition = getPositionFromSlotId(slotName, deckDef);
              if (labwareEntity == null || slotPosition == null) return null;

              const wellContents =
                getAllWellContentsAtFrame(
                  liquidState,
                  labwareEntity.def as LabwareDefinition2
                )[labwareId] ?? null;
              const missingTips = getMissingTips(tipState, labwareId);
              const highlightedWells: WellGroup =
                activeEvent?.target?.labwareId === labwareId &&
                activeEvent.target.wellName != null
                  ? { [activeEvent.target.wellName]: null }
                  : {};
              return (
                <g
                  key={labwareId}
                  transform={`translate(${slotPosition[0]}, ${slotPosition[1]})`}
                >
                  <CenterLabwareInSlot definition={labwareEntity.def}>
                    <LabwareRender
                      positioningMode="passThrough"
                      definition={labwareEntity.def}
                      highlightedWells={highlightedWells}
                      missingTips={missingTips}
                      wellFill={
                        wellContents != null
                          ? wellFillFromWellContents(wellContents, liquidDisplayColors)
                          : undefined
                      }
                    />
                  </CenterLabwareInSlot>
                </g>
              );
            })}

            {activeTarget != null && (
              <g transform={`translate(${activeTarget.x}, ${activeTarget.y})`}>
                <circle
                  r="13"
                  fill={activeEvent != null ? EFFECT_COLORS[activeEvent.effect] : '#2563eb'}
                  opacity="0.18"
                />
                <circle
                  r="6"
                  fill={activeEvent != null ? EFFECT_COLORS[activeEvent.effect] : '#2563eb'}
                />
                <path
                  d="M -10 -18 L 10 -18 L 4 -2 L -4 -2 Z"
                  fill="#0f172a"
                  opacity="0.92"
                />
              </g>
            )}

            <SlotLabels robotType={robotType} show4thColumn={false} />
          </>
        )}
      </RobotCoordinateSpaceWithRef>
    </Box>
  );
};

const ProtocolOperationAnimator: React.FC<ProtocolOperationAnimatorProps> = ({
  analysisOutput,
}) => {
  const theme = useTheme();
  const { commands, liquids, robotType = FLEX_ROBOT_TYPE } = analysisOutput;

  const createdDate = useMemo(
    () => new Date(analysisOutput.createdAt),
    [analysisOutput.createdAt]
  );
  const invariantContext = useMemo(
    () =>
      constructInvariantContextFromAnalysis(
        analysisOutput,
        analysisOutput.config,
        createdDate
      ),
    [analysisOutput, createdDate]
  );
  const deckDef = useMemo(
    () => getDeckDefFromRobotType(robotType),
    [robotType]
  );
  const robotStateMap = useMemo(
    () => precomputeRobotStates(commands, invariantContext),
    [commands, invariantContext]
  );
  const events = useMemo(
    () => buildAnimationEvents(commands, robotStateMap, invariantContext, deckDef),
    [commands, deckDef, invariantContext, robotStateMap]
  );
  const [playback, setPlayback] = useState<AnimationPlaybackState>(() =>
    createPlaybackState(0, false, 1, events)
  );
  const rafRef = useRef<number | null>(null);
  const lastTickRef = useRef<number | null>(null);

  useEffect(() => {
    setPlayback(prev => createPlaybackState(0, false, prev.speed, events));
  }, [events]);

  const activeEvent = events[playback.activeEventIndex];
  const activeProgress =
    activeEvent != null && activeEvent.endMs > activeEvent.startMs
      ? clamp(
          (playback.currentMs - activeEvent.startMs) /
            (activeEvent.endMs - activeEvent.startMs),
          0,
          1
        )
      : 0;
  const activeTarget = useMemo(
    () =>
      interpolatePoint(
        findPreviousTarget(events, playback.activeEventIndex, activeEvent?.pipetteId),
        activeEvent?.target,
        activeProgress
      ),
    [activeEvent, activeProgress, events, playback.activeEventIndex]
  );
  const robotState = useMemo(
    () =>
      getCurrentRobotState(
        events,
        commands,
        robotStateMap,
        playback.activeEventIndex
      ),
    [commands, events, playback.activeEventIndex, robotStateMap]
  );

  useEffect(() => {
    if (!playback.isPlaying) {
      lastTickRef.current = null;
      return undefined;
    }

    const tick = (timestamp: number): void => {
      const previous = lastTickRef.current ?? timestamp;
      lastTickRef.current = timestamp;
      const delta = (timestamp - previous) * playback.speed;
      setPlayback(prev =>
        createPlaybackState(
          prev.currentMs + delta,
          prev.currentMs + delta < prev.durationMs,
          prev.speed,
          events
        )
      );
      rafRef.current = window.requestAnimationFrame(tick);
    };

    rafRef.current = window.requestAnimationFrame(tick);
    return () => {
      if (rafRef.current != null) {
        window.cancelAnimationFrame(rafRef.current);
      }
      lastTickRef.current = null;
    };
  }, [events, playback.isPlaying, playback.speed]);

  const setCurrentMs = useCallback(
    (currentMs: number, isPlaying = false) => {
      setPlayback(prev =>
        createPlaybackState(currentMs, isPlaying, prev.speed, events)
      );
    },
    [events]
  );

  const togglePlayback = (): void => {
    setPlayback(prev => {
      const restartAtEnd = prev.currentMs >= prev.durationMs;
      return createPlaybackState(
        restartAtEnd ? 0 : prev.currentMs,
        !prev.isPlaying,
        prev.speed,
        events
      );
    });
  };

  const stepBy = (delta: number): void => {
    const nextIndex = clamp(
      playback.activeEventIndex + delta,
      0,
      Math.max(events.length - 1, 0)
    );
    setCurrentMs(events[nextIndex]?.startMs ?? 0, false);
  };

  const handleSpeedChange = (event: SelectChangeEvent<number>): void => {
    const nextSpeed = Number(event.target.value);
    setPlayback(prev =>
      createPlaybackState(prev.currentMs, prev.isPlaying, nextSpeed, events)
    );
  };

  const handleProgressInput = (
    event: React.ChangeEvent<HTMLInputElement> | React.FormEvent<HTMLInputElement>
  ): void => {
    setCurrentMs(Number(event.currentTarget.value), false);
  };

  const progressPercent =
    playback.durationMs > 0
      ? clamp((playback.currentMs / playback.durationMs) * 100, 0, 100)
      : 0;
  const analysisErrorMessage = getAnalysisErrorMessage(analysisOutput);

  if (analysisErrorMessage != null && (robotState == null || events.length === 0)) {
    return (
      <Stack
        spacing={2}
        alignItems="center"
        justifyContent="center"
        sx={{ height: '100%', p: 4, textAlign: 'center' }}
      >
        <AlertCircle size={28} color={theme.palette.error.main} />
        <Typography variant="h6" sx={{ fontWeight: 700 }}>
          Protocol analysis stopped before playback could be built.
        </Typography>
        <Typography
          variant="body2"
          color="text.secondary"
          sx={{ maxWidth: 760, whiteSpace: 'pre-wrap' }}
        >
          {analysisErrorMessage}
        </Typography>
      </Stack>
    );
  }

  if (commands.length === 0) {
    return (
      <Stack
        spacing={2}
        alignItems="center"
        justifyContent="center"
        sx={{ height: '100%', p: 4, textAlign: 'center' }}
      >
        <AlertCircle size={28} color={theme.palette.info.main} />
        <Typography variant="h6" sx={{ fontWeight: 700 }}>
          No protocol commands are available yet.
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Generate or paste an Opentrons protocol before opening the animation
          preview.
        </Typography>
      </Stack>
    );
  }

  if (robotState == null || events.length === 0) {
    return (
      <Stack
        spacing={2}
        alignItems="center"
        justifyContent="center"
        sx={{ height: '100%', p: 4, textAlign: 'center' }}
      >
        <AlertCircle size={28} color={theme.palette.warning.main} />
        <Typography variant="h6" sx={{ fontWeight: 700 }}>
          No playable Opentrons operations were found.
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Setup commands were analyzed, but no liquid-handling or motion commands
          were available for animation.
        </Typography>
      </Stack>
    );
  }

  return (
    <Box
      data-testid="protocol-operation-animator"
      sx={{
        display: 'grid',
        gridTemplateRows: 'minmax(0, 1fr) auto',
        height: '100%',
        minHeight: 0,
        bgcolor: '#f8fafc',
        '@keyframes liquidPulse': {
          '0%': { transform: 'translateY(0)', opacity: 0.35 },
          '50%': { transform: 'translateY(-8px)', opacity: 1 },
          '100%': { transform: 'translateY(0)', opacity: 0.35 },
        },
      }}
    >
      <Box
        sx={{
          display: 'grid',
          gridTemplateColumns: {
            xs: '1fr',
            lg: 'minmax(620px, 1fr) minmax(320px, 360px)',
            xl: 'minmax(760px, 1fr) minmax(340px, 380px)',
          },
          minHeight: 0,
        }}
      >
        <DeckScene
          activeEvent={activeEvent}
          activeTarget={activeTarget}
          deckDef={deckDef}
          invariantContext={invariantContext}
          liquids={liquids}
          robotState={robotState}
          robotType={robotType}
        />

        <Box
          sx={{
            display: 'flex',
            flexDirection: 'column',
            gap: 2,
            minHeight: 0,
            borderLeft: { lg: `1px solid ${alpha('#0f172a', 0.08)}` },
            borderTop: { xs: `1px solid ${alpha('#0f172a', 0.08)}`, lg: 'none' },
            bgcolor: '#ffffff',
            p: { xs: 2, lg: 2.5 },
          }}
        >
          <Stack spacing={1.25}>
            <Stack direction="row" alignItems="center" spacing={1}>
              <Chip
                size="small"
                label={activeEvent != null ? EFFECT_LABELS[activeEvent.effect] : 'Idle'}
                sx={{
                  bgcolor:
                    activeEvent != null
                      ? alpha(EFFECT_COLORS[activeEvent.effect], 0.12)
                      : alpha(theme.palette.text.secondary, 0.1),
                  color:
                    activeEvent != null
                      ? EFFECT_COLORS[activeEvent.effect]
                      : theme.palette.text.secondary,
                  fontWeight: 700,
                }}
              />
              <Typography variant="caption" color="text.secondary">
                {playback.activeEventIndex + 1} / {events.length}
              </Typography>
            </Stack>
            <Typography variant="h6" sx={{ fontWeight: 800, lineHeight: 1.25 }}>
              {activeEvent?.label ?? 'Ready'}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {activeEvent?.commandType ?? 'protocol'} ·{' '}
              {formatElapsed(playback.currentMs, playback.durationMs)}
            </Typography>
          </Stack>

          <Divider />

          <Stack spacing={1.5}>
            <Typography variant="subtitle2" sx={{ fontWeight: 800 }}>
              Motion
            </Typography>
            <Box
              sx={{
                position: 'relative',
                minHeight: 92,
                borderRadius: 1,
                border: `1px solid ${alpha('#0f172a', 0.08)}`,
                bgcolor: '#f8fafc',
                p: 2,
                overflow: 'hidden',
              }}
            >
              <Stack direction="row" alignItems="center" spacing={1.25}>
                <Droplets
                  size={24}
                  color={
                    activeEvent != null
                      ? EFFECT_COLORS[activeEvent.effect]
                      : theme.palette.text.secondary
                  }
                />
                <Box>
                  <Typography variant="body2" sx={{ fontWeight: 700 }}>
                    {activeEvent?.target?.label ??
                      activeEvent?.target?.wellName ??
                      activeEvent?.target?.slotName ??
                      'Deck position'}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    {activeEvent?.volume != null
                      ? `${activeEvent.volume} uL`
                      : activeEvent?.pipetteId ?? 'No volume change'}
                  </Typography>
                </Box>
              </Stack>
              {(activeEvent?.effect === 'aspirate' ||
                activeEvent?.effect === 'dispense') && (
                <Box
                  sx={{
                    position: 'absolute',
                    right: 24,
                    bottom: 18,
                    width: 14,
                    height: 24,
                    borderRadius: '50% 50% 55% 55%',
                    bgcolor: EFFECT_COLORS[activeEvent.effect],
                    animation: 'liquidPulse 1.1s ease-in-out infinite',
                    transform:
                      activeEvent.effect === 'aspirate'
                        ? 'rotate(180deg)'
                        : 'rotate(0deg)',
                  }}
                />
              )}
            </Box>
          </Stack>

          <Divider />

          <Box sx={{ minHeight: 0, overflow: 'auto' }}>
            <Stack spacing={1}>
              {events
                .slice(
                  Math.max(0, playback.activeEventIndex - 3),
                  Math.min(events.length, playback.activeEventIndex + 5)
                )
                .map(event => {
                  const isActive = event.id === activeEvent?.id;
                  return (
                    <Button
                      key={event.id}
                      variant={isActive ? 'contained' : 'text'}
                      onClick={() => setCurrentMs(event.startMs, false)}
                      sx={{
                        justifyContent: 'flex-start',
                        minHeight: 36,
                        borderRadius: 1,
                        px: 1.25,
                        textAlign: 'left',
                        color: isActive ? '#fff' : 'text.primary',
                        bgcolor: isActive
                          ? EFFECT_COLORS[event.effect]
                          : 'transparent',
                        '&:hover': {
                          bgcolor: isActive
                            ? EFFECT_COLORS[event.effect]
                            : alpha(EFFECT_COLORS[event.effect], 0.08),
                        },
                      }}
                    >
                      <Typography variant="caption" noWrap>
                        {event.label}
                      </Typography>
                    </Button>
                  );
                })}
            </Stack>
          </Box>
        </Box>
      </Box>

      <Box
        sx={{
          borderTop: `1px solid ${alpha('#0f172a', 0.1)}`,
          bgcolor: '#ffffff',
          p: 2,
        }}
      >
        <Stack spacing={1.5}>
          <Box
            component="input"
            type="range"
            min={0}
            max={playback.durationMs}
            step={1}
            value={playback.currentMs}
            aria-label="Animation progress"
            onChange={handleProgressInput}
            onInput={handleProgressInput}
            sx={{
              width: '100%',
              height: 12,
              m: 0,
              borderRadius: 999,
              appearance: 'none',
              cursor: 'pointer',
              background: `linear-gradient(to right, ${theme.palette.primary.main} 0%, ${theme.palette.primary.main} ${progressPercent}%, #d7dee8 ${progressPercent}%, #d7dee8 100%)`,
              '&::-webkit-slider-thumb': {
                width: 22,
                height: 22,
                border: '3px solid #fff',
                borderRadius: '50%',
                appearance: 'none',
                bgcolor: theme.palette.primary.main,
                boxShadow: '0 3px 10px rgba(37, 99, 235, 0.35)',
              },
              '&::-moz-range-thumb': {
                width: 22,
                height: 22,
                border: '3px solid #fff',
                borderRadius: '50%',
                bgcolor: theme.palette.primary.main,
                boxShadow: '0 3px 10px rgba(37, 99, 235, 0.35)',
              },
            }}
          />

          <Stack
            direction="row"
            alignItems="center"
            justifyContent="space-between"
            spacing={2}
            sx={{ flexWrap: 'wrap', rowGap: 1.5 }}
          >
            <Stack direction="row" alignItems="center" spacing={1}>
              <Tooltip title="Restart">
                <span>
                  <IconButton
                    size="small"
                    onClick={() => setCurrentMs(0, false)}
                    disabled={playback.currentMs === 0}
                    aria-label="Restart animation"
                  >
                    <RotateCcw size={18} />
                  </IconButton>
                </span>
              </Tooltip>
              <Tooltip title="Previous operation">
                <span>
                  <IconButton
                    size="small"
                    onClick={() => stepBy(-1)}
                    disabled={playback.activeEventIndex <= 0}
                    aria-label="Previous operation"
                  >
                    <SkipBack size={18} />
                  </IconButton>
                </span>
              </Tooltip>
              <IconButton
                onClick={togglePlayback}
                aria-label={playback.isPlaying ? 'Pause animation' : 'Play animation'}
                sx={{
                  width: 42,
                  height: 42,
                  bgcolor: theme.palette.primary.main,
                  color: '#fff',
                  '&:hover': { bgcolor: theme.palette.primary.dark },
                }}
              >
                {playback.isPlaying ? <Pause size={20} /> : <Play size={20} />}
              </IconButton>
              <Tooltip title="Next operation">
                <span>
                  <IconButton
                    size="small"
                    onClick={() => stepBy(1)}
                    disabled={playback.activeEventIndex >= events.length - 1}
                    aria-label="Next operation"
                  >
                    <SkipForward size={18} />
                  </IconButton>
                </span>
              </Tooltip>
            </Stack>

            <Stack direction="row" alignItems="center" spacing={1.5}>
              <Typography variant="body2" color="text.secondary">
                {Math.round(progressPercent)}%
              </Typography>
              <Select<number>
                size="small"
                value={playback.speed}
                onChange={handleSpeedChange}
                sx={{ minWidth: 92 }}
              >
                <MenuItem value={0.5}>0.5x</MenuItem>
                <MenuItem value={1}>1x</MenuItem>
                <MenuItem value={1.5}>1.5x</MenuItem>
                <MenuItem value={2}>2x</MenuItem>
              </Select>
            </Stack>
          </Stack>
        </Stack>
      </Box>
    </Box>
  );
};

export default ProtocolOperationAnimator;
