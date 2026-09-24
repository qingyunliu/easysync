const PROGRESS_PATTERN = /(?:同步进度|progress)\s*[:：]?\s*(\d+(?:\.\d+)?)%/i

const firstValue = (details, keys, fallback = null) => {
  for (const key of keys) {
    const value = details?.[key]
    if (value !== undefined && value !== null && value !== '') return value
  }
  return fallback
}

const asNumber = (value, fallback = 0) => {
  const number = Number(value)
  return Number.isFinite(number) ? number : fallback
}

const progressFromMessage = (message = '') => {
  const match = message.match(PROGRESS_PATTERN)
  return match ? asNumber(match[1]) : null
}

export const classifyTaskLog = (log = {}) => {
  const status = String(log.status || '').toLowerCase()
  const message = String(log.message || '')
  const phase = String(log.details?.phase || '').toLowerCase()

  if (status === 'error' || status === 'failed' || phase === 'task_failed') return 'error'
  if (status === 'progress' || phase === 'sync_progress' || PROGRESS_PATTERN.test(message)) return 'progress'
  return 'activity'
}

const phaseFromLog = (log = {}) => {
  const details = log.details || {}
  const rawPhase = String(details.phase || details.current_step || '').toLowerCase()
  const message = String(log.message || '').toLowerCase()

  if (/failed|error|失败/.test(rawPhase) || classifyTaskLog(log) === 'error') return 'failed'
  if (/complete|completed|完成/.test(rawPhase) || /任务.*完成|同步.*完成/.test(message)) return 'completed'
  if (/verify|校验|check/.test(rawPhase) || /校验/.test(message)) return 'verifying'
  if (/sync|transfer|progress|传输|同步/.test(rawPhase) || classifyTaskLog(log) === 'progress') return 'transferring'
  if (/scan|diff|扫描|差异/.test(rawPhase) || /扫描|差异/.test(message)) return 'scanning'
  if (/connect|mount|config|连接|挂载|配置/.test(rawPhase) || /连接|挂载|配置/.test(message)) return 'connecting'
  return 'initializing'
}

const phaseFromTask = (task = {}, latestLog = {}) => {
  const status = String(task.status || '').toLowerCase()
  if (status === 'failed') return 'failed'
  if (['completed', 'success'].includes(status)) return 'completed'
  if (['pending', 'assigned'].includes(status)) return 'initializing'
  if (['paused', 'pause_requested'].includes(status)) return 'paused'
  return phaseFromLog(latestLog)
}

export const buildTaskLogSummary = (task = {}, logs = [], now = new Date()) => {
  const sorted = [...logs].sort((a, b) => new Date(b.updated_at || b.created_at || 0) - new Date(a.updated_at || a.created_at || 0))
  const progressLog = sorted.find(log => classifyTaskLog(log) === 'progress') || {}
  const latestLog = sorted[0] || {}
  const details = progressLog.details || {}
  const parsedProgress = progressFromMessage(progressLog.message)
  const taskProgress = asNumber(task.progress)
  const progress = asNumber(firstValue(details, ['progress', 'percent'], parsedProgress ?? taskProgress), taskProgress)
  const startedAt = task.started_at ? new Date(task.started_at) : null
  const completedAt = task.completed_at ? new Date(task.completed_at) : null
  const end = completedAt || now
  const elapsedSeconds = startedAt && !Number.isNaN(startedAt.getTime())
    ? Math.max(0, Math.round((end.getTime() - startedAt.getTime()) / 1000))
    : 0

  return {
    status: task.status || 'pending',
    phase: phaseFromTask(task, latestLog),
    progress: Math.max(0, Math.min(100, progress)),
    transferredFiles: asNumber(firstValue(details, ['transferred_files', 'transfers', 'completed_files'])),
    totalFiles: asNumber(firstValue(details, ['total_files', 'files_total'])),
    transferredBytes: asNumber(firstValue(details, ['transferred_size', 'transferred_bytes', 'bytes'])),
    totalBytes: asNumber(firstValue(details, ['total_size', 'total_bytes'])),
    speedBytes: asNumber(firstValue(details, ['transfer_speed_bytes', 'speed_bytes', 'speed'])),
    speedText: typeof details.transfer_speed === 'string' ? details.transfer_speed : '',
    etaSeconds: asNumber(firstValue(details, ['eta_seconds', 'eta'])),
    currentFile: firstValue(details, ['current_file', 'file', 'name'], ''),
    elapsedSeconds,
    error: task.error || sorted.find(log => classifyTaskLog(log) === 'error')?.message || '',
    latestMessage: latestLog.message || ''
  }
}

const PHASES = [
  ['initializing', '初始化'],
  ['connecting', '连接存储'],
  ['scanning', '扫描与分析'],
  ['transferring', '传输文件'],
  ['verifying', '校验数据'],
  ['completed', '完成']
]

export const getTaskPhaseSteps = (taskStatus, currentPhase) => {
  const status = String(taskStatus || '').toLowerCase()
  const activeIndex = PHASES.findIndex(([key]) => key === currentPhase)
  return PHASES.map(([key, label], index) => {
    let state = 'waiting'
    if (status === 'completed') state = 'completed'
    else if (currentPhase === 'failed') state = index < Math.max(activeIndex, 1) ? 'completed' : (index === Math.max(activeIndex, 1) ? 'error' : 'waiting')
    else if (index < activeIndex) state = 'completed'
    else if (index === activeIndex) state = status === 'paused' ? 'paused' : 'active'
    return { key, label, state }
  })
}
