import test from 'node:test'
import assert from 'node:assert/strict'
import {
  buildTaskLogSummary,
  classifyTaskLog,
  getTaskPhaseSteps
} from '../src/utils/task-log-view-model.mjs'

test('buildTaskLogSummary prefers structured progress details', () => {
  const task = { status: 'running', progress: 42, started_at: '2026-09-24T08:00:00Z' }
  const logs = [{
    status: 'progress',
    message: '同步进度: 42%',
    details: {
      progress: 42.6,
      transferred_files: 1248,
      total_files: 2930,
      transferred_size: 19756849561,
      total_size: 46403211264,
      transfer_speed: 90603520,
      eta: 252,
      current_file: 'backup/database.sql'
    }
  }]

  const summary = buildTaskLogSummary(task, logs, new Date('2026-09-24T08:10:00Z'))
  assert.equal(summary.progress, 42.6)
  assert.equal(summary.transferredFiles, 1248)
  assert.equal(summary.totalFiles, 2930)
  assert.equal(summary.currentFile, 'backup/database.sql')
  assert.equal(summary.phase, 'transferring')
  assert.equal(summary.elapsedSeconds, 600)
})

test('classifyTaskLog recognizes progress without translated literal strings', () => {
  assert.equal(classifyTaskLog({ status: 'progress', message: 'Progress: 10%' }), 'progress')
  assert.equal(classifyTaskLog({ status: 'error', message: 'AccessDenied' }), 'error')
  assert.equal(classifyTaskLog({ status: 'step_completed', message: 'scan completed' }), 'activity')
})

test('getTaskPhaseSteps marks the current transfer phase', () => {
  const steps = getTaskPhaseSteps('running', 'transferring')
  assert.equal(steps.find(step => step.key === 'transferring').state, 'active')
  assert.equal(steps.find(step => step.key === 'initializing').state, 'completed')
  assert.equal(steps.find(step => step.key === 'verifying').state, 'waiting')
})

test('failed task exposes the failure phase and preserves error', () => {
  const summary = buildTaskLogSummary({ status: 'failed', progress: 12, error: 'AccessDenied' }, [])
  assert.equal(summary.phase, 'failed')
  assert.equal(summary.error, 'AccessDenied')
})
