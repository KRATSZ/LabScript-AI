import { useEffect, useMemo, useRef } from 'react'
import { useTranslation } from 'react-i18next'

import {
  COLORS,
  StyledText,
  getCommandTextData,
  getLabwareDefinitionsFromCommands,
  useCommandTextString,
} from '@opentrons/components'
import { FLEX_ROBOT_TYPE } from '@opentrons/shared-data'

import styles from './simplecommandsteps.module.css'

import type { Dispatch, RefObject, SetStateAction } from 'react'
import type {
  LabwareDefinition,
  ProtocolAnalysisOutput,
  RobotType,
  RunTimeCommand,
} from '@opentrons/shared-data'
import type { CommandTextData } from '@opentrons/components'

interface SimpleCommandStepsProps {
  analysisOutput: ProtocolAnalysisOutput
  filteredCommands: RunTimeCommand[]
  currentCommandIndex: number
  setSelectedCommand: Dispatch<SetStateAction<string | null>>
  percentComplete: number
  handlePause: () => void
}

interface StepCardProps {
  command: RunTimeCommand
  index: number
  state: 'current' | 'completed' | 'pending'
  commandTextData: CommandTextData
  allRunDefs: LabwareDefinition[]
  robotType: RobotType
  setSelectedCommand: Dispatch<SetStateAction<string | null>>
  handlePause: () => void
  activeRef?: RefObject<HTMLLIElement>
}

function StepCard({
  command,
  index,
  state,
  commandTextData,
  allRunDefs,
  robotType,
  setSelectedCommand,
  handlePause,
  activeRef,
}: StepCardProps): JSX.Element {
  const { commandText } = useCommandTextString({
    command,
    allRunDefs,
    commandTextData,
    robotType,
  })

  const statusLabel =
    state === 'current' ? 'Current' : state === 'completed' ? 'Completed' : 'Pending'

  const displayText = commandText.trim() === '' ? command.commandType : commandText

  return (
    <li ref={activeRef ?? null} className={styles.step_item}>
      <button
        type="button"
        className={`${styles.step_button} ${styles[`step_button_${state}`]}`}
        onClick={() => {
          handlePause()
          setSelectedCommand(command.id)
        }}
      >
        <div className={styles.step_header}>
          <div className={`${styles.step_badge} ${styles[`step_badge_${state}`]}`}>
            {index + 1}
          </div>
          <div className={`${styles.step_status} ${styles[`step_status_${state}`]}`}>
            {statusLabel}
          </div>
        </div>
        <StyledText
          desktopStyle="bodyDefaultRegular"
          color={COLORS.grey60}
          className={styles.step_summary}
          title={displayText}
        >
          {displayText}
        </StyledText>
      </button>
    </li>
  )
}

export function SimpleCommandSteps(
  props: SimpleCommandStepsProps
): JSX.Element {
  const {
    analysisOutput,
    filteredCommands,
    currentCommandIndex,
    setSelectedCommand,
    percentComplete,
    handlePause,
  } = props
  const { t } = useTranslation('protocol_visualization')
  const activeItemRef = useRef<HTMLLIElement>(null)
  const commandTextData = useMemo(
    () => getCommandTextData(analysisOutput),
    [analysisOutput]
  )
  const allRunDefs = useMemo(
    () => getLabwareDefinitionsFromCommands(analysisOutput.commands),
    [analysisOutput.commands]
  )
  const robotType = analysisOutput.robotType ?? FLEX_ROBOT_TYPE

  useEffect(() => {
    if (activeItemRef.current != null) {
      activeItemRef.current.scrollIntoView({
        behavior: 'smooth',
        block: 'nearest',
      })
    }
  }, [currentCommandIndex])

  return (
    <div className={styles.detail_container}>
      <div className={styles.command_step}>
        <div className={styles.command_step_header}>
          <StyledText desktopStyle="bodyDefaultSemiBold">
            {t('protocol_steps')}
          </StyledText>
          <StyledText desktopStyle="bodyDefaultRegular" color={COLORS.grey60}>
            {t('percent_complete', { percent: percentComplete.toFixed(0) })}
          </StyledText>
        </div>
        <div className={styles.command_step_groups}>
          <ul className={styles.step_list}>
            {filteredCommands.map((cmd, index) => {
              const state =
                index < currentCommandIndex
                  ? 'completed'
                  : index === currentCommandIndex
                    ? 'current'
                    : 'pending'
              return (
                <StepCard
                  key={cmd.id}
                  command={cmd}
                  index={index}
                  state={state}
                  commandTextData={commandTextData}
                  allRunDefs={allRunDefs}
                  robotType={robotType}
                  setSelectedCommand={setSelectedCommand}
                  handlePause={handlePause}
                  activeRef={index === currentCommandIndex ? activeItemRef : undefined}
                />
              )
            })}
          </ul>
        </div>
      </div>
    </div>
  )
}
