import type { RunTimeCommand } from '@opentrons/shared-data'

interface ParentNode {
  annotationId: string
  subCommands: LeafNode[]
  isHighlighted: boolean
  annotation?: unknown
}

export interface LeafNode {
  command: RunTimeCommand
  isHighlighted: boolean
}

export type GroupedCommands = Array<LeafNode | ParentNode>
