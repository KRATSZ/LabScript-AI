import { useEffect, useState } from 'react'

import {
  COLORS,
  NewIconButton,
  TertiaryButton,
  TimelineScrubber,
} from '@opentrons/components'

import styles from './controls.module.css'
import { PerStepOverflowMenu } from './PerStepOverflowMenu'

// import {
//   getNextGroupFirstCommandId,
//   getPreviousGroupFirstCommandId,
// } from './utils'

import type { Dispatch, SetStateAction } from 'react'
import type { RunTimeCommand } from '@opentrons/shared-data'
import type { GroupedCommands } from '../groupedCommandsTypes'

interface ControlsProps {
  numCommandLength: number
  currentCommandIndex: number
  setSelectedCommand: Dispatch<SetStateAction<string | null>>
  handlePlayPause: () => void
  isPlaying: boolean
  commands: RunTimeCommand[]
  groupedCommands: GroupedCommands | null
  milliSecondsPerFrame: number
  setMilliSecondsPerFrame: Dispatch<SetStateAction<number>>
}
export function Controls(props: ControlsProps): JSX.Element {
  const {
    numCommandLength,
    currentCommandIndex,
    setSelectedCommand,
    handlePlayPause,
    isPlaying,
    commands,
    groupedCommands,
    milliSecondsPerFrame,
    setMilliSecondsPerFrame,
  } = props
  void groupedCommands

  const playableCommandCount = numCommandLength > 1
  const safeCurrentCommandIndex = Math.min(
    Math.max(currentCommandIndex, 0),
    Math.max(numCommandLength - 1, 0)
  )
  const [showPerStepOverflowMenu, setShowPerStepOverflowMenu] = useState(false)
  const handlePerStepOverflowClick = (): void => {
    setShowPerStepOverflowMenu(
      showPerStepOverflowMenu => !showPerStepOverflowMenu
    )
  }

  const handleTrackChange = (updatedTrack: {
    id: string
    value: number
  }): void => {
    if (numCommandLength === 0) return
    const normalizedValue = updatedTrack.value / 100
    const nextIndex = Math.min(
      Math.max(Math.round(normalizedValue * (numCommandLength - 1)), 0),
      numCommandLength - 1
    )

    const nextCommandId = commands[nextIndex].id
    setSelectedCommand(nextCommandId)
  }

  const currentProgress =
    numCommandLength <= 1
      ? numCommandLength === 0
        ? 0
        : 100
      : (safeCurrentCommandIndex / (numCommandLength - 1)) * 100

  const tracks = [
    {
      id: 'protocol-timeline',
      value: currentProgress,
    },
  ]

  // handlePlayPause by space key
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent): void => {
      if (event.key === ' ') {
        event.preventDefault()
        if (playableCommandCount) {
          handlePlayPause()
        }
      }
    }

    document.addEventListener('keydown', handleKeyDown)

    return () => {
      document.removeEventListener('keydown', handleKeyDown)
    }
  }, [handlePlayPause, playableCommandCount])

  return (
    <div className={styles.container}>
      <div className={styles.controls_container}>
        <div className={styles.all_controls_info}>
          <div className={styles.timeline_wrapper}>
            <TimelineScrubber tracks={tracks} onTrackChange={handleTrackChange} />
          </div>
          <div className={styles.buttons_container}>
            <div className={styles.per_step_button_wrapper}>
              <TertiaryButton
                buttonType="white"
                onClick={handlePerStepOverflowClick}
                aria-label="Playback speed"
                title="Playback speed"
                className={styles.speed_button}
              >
                {`${milliSecondsPerFrame / 1000}s`}
              </TertiaryButton>
              {showPerStepOverflowMenu ? (
                <PerStepOverflowMenu
                  setShowPerStepOverflowMenu={setShowPerStepOverflowMenu}
                  setMilliSecondsPerFrame={setMilliSecondsPerFrame}
                />
              ) : null}
            </div>
            <NewIconButton
              variant="primary"
              iconName={isPlaying ? 'pause' : 'play'}
              iconSize="1.25rem"
              iconColor={COLORS.white}
              size="2.5rem"
              onClick={handlePlayPause}
              disabled={!playableCommandCount}
              ariaLabel={isPlaying ? 'Pause animation' : 'Play animation'}
            />
          </div>
        </div>
      </div>
    </div>
  )
}
