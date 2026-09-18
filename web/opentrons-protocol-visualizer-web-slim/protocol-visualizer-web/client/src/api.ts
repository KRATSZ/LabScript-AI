import type { ProtocolAnalysisOutput } from '@opentrons/shared-data'

const apiBase = (): string =>
  (import.meta.env.VITE_API_BASE as string | undefined) ?? ''

const POLL_MS = 900
const MAX_WAIT_MS = 15 * 60 * 1000

function formatDetail(detail: unknown): string {
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) {
    return detail
      .map((e: { msg?: string }) => e?.msg ?? JSON.stringify(e))
      .join('; ')
  }
  return JSON.stringify(detail)
}

export interface AnalyzeFormOptions {
  labware?: File[]
  rtpCsv?: File[]
  /** JSON object string for `opentrons analyze --rtp-values` */
  rtpValues?: string
  /**
   * JSON object mapping RTP variable names to uploaded CSV basenames, e.g.
   * `{"liquids": "liquids.csv"}` when a file named liquids.csv is in rtpCsv.
   */
  rtpFilesMap?: string
  check?: boolean
}

/** Progress while the server job runs (emitted only when the phase changes). */
export type AnalyzeProgressPhase =
  | 'submitting'
  | 'submitted'
  | 'queued'
  | 'running'

export type AnalyzeProtocolParams = AnalyzeFormOptions & {
  onProgress?: (phase: AnalyzeProgressPhase) => void
}

function buildFormData(protocol: File, options: AnalyzeFormOptions = {}): FormData {
  const fd = new FormData()
  fd.append('protocol', protocol)
  for (const f of options.labware ?? []) {
    fd.append('labware', f)
  }
  for (const f of options.rtpCsv ?? []) {
    fd.append('rtp_csv', f)
  }
  const rv = options.rtpValues?.trim()
  if (rv != null && rv !== '') {
    fd.append('rtp_values', rv)
  }
  const rm = options.rtpFilesMap?.trim()
  if (rm != null && rm !== '') {
    fd.append('rtp_files_map', rm)
  }
  if (options.check === true) {
    fd.append('check', 'true')
  }
  return fd
}

interface JobStatusBody {
  status: 'pending' | 'running' | 'completed' | 'failed'
  result?: ProtocolAnalysisOutput
  error?: string
}

function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms))
}

/**
 * Enqueues analysis and polls until completed, failed, or timeout.
 */
export async function analyzeProtocol(
  protocol: File,
  params: AnalyzeProtocolParams = {}
): Promise<ProtocolAnalysisOutput> {
  const { onProgress, ...options } = params
  let lastPhase: AnalyzeProgressPhase | null = null
  const emit = (phase: AnalyzeProgressPhase): void => {
    if (phase !== lastPhase) {
      lastPhase = phase
      onProgress?.(phase)
    }
  }

  emit('submitting')
  const fd = buildFormData(protocol, options)

  const startRes = await fetch(`${apiBase()}/api/analyze/start`, {
    method: 'POST',
    body: fd,
  })

  if (!startRes.ok) {
    let message = startRes.statusText
    try {
      const body = (await startRes.json()) as { detail?: unknown }
      if (body.detail != null) message = formatDetail(body.detail)
    } catch {
      /* ignore */
    }
    throw new Error(message)
  }

  const { job_id: jobId } = (await startRes.json()) as { job_id: string }
  emit('submitted')

  const deadline = Date.now() + MAX_WAIT_MS

  while (Date.now() < deadline) {
    await sleep(POLL_MS)
    const r = await fetch(`${apiBase()}/api/analyze/jobs/${jobId}`)
    if (!r.ok) {
      let message = r.statusText
      try {
        const body = (await r.json()) as { detail?: unknown }
        if (body.detail != null) message = formatDetail(body.detail)
      } catch {
        /* ignore */
      }
      throw new Error(message)
    }
    const body = (await r.json()) as JobStatusBody
    if (body.status === 'pending') {
      emit('queued')
    } else if (body.status === 'running') {
      emit('running')
    }

    if (body.status === 'completed') {
      if (body.result == null) {
        throw new Error('Analysis completed but result was missing')
      }
      return body.result
    }
    if (body.status === 'failed') {
      throw new Error(body.error ?? 'Analysis failed')
    }
  }

  throw new Error('Analysis timed out while waiting for the server job')
}
