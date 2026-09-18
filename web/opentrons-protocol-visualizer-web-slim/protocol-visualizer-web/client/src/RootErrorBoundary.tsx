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
}

interface State {
  error: Error | null
}

export class RootErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = { error: null }
  }

  static getDerivedStateFromError(error: Error): State {
    return { error }
  }

  override componentDidCatch(error: Error, info: ErrorInfo): void {
    console.error('Protocol visualizer root error:', error, info.componentStack)
  }

  override render(): ReactNode {
    if (this.state.error != null) {
      return (
        <Flex
          flexDirection={DIRECTION_COLUMN}
          alignItems="center"
          justifyContent="center"
          backgroundColor={COLORS.grey10}
          style={{ minHeight: '100vh' }}
          padding={SPACING.spacing24}
        >
          <Flex
            flexDirection={DIRECTION_COLUMN}
            gridGap={SPACING.spacing12}
            backgroundColor={COLORS.white}
            padding={SPACING.spacing24}
            style={{
              width: '100%',
              maxWidth: '40rem',
              borderRadius: '12px',
              boxShadow: '0 12px 32px rgba(18, 36, 68, 0.14)',
            }}
          >
            <StyledText desktopStyle="headingSmallBold">
              Page render failed
            </StyledText>
            <StyledText desktopStyle="bodyDefaultRegular" color={COLORS.grey60}>
              The analysis result or animation renderer encountered an error.
              Try reloading the page first. If it still fails, send me the error
              message below.
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
            <PrimaryButton onClick={() => window.location.reload()}>
              Reload
            </PrimaryButton>
          </Flex>
        </Flex>
      )
    }
    return this.props.children
  }
}
