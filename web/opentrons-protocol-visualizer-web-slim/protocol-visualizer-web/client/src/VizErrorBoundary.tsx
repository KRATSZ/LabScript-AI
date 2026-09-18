import { Component, type ErrorInfo, type ReactNode } from 'react'

import {
  COLORS,
  DIRECTION_COLUMN,
  Flex,
  PrimaryButton,
  SPACING,
  StyledText,
} from '@opentrons/components'

interface Props {
  children: ReactNode
  /** Change when loading a new analysis so the boundary resets */
  resetKey: string
  onBack: () => void
}

interface State {
  error: Error | null
}

export class VizErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = { error: null }
  }

  static getDerivedStateFromError(error: Error): State {
    return { error }
  }

  override componentDidCatch(error: Error, info: ErrorInfo): void {
    console.error('Protocol visualizer render error:', error, info.componentStack)
  }

  override componentDidUpdate(prevProps: Props): void {
    if (prevProps.resetKey !== this.props.resetKey) {
      this.setState({ error: null })
    }
  }

  override render(): ReactNode {
    if (this.state.error != null) {
      return (
        <Flex
          flexDirection={DIRECTION_COLUMN}
          padding={SPACING.spacing24}
          gridGap={SPACING.spacing16}
          backgroundColor={COLORS.white}
          height="100%"
        >
          <StyledText desktopStyle="headingSmallBold">
            Animation view render failed
          </StyledText>
          <StyledText desktopStyle="bodyDefaultRegular" color={COLORS.grey60}>
            Analysis completed, but the playback engine could not process some
            commands or deck states in this protocol. Try running the analysis
            in the Opentrons App, or simplify the protocol and try again.
          </StyledText>
          <pre
            style={{
              margin: 0,
              color: COLORS.red60,
              fontFamily: 'inherit',
              fontSize: '0.875rem',
              whiteSpace: 'pre-wrap',
              wordBreak: 'break-word',
            }}
          >
            {this.state.error.message}
          </pre>
          <PrimaryButton onClick={() => this.props.onBack()}>
            Back to upload
          </PrimaryButton>
        </Flex>
      )
    }
    return this.props.children
  }
}
