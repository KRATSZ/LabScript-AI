import { useCallback, useEffect, useRef, useState } from 'react'

import type { ChangeEvent, DragEvent } from 'react'

import {
  Chip,
  COLORS,
  DIRECTION_COLUMN,
  Flex,
  Icon,
  PrimaryButton,
  SPACING,
  StyledText,
  TextAreaField,
  ToggleField,
  TertiaryButton,
} from '@opentrons/components'

import {
  analyzeProtocol,
  type AnalyzeProgressPhase,
} from './api'
import { normalizeAnalysisOutput } from './normalizeAnalysisOutput'
import styles from './upload.module.css'
import { VizErrorBoundary } from './VizErrorBoundary'
import { VisualizerContainer } from './viz/VisualizerContainer'

import type { ProtocolAnalysisOutput } from '@opentrons/shared-data'

function getProtocolTitle(analysis: ProtocolAnalysisOutput): string {
  const meta = analysis.metadata as Record<string, unknown> | undefined
  const name = meta?.protocolName
  return typeof name === 'string' && name.trim() !== ''
    ? name
    : 'Untitled protocol'
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

function fileKindLabel(file: File): string {
  const n = file.name.toLowerCase()
  if (n.endsWith('.py')) return 'Python protocol'
  if (n.endsWith('.json')) return 'JSON protocol'
  return 'Protocol file'
}

const PHASE_LABEL: Record<AnalyzeProgressPhase, string> = {
  submitting: 'Submitting to server…',
  submitted: 'Submitted, waiting in queue…',
  queued: 'Waiting in queue…',
  running: 'Analyzing protocol…',
}

const EMBEDDED_PROTOCOL_MESSAGE_TYPE = 'labscriptai:set-protocol'
const DEFAULT_PARENT_ORIGINS = [
  'http://localhost:5173',
  'http://127.0.0.1:5173',
  'http://localhost:4173',
  'http://127.0.0.1:4173',
  'http://labscriptai.cn',
  'https://labscriptai.cn',
  'https://www.labscriptai.cn',
]

interface EmbeddedProtocolMessage {
  type: typeof EMBEDDED_PROTOCOL_MESSAGE_TYPE
  source: string
  filename?: string
  autoAnalyze?: boolean
  check?: boolean
}

function getAllowedParentOrigins(): string[] {
  const configured = (import.meta.env.VITE_EMBED_PARENT_ORIGINS as string | undefined)
    ?.split(',')
    .map(origin => origin.trim())
    .filter(Boolean)

  return configured != null && configured.length > 0
    ? configured
    : DEFAULT_PARENT_ORIGINS
}

function isAllowedParentOrigin(origin: string): boolean {
  const allowedOrigins = getAllowedParentOrigins()
  return (
    origin === window.location.origin ||
    allowedOrigins.includes('*') ||
    allowedOrigins.includes(origin)
  )
}

function isEmbeddedProtocolMessage(value: unknown): value is EmbeddedProtocolMessage {
  if (typeof value !== 'object' || value == null) return false
  const candidate = value as Partial<EmbeddedProtocolMessage>
  return (
    candidate.type === EMBEDDED_PROTOCOL_MESSAGE_TYPE &&
    typeof candidate.source === 'string' &&
    candidate.source.trim() !== ''
  )
}

function getEmbeddedProtocolFilename(filename: string | undefined): string {
  const trimmed = filename?.trim()
  if (trimmed != null && trimmed !== '') return trimmed
  return `labscriptai-protocol-${new Date().toISOString().slice(0, 10)}.py`
}

export function App(): JSX.Element {
  const protocolInputRef = useRef<HTMLInputElement>(null)
  const labwareInputRef = useRef<HTMLInputElement>(null)
  const rtpCsvInputRef = useRef<HTMLInputElement>(null)
  const helpPanelRef = useRef<HTMLDetailsElement>(null)

  const [analysis, setAnalysis] = useState<ProtocolAnalysisOutput | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [errorExpanded, setErrorExpanded] = useState(false)
  const [loading, setLoading] = useState(false)
  const [progressPhase, setProgressPhase] =
    useState<AnalyzeProgressPhase | null>(null)

  const [rtpValues, setRtpValues] = useState('')
  const [rtpFilesMap, setRtpFilesMap] = useState('')
  const [checkProtocol, setCheckProtocol] = useState(false)

  const [protocolFile, setProtocolFile] = useState<File | null>(null)
  const [labwareFiles, setLabwareFiles] = useState<File[]>([])
  const [rtpCsvFiles, setRtpCsvFiles] = useState<File[]>([])
  const [pendingEmbeddedAnalyze, setPendingEmbeddedAnalyze] = useState(false)

  const [dragActive, setDragActive] = useState(false)
  const dragDepthRef = useRef(0)

  const runAnalyze = useCallback(async () => {
    if (protocolFile == null) return
    setError(null)
    setErrorExpanded(false)
    setLoading(true)
    setProgressPhase(null)
    setAnalysis(null)
    try {
      const result = await analyzeProtocol(protocolFile, {
        labware: labwareFiles,
        rtpCsv: rtpCsvFiles,
        rtpValues: rtpValues.trim() === '' ? undefined : rtpValues,
        rtpFilesMap: rtpFilesMap.trim() === '' ? undefined : rtpFilesMap,
        check: checkProtocol,
        onProgress: setProgressPhase,
      })
      setAnalysis(normalizeAnalysisOutput(result))
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e))
    } finally {
      setLoading(false)
      setProgressPhase(null)
    }
  }, [
    protocolFile,
    labwareFiles,
    rtpCsvFiles,
    rtpValues,
    rtpFilesMap,
    checkProtocol,
  ])

  const openHelp = useCallback(() => {
    const el = helpPanelRef.current
    if (el != null) {
      el.open = true
      el.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
    }
  }, [])

  const copyError = useCallback(async () => {
    if (error == null) return
    try {
      await navigator.clipboard.writeText(error)
    } catch {
      /* ignore */
    }
  }, [error])

  const onProtocolInputChange = useCallback(
    (e: ChangeEvent<HTMLInputElement>) => {
      const f = e.target.files?.[0] ?? null
      setProtocolFile(f)
      e.target.value = ''
    },
    []
  )

  const onDropZoneDragEnter = useCallback((e: DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    dragDepthRef.current += 1
    setDragActive(true)
  }, [])

  const onDropZoneDragLeave = useCallback((e: DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    dragDepthRef.current -= 1
    if (dragDepthRef.current <= 0) {
      dragDepthRef.current = 0
      setDragActive(false)
    }
  }, [])

  const onDropZoneDragOver = useCallback((e: DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
  }, [])

  const onDropZoneDrop = useCallback((e: DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    dragDepthRef.current = 0
    setDragActive(false)
    const f = e.dataTransfer.files?.[0]
    if (f == null) return
    const lower = f.name.toLowerCase()
    if (!lower.endsWith('.py') && !lower.endsWith('.json')) {
      setError('Please drop a .py or .json protocol file.')
      return
    }
    setError(null)
    setProtocolFile(f)
  }, [])

  const clearProtocol = useCallback(() => {
    setProtocolFile(null)
    setPendingEmbeddedAnalyze(false)
    if (protocolInputRef.current != null) {
      protocolInputRef.current.value = ''
    }
  }, [])

  useEffect(() => {
    const onMessage = (event: MessageEvent<unknown>): void => {
      if (!isAllowedParentOrigin(event.origin)) return
      if (!isEmbeddedProtocolMessage(event.data)) return

      const data = event.data
      const filename = getEmbeddedProtocolFilename(data.filename)
      const file = new File([data.source], filename, {
        type: filename.toLowerCase().endsWith('.json')
          ? 'application/json'
          : 'text/x-python',
      })

      setError(null)
      setErrorExpanded(false)
      setAnalysis(null)
      setLabwareFiles([])
      setRtpCsvFiles([])
      setRtpValues('')
      setRtpFilesMap('')
      setCheckProtocol(data.check === true)
      setProtocolFile(file)
      setPendingEmbeddedAnalyze(data.autoAnalyze === true)
    }

    window.addEventListener('message', onMessage)
    return () => window.removeEventListener('message', onMessage)
  }, [])

  useEffect(() => {
    if (!pendingEmbeddedAnalyze || protocolFile == null || loading) return
    setPendingEmbeddedAnalyze(false)
    void runAnalyze()
  }, [loading, pendingEmbeddedAnalyze, protocolFile, runAnalyze])

  if (analysis != null) {
    const title = getProtocolTitle(analysis)
    const errCount = analysis.errors.length
    const robotLabel = analysis.robotType ?? '—'

    return (
      <Flex
        flexDirection={DIRECTION_COLUMN}
        height="100%"
        backgroundColor={COLORS.grey10}
      >
        <Flex
          padding={`${SPACING.spacing16} ${SPACING.spacing24}`}
          backgroundColor={COLORS.white}
          justifyContent="space-between"
          alignItems="center"
          gridGap={SPACING.spacing16}
          className={styles.result_bar}
        >
          <Flex
            flexDirection={DIRECTION_COLUMN}
            gridGap={SPACING.spacing4}
            flex="1"
            minWidth="12rem"
          >
            <StyledText desktopStyle="bodyDefaultSemiBold">{title}</StyledText>
            <StyledText desktopStyle="bodyDefaultRegular" color={COLORS.grey60}>
              {robotLabel}
            </StyledText>
          </Flex>
          <Flex alignItems="center" gridGap={SPACING.spacing12} flexWrap="wrap">
            {errCount === 0 ? (
              <Chip type="success" chipSize="small" text="No errors" />
            ) : (
              <Chip
                type="error"
                chipSize="small"
                text={
                  errCount === 1
                    ? '1 analysis error'
                    : `${errCount} analysis errors`
                }
              />
            )}
            <PrimaryButton
              onClick={() => {
                setAnalysis(null)
                setError(null)
              }}
            >
              Upload another protocol
            </PrimaryButton>
          </Flex>
        </Flex>
        <Flex flex="1" minHeight="0" overflow="hidden">
          <VizErrorBoundary
            resetKey={analysis.createdAt}
            onBack={() => {
              setAnalysis(null)
              setError(null)
            }}
          >
            <VisualizerContainer
              analysisOutput={analysis}
            />
          </VizErrorBoundary>
        </Flex>
      </Flex>
    )
  }

  const phaseText =
    progressPhase != null ? PHASE_LABEL[progressPhase] : 'Processing…'

  const submitDisabled = protocolFile == null || loading
  const onSubmitClick = (): void => {
    void runAnalyze()
  }

  return (
    <div className={styles.page}>
      <div className={styles.card_shell}>
        <div className={styles.card}>
          {loading ? (
            <div className={styles.loading_overlay} aria-live="polite">
              <Icon name="ot-spinner" spin size="2.5rem" color={COLORS.blue50} />
              <StyledText desktopStyle="bodyDefaultSemiBold">
                {phaseText}
              </StyledText>
              <div className={styles.indeterminate_track}>
                <div className={styles.indeterminate_bar} />
              </div>
              <StyledText desktopStyle="bodyDefaultRegular" color={COLORS.grey60}>
                Complex protocols can take several seconds to a few minutes.
                Please wait. The page will refresh automatically when results
                are ready.
              </StyledText>
            </div>
          ) : null}

          <div className={styles.title_block}>
            <StyledText desktopStyle="headingSmallBold">
              Protocol animation preview
            </StyledText>
            <StyledText
              desktopStyle="bodyDefaultRegular"
              color={COLORS.grey60}
              className={styles.tagline}
            >
              Upload a protocol and replay pipetting plus deck changes step by
              step in the browser to check that the workflow matches your
              expectations.
            </StyledText>
            <div className={styles.help_row}>
              <button
                type="button"
                className={styles.help_link}
                onClick={openHelp}
              >
                Help & technical notes
              </button>
            </div>
          </div>

          <StyledText
            desktopStyle="captionSemiBold"
            color={COLORS.grey60}
            className={styles.section_label}
          >
            Step 1 · Select protocol
          </StyledText>

          <input
            id="pv-protocol-input"
            ref={protocolInputRef}
            type="file"
            accept=".py,.json"
            className={styles.hidden_input}
            onChange={onProtocolInputChange}
            aria-label="Choose protocol file"
          />
          <label
            htmlFor="pv-protocol-input"
            className={`${styles.dropzone} ${dragActive ? styles.dropzone_active : ''}`}
            onDragEnter={onDropZoneDragEnter}
            onDragLeave={onDropZoneDragLeave}
            onDragOver={onDropZoneDragOver}
            onDrop={onDropZoneDrop}
          >
            <Icon name="upload" size="2rem" color={COLORS.grey60} />
            <StyledText desktopStyle="bodyDefaultSemiBold">
              Click to select or drag and drop a protocol file
            </StyledText>
            <StyledText desktopStyle="bodyDefaultRegular" color={COLORS.grey60}>
              Supports .py (Python) or .json (Protocol Designer export)
            </StyledText>
          </label>

          {protocolFile != null ? (
            <div className={styles.file_summary}>
              <Flex
                justifyContent="space-between"
                alignItems="flex-start"
                gridGap={SPACING.spacing12}
              >
                <Flex flexDirection={DIRECTION_COLUMN} gridGap={SPACING.spacing4}>
                  <StyledText desktopStyle="bodyDefaultSemiBold">
                    {protocolFile.name}
                  </StyledText>
                  <StyledText desktopStyle="bodyDefaultRegular" color={COLORS.grey60}>
                    {formatFileSize(protocolFile.size)} · {fileKindLabel(protocolFile)}
                  </StyledText>
                </Flex>
                <TertiaryButton
                  buttonType="white"
                  onClick={e => {
                    e.preventDefault()
                    clearProtocol()
                  }}
                >
                  Remove
                </TertiaryButton>
              </Flex>
            </div>
          ) : null}

          <details className={styles.advanced}>
            <summary>
              <span>Advanced options (usually not needed)</span>
              <Icon name="chevron-down" size="1rem" />
            </summary>
            <div className={styles.advanced_body}>
              <input
                ref={labwareInputRef}
                type="file"
                accept=".json,application/json"
                multiple
                className={styles.hidden_input}
                id="pv-labware-input"
                onChange={e => {
                  setLabwareFiles(Array.from(e.target.files ?? []))
                  e.target.value = ''
                }}
              />
              <Flex flexDirection={DIRECTION_COLUMN} gridGap={SPACING.spacing8}>
                <label htmlFor="pv-labware-input">
                  <StyledText desktopStyle="bodyDefaultSemiBold">
                    Custom labware JSON
                  </StyledText>
                </label>
                <Flex gridGap={SPACING.spacing8} alignItems="center" flexWrap="wrap">
                  <TertiaryButton
                    buttonType="white"
                    onClick={() => labwareInputRef.current?.click()}
                  >
                    Add labware files
                  </TertiaryButton>
                  <StyledText desktopStyle="bodyDefaultRegular" color={COLORS.grey60}>
                    {labwareFiles.length > 0
                      ? `Selected ${labwareFiles.length} file${
                          labwareFiles.length === 1 ? '' : 's'
                        }`
                      : 'None selected'}
                  </StyledText>
                </Flex>
              </Flex>

              <TextAreaField
                id="pv-rtp-values"
                title="Runtime parameters RTP (JSON, optional)"
                caption='Same format as --rtp-values, for example {"dry_run": true}'
                value={rtpValues}
                onChange={e => {
                  setRtpValues(e.target.value)
                }}
                height="6rem"
              />

              <TextAreaField
                id="pv-rtp-map"
                title="RTP to CSV filename mapping (JSON, optional)"
                caption='Key is the RTP variable name and value is the uploaded CSV filename, for example {"liquids": "liquids.csv"}'
                value={rtpFilesMap}
                onChange={e => {
                  setRtpFilesMap(e.target.value)
                }}
                height="5rem"
              />

              <input
                ref={rtpCsvInputRef}
                type="file"
                accept=".csv,text/csv"
                multiple
                className={styles.hidden_input}
                id="pv-rtp-csv-input"
                onChange={e => {
                  setRtpCsvFiles(Array.from(e.target.files ?? []))
                  e.target.value = ''
                }}
              />
              <Flex flexDirection={DIRECTION_COLUMN} gridGap={SPACING.spacing8}>
                <label htmlFor="pv-rtp-csv-input">
                  <StyledText desktopStyle="bodyDefaultSemiBold">
                    RTP CSV files
                  </StyledText>
                </label>
                <Flex gridGap={SPACING.spacing8} alignItems="center" flexWrap="wrap">
                  <TertiaryButton
                    buttonType="white"
                    onClick={() => rtpCsvInputRef.current?.click()}
                  >
                    Choose CSV
                  </TertiaryButton>
                  <StyledText desktopStyle="bodyDefaultRegular" color={COLORS.grey60}>
                    {rtpCsvFiles.length > 0
                      ? rtpCsvFiles.map(f => f.name).join(', ')
                      : 'None selected'}
                  </StyledText>
                </Flex>
              </Flex>

              <Flex flexDirection={DIRECTION_COLUMN} gridGap={SPACING.spacing8}>
                <ToggleField
                  name="pv-check-toggle"
                  value={checkProtocol}
                  onChange={e => {
                    setCheckProtocol(e.target.checked)
                  }}
                  offLabel="Strict validation off"
                  onLabel="Strict validation on"
                />
                <StyledText desktopStyle="bodyDefaultRegular" color={COLORS.grey60}>
                  Matches analyzer --check: stricter and may report more errors,
                  which is useful before release.
                </StyledText>
              </Flex>
            </div>
          </details>

          <details ref={helpPanelRef} className={styles.help_panel}>
            <summary>
              <span>Help & technical notes</span>
              <Icon name="chevron-down" size="1rem" />
            </summary>
            <div>
              <Flex
                flexDirection={DIRECTION_COLUMN}
                gridGap={SPACING.spacing12}
              >
              <StyledText desktopStyle="bodyDefaultRegular" color={COLORS.grey60}>
                This page submits the protocol to the local backend, polls until
                analysis completes, and then replays the command sequence in the
                lower section. In production, use PV_CORS_ORIGINS to restrict
                which frontend domains can access the API.
              </StyledText>
              <StyledText desktopStyle="bodyDefaultRegular" color={COLORS.grey60}>
                The backend uses the Python interpreter from{' '}
                <code>api/.venv</code> by default to run{' '}
                <code>opentrons.cli analyze</code>. If analysis fails, make sure
                you have run <code>make -C api setup</code>, or set
                OT_ANALYZE_PYTHON to a Python interpreter with Opentrons
                installed.
              </StyledText>
            </Flex>
            </div>
          </details>

          <div className={styles.inline_submit}>
            <PrimaryButton
              disabled={submitDisabled}
              onClick={onSubmitClick}
              className={styles.full_width_button}
            >
              Generate animation
            </PrimaryButton>
          </div>

          {error != null ? (
            <div className={styles.error_box}>
              <StyledText desktopStyle="bodyDefaultSemiBold" color={COLORS.red60}>
                Analysis failed
              </StyledText>
              <Flex marginTop={SPACING.spacing8}>
                <StyledText desktopStyle="bodyDefaultRegular" color={COLORS.red60}>
                  {error.length > 280 && !errorExpanded
                    ? `${error.slice(0, 280)}…`
                    : error}
                </StyledText>
              </Flex>
              {error.length > 280 ? (
                <div className={styles.error_actions}>
                  <button
                    type="button"
                    className={styles.copy_btn}
                    onClick={() => {
                      setErrorExpanded(v => !v)
                    }}
                  >
                    {errorExpanded ? 'Hide details' : 'Show full details'}
                  </button>
                </div>
              ) : null}
              {errorExpanded && error.length > 280 ? (
                <pre className={styles.error_pre}>{error}</pre>
              ) : null}
              <div className={styles.error_actions}>
                <button type="button" className={styles.copy_btn} onClick={copyError}>
                  Copy error message
                </button>
              </div>
              <details className={styles.error_details}>
                <summary>
                  <StyledText desktopStyle="captionSemiBold" color={COLORS.grey60}>
                    Common causes
                  </StyledText>
                </summary>
                <Flex
                  flexDirection={DIRECTION_COLUMN}
                  gridGap={SPACING.spacing8}
                  marginTop={SPACING.spacing8}
                >
                  <StyledText desktopStyle="bodyDefaultRegular" color={COLORS.grey60}>
                    · Opentrons environment is not configured: run make -C api setup
                    from the repository root.
                  </StyledText>
                  <StyledText desktopStyle="bodyDefaultRegular" color={COLORS.grey60}>
                    · Protocol syntax or API version mismatch: update the .py or
                    .json file based on the error message.
                  </StyledText>
                  <StyledText desktopStyle="bodyDefaultRegular" color={COLORS.grey60}>
                    · RTP / CSV files are used: provide the mapping JSON and upload
                    CSV files with matching filenames.
                  </StyledText>
                  <StyledText desktopStyle="bodyDefaultRegular" color={COLORS.grey60}>
                    · Backend is not running or the port is wrong: start the API
                    on 8765 and make sure the Vite proxy or VITE_API_BASE is
                    correct.
                  </StyledText>
                </Flex>
              </details>
            </div>
          ) : null}
        </div>
      </div>

      <div className={styles.sticky_bar}>
        <div className={styles.sticky_inner}>
          <PrimaryButton
            disabled={submitDisabled}
            onClick={onSubmitClick}
            className={styles.full_width_button}
          >
            Generate animation
          </PrimaryButton>
        </div>
      </div>
    </div>
  )
}
