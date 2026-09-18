import { useCallback, useEffect, useMemo, useRef, useState } from 'react'

import {
  FLEX_ROBOT_TYPE,
  THERMOCYCLER_MODULE_TYPE,
} from '@opentrons/shared-data'
import {
  constructInvariantContextFromAnalysis,
  getResultingTimelineFrameFromRunCommands,
} from '@opentrons/step-generation'

import { Controls } from '../Controls'
import { DeckView } from '../DeckView'
import { SimpleCommandSteps } from '../SimpleCommandSteps'
import { StepDetailContainer } from '../StepDetailContainer'
import styles from './visualizercontainer.module.css'

import type { MouseEvent } from 'react'
import type {
  ProtocolAnalysisOutput,
  RunTimeCommand,
} from '@opentrons/shared-data'
import type { InvariantContext } from '@opentrons/step-generation'

const INITIAL_MILLISECONDS_PER_FRAME = 2000
const INITIAL_WIDTH_PX = 230
const MIN_CENTER_WIDTH_PX = 148
const MIN_LEFT_COLUMN_WIDTH_PX = 148
const MIN_RIGHT_COLUMN_WIDTH_PX = 172
const MAX_COLUMN_WIDTH_PX = 600
const GUTTER_WIDTH_PX = 16

type ResizableColumn = 'left' | 'right'

export interface VisualizerContainerProps {
  analysisOutput: ProtocolAnalysisOutput
}

/**
 * Pre-compute the robot state after every command in the protocol.
 * Runs once per analysisOutput change (O(n²) total), then playback is O(1) per frame.
 */
function precomputeRobotStates(
  commands: RunTimeCommand[],
  invariantContext: InvariantContext
): Map<string, unknown> {
  const states = new Map<string, unknown>()
  for (let i = 0; i < commands.length; i++) {
    const { frame } = getResultingTimelineFrameFromRunCommands(
      commands.slice(0, i + 1),
      invariantContext
    )
    states.set(commands[i].id, frame.robotState)
  }
  return states
}

export function VisualizerContainer(props: VisualizerContainerProps): JSX.Element {
  const { analysisOutput } = props
  const { commands, robotType, liquids } = analysisOutput

  // ── State ──────────────────────────────────────────────
  const [isPlaying, setIsPlaying] = useState(false)
  const [selectedSlot, setSelectedSlot] = useState<string | null>(null)
  const [milliSecondsPerFrame, setMilliSecondsPerFrame] = useState(INITIAL_MILLISECONDS_PER_FRAME)
  const [selectedCommandId, setSelectedCommandId] = useState<string | null>(null)
  const [isDragging, setIsDragging] = useState(false)
  const [leftWidth, setLeftWidth] = useState(INITIAL_WIDTH_PX)
  const [rightWidth, setRightWidth] = useState(INITIAL_WIDTH_PX)

  // ── Refs ───────────────────────────────────────────────
  const containerRef = useRef<HTMLDivElement>(null)
  const resizingRef = useRef<ResizableColumn | null>(null)
  const startXRef = useRef(0)
  const startWidthRef = useRef(0)
  const leftWidthRef = useRef(leftWidth)
  const rightWidthRef = useRef(rightWidth)

  // Ref mirrors for stable callbacks (no stale closures)
  const filteredRef = useRef<RunTimeCommand[]>([])
  const selectedIdRef = useRef(selectedCommandId)
  const playingRef = useRef(isPlaying)

  useEffect(() => { leftWidthRef.current = leftWidth }, [leftWidth])
  useEffect(() => { rightWidthRef.current = rightWidth }, [rightWidth])
  useEffect(() => { selectedIdRef.current = selectedCommandId }, [selectedCommandId])
  useEffect(() => { playingRef.current = isPlaying }, [isPlaying])

  // ── Memoized: filtered commands (stable reference) ─────
  const filteredCommands = useMemo<RunTimeCommand[]>(
    () =>
      commands.filter(
        (cmd): cmd is RunTimeCommand =>
          typeof cmd.commandType === 'string' &&
          !cmd.commandType.includes('load') &&
          cmd.commandType !== 'home'
      ),
    [commands]
  )
  useEffect(() => { filteredRef.current = filteredCommands }, [filteredCommands])

  // ── Heavy compute: invariant context (once per analysis) ──
  const createdDate = useMemo(
    () => new Date(analysisOutput.createdAt),
    [analysisOutput.createdAt]
  )
  const invariantContext = useMemo(
    () => constructInvariantContextFromAnalysis(analysisOutput, analysisOutput.config, createdDate),
    [analysisOutput, createdDate]
  )

  // ── KEY OPTIMIZATION: Pre-compute ALL robot states ─────
  // Before: every playback step called getResultingTimelineFrameFromRunCommands (O(n) per step)
  // Now: one-time O(n²) precompute, then O(1) Map lookup per step
  const robotStateMap = useMemo(
    () => precomputeRobotStates(commands, invariantContext),
    [commands, invariantContext]
  )

  // ── Derived: indices ───────────────────────────────────
  const selectedCommandIndex = useMemo(
    () => commands.findIndex(c => c.id === selectedCommandId),
    [commands, selectedCommandId]
  )
  const filteredIdx = useMemo(
    () => filteredCommands.findIndex(c => c.id === selectedCommandId),
    [filteredCommands, selectedCommandId]
  )
  const safeFilteredIdx = filteredIdx >= 0 ? filteredIdx : 0

  // ── O(1) robot state lookup ────────────────────────────
  const robotState = useMemo(() => {
    if (selectedCommandId != null) {
      const s = robotStateMap.get(selectedCommandId)
      if (s != null) return s
    }
    const lastCmd = commands[commands.length - 1]
    return robotStateMap.get(lastCmd?.id ?? '')!
  }, [selectedCommandId, robotStateMap, commands])

  const selectedRunTimeCommand = useMemo(
    () => commands.find(c => c.id === selectedCommandId),
    [commands, selectedCommandId]
  )

  // ── Auto-select first command ──────────────────────────
  useEffect(() => {
    if (selectedCommandId != null) return
    const id = filteredCommands[0]?.id ?? commands[0]?.id ?? null
    if (id != null) setSelectedCommandId(id)
  }, [selectedCommandId, filteredCommands, commands])

  // ── Playback: advance one step ─────────────────────────
  const advancePlayback = useCallback((): void => {
    const cmds = filteredRef.current
    setSelectedCommandId(prev => {
      const idx = cmds.findIndex(c => c.id === prev)
      if (idx < 0 || idx >= cmds.length - 1) return prev
      return cmds[idx + 1].id
    })
  }, [])

  // ── Playback timer: setTimeout chain ───────────────────
  // setTimeout chain instead of setInterval:
  //   - Each tick waits for render to complete before scheduling next
  //   - Prevents frame queue buildup that freezes the UI
  //   - Buttons remain responsive between frames
  useEffect(() => {
    if (!isPlaying || filteredCommands.length <= 1) return

    // Auto-stop at last step
    if (filteredIdx >= filteredCommands.length - 1) {
      setIsPlaying(false)
      return
    }

    const tid = setTimeout(advancePlayback, milliSecondsPerFrame)
    return () => clearTimeout(tid)
  }, [isPlaying, filteredIdx, filteredCommands.length, milliSecondsPerFrame, advancePlayback])

  // ── Play / Pause (no nested setState) ──────────────────
  const handlePlayPause = useCallback((): void => {
    if (playingRef.current) {
      setIsPlaying(false)
      return
    }

    const cmds = filteredRef.current
    if (cmds.length <= 1) return

    const curId = selectedIdRef.current
    const idx = cmds.findIndex(c => c.id === curId)

    // At end → restart from beginning; otherwise advance one step
    setSelectedCommandId(
      idx < 0 || idx >= cmds.length - 1
        ? cmds[0].id
        : cmds[idx + 1].id
    )
    setIsPlaying(true)
  }, [])

  // ── Step forward / backward ────────────────────────────
  const stepForward = useCallback((): void => {
    const cmds = filteredRef.current
    setIsPlaying(false)
    setSelectedCommandId(prev => {
      const idx = cmds.findIndex(c => c.id === prev)
      if (idx < 0) return cmds[0]?.id ?? prev
      return cmds[Math.min(idx + 1, cmds.length - 1)]?.id ?? prev
    })
  }, [])

  const stepBackward = useCallback((): void => {
    const cmds = filteredRef.current
    setIsPlaying(false)
    setSelectedCommandId(prev => {
      const idx = cmds.findIndex(c => c.id === prev)
      if (idx <= 0) return prev
      return cmds[idx - 1]?.id ?? prev
    })
  }, [])

  // ── Keyboard shortcuts (stable deps) ───────────────────
  useEffect(() => {
    const onKey = (e: KeyboardEvent): void => {
      if (
        e.target instanceof HTMLInputElement ||
        e.target instanceof HTMLTextAreaElement
      ) return

      if (e.key === ' ') {
        e.preventDefault()
        handlePlayPause()
      } else if (e.key === 'ArrowRight') {
        e.preventDefault()
        stepForward()
      } else if (e.key === 'ArrowLeft') {
        e.preventDefault()
        stepBackward()
      }
    }
    document.addEventListener('keydown', onKey)
    return () => document.removeEventListener('keydown', onKey)
  }, [handlePlayPause, stepForward, stepBackward])

  // ── Percent complete ───────────────────────────────────
  const percentComplete = useMemo(() => {
    if (filteredIdx < 0 || filteredCommands.length === 0) return 0
    if (filteredCommands.length <= 1) return 100
    return Math.min(100, Math.max(0, (filteredIdx / (filteredCommands.length - 1)) * 100))
  }, [filteredIdx, filteredCommands.length])

  // ── Thermocycler guard ─────────────────────────────────
  const isThermocyclerAttached = useMemo(
    () =>
      Object.keys((robotState as Record<string, Record<string, unknown>>).modules ?? {}).some(id => {
        const entities = (invariantContext as Record<string, Record<string, Record<string, unknown>>>).moduleEntities
        const entity = entities?.[id]
        return (entity as { type?: string })?.type === THERMOCYCLER_MODULE_TYPE
      }),
    [robotState, invariantContext]
  )

  useEffect(() => {
    const tcSlots = ['A1', '8', '10', '11']
    if (isThermocyclerAttached && selectedSlot != null && tcSlots.includes(selectedSlot)) {
      setSelectedSlot(robotType === FLEX_ROBOT_TYPE ? 'B1' : '7')
    }
  }, [isThermocyclerAttached, selectedSlot, robotType])

  // ── Resizable columns ──────────────────────────────────
  const handleMouseMove = useCallback((e: globalThis.MouseEvent) => {
    if (resizingRef.current === null) return
    const cw = containerRef.current?.clientWidth ?? 0
    if (cw === 0) return

    const dx = e.clientX - startXRef.current

    if (resizingRef.current === 'left') {
      const nw = startWidthRef.current + dx
      const center = cw - nw - rightWidthRef.current - 2 * GUTTER_WIDTH_PX
      if (nw >= MIN_LEFT_COLUMN_WIDTH_PX && nw <= MAX_COLUMN_WIDTH_PX && center >= MIN_CENTER_WIDTH_PX) {
        setLeftWidth(nw)
      }
    } else {
      const nw = startWidthRef.current - dx
      const center = cw - leftWidthRef.current - nw - 2 * GUTTER_WIDTH_PX
      if (nw >= MIN_RIGHT_COLUMN_WIDTH_PX && nw <= MAX_COLUMN_WIDTH_PX && center >= MIN_CENTER_WIDTH_PX) {
        setRightWidth(nw)
      }
    }
  }, [])

  const handleMouseUp = useCallback((): void => {
    setIsDragging(false)
    resizingRef.current = null
    window.removeEventListener('mousemove', handleMouseMove)
    window.removeEventListener('mouseup', handleMouseUp)
  }, [handleMouseMove])

  const handleMouseDown = useCallback(
    (e: MouseEvent<HTMLDivElement>, col: ResizableColumn): void => {
      e.preventDefault()
      setIsDragging(true)
      resizingRef.current = col
      startXRef.current = e.clientX
      startWidthRef.current = col === 'left' ? leftWidthRef.current : rightWidthRef.current
      window.addEventListener('mousemove', handleMouseMove)
      window.addEventListener('mouseup', handleMouseUp)
    },
    [handleMouseMove, handleMouseUp]
  )

  useEffect(() => {
    const mm = handleMouseMove
    const mu = handleMouseUp
    return () => {
      window.removeEventListener('mousemove', mm)
      window.removeEventListener('mouseup', mu)
    }
  }, [handleMouseMove, handleMouseUp])

  // ── Render ─────────────────────────────────────────────
  return (
    <div className={styles.main_wrapper}>
      <div ref={containerRef} className={styles.layout_container}>
        <div className={styles.left_column} style={{ width: `${leftWidth}px` }}>
          <SimpleCommandSteps
            analysisOutput={analysisOutput}
            filteredCommands={filteredCommands}
            currentCommandIndex={safeFilteredIdx}
            setSelectedCommand={setSelectedCommandId}
            percentComplete={percentComplete}
            handlePause={() => setIsPlaying(false)}
          />
        </div>

        <div
          className={`${styles.gutter} ${isDragging ? styles.grabbing : ''}`}
          onMouseDown={e => handleMouseDown(e, 'left')}
        />

        <div className={styles.center_column}>
          <DeckView
            filteredCommands={filteredCommands}
            commands={commands}
            liquids={liquids}
            invariantContext={invariantContext}
            robotState={robotState}
            robotType={robotType ?? FLEX_ROBOT_TYPE}
            setSelectedSlot={setSelectedSlot}
            selectedRunTimeCommand={selectedRunTimeCommand}
          />
        </div>

        <div
          className={`${styles.gutter} ${isDragging ? styles.grabbing : ''}`}
          onMouseDown={e => handleMouseDown(e, 'right')}
        />

        <div className={styles.right_column} style={{ width: `${rightWidth}px` }}>
          {selectedRunTimeCommand != null ? (
            <StepDetailContainer
              commands={commands}
              robotState={robotState}
              invariantContext={invariantContext}
              currentCommand={selectedRunTimeCommand}
              liquids={liquids}
            />
          ) : null}
        </div>
      </div>

      <div className={styles.bottom_controls}>
        <Controls
          numCommandLength={filteredCommands.length}
          currentCommandIndex={filteredIdx}
          setSelectedCommand={setSelectedCommandId}
          handlePlayPause={handlePlayPause}
          isPlaying={isPlaying}
          commands={filteredCommands}
          groupedCommands={null}
          milliSecondsPerFrame={milliSecondsPerFrame}
          setMilliSecondsPerFrame={setMilliSecondsPerFrame}
        />
      </div>
    </div>
  )
}
