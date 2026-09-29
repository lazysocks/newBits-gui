<template>
  <div>
    <h1>Apply Image</h1>
    <p class="subtitle">Writing recovery image to {{ drives.length }} USB device(s).</p>

    <div v-if="model" class="card" style="margin-top: 20px">
      <div style="font-weight: 600; margin-bottom: 6px">{{ model.manufacturer }} {{ model.model }}</div>
      <div style="font-size: 12px; color: var(--text-muted)">ChromeOS {{ model.chrome_version }} &mdash; v{{ model.version }}</div>
    </div>

    <div class="card" style="margin-top: 12px">
      <div v-for="d in drives" :key="d" class="drive-item">
        <code>/dev/{{ d }}</code>
      </div>
      <div style="margin-top: 10px; color: var(--warning); font-size: 13px">
        Image: {{ imageFile }}
      </div>
    </div>

    <div v-if="!started && !cancelling" class="step-actions" style="margin-top: 20px">
      <button class="secondary" @click="$emit('back')">← Back</button>
      <button class="secondary" @click="cancel">Cancel</button>
      <button class="danger" @click="apply">Write Image Now</button>
    </div>

    <div v-if="cancelling" style="margin-top: 20px; color: var(--text-muted); font-size: 13px">
      {{ cancelDone ? 'Cleaned up. Closing…' : 'Cleaning up temp files…' }}
    </div>

    <div v-else style="margin-top: 20px">
      <div class="phase-block" :class="{ 'phase-done': done, 'phase-error': !!error, 'phase-active': started && !done && !error }">
        <div class="phase-header">
          <h3>Writing…</h3>
          <span class="badge" :class="done ? 'badge-success' : error ? 'badge-error' : 'badge-warning'">
            {{ done ? 'Done' : error ? 'Error' : 'Running' }}
          </span>
        </div>
        <div v-if="!done && !error" style="margin-top: 10px">
          <div class="progress-bar">
            <div class="progress-bar-fill" :style="{ width: progressPct + '%' }"></div>
          </div>
          <div class="progress-label">
            {{ store.progress.desc }}
            <span v-if="store.progress.total">
              {{ formatBytes(store.progress.current) }} / {{ formatBytes(store.progress.total) }}
              ({{ progressPct }}%)
            </span>
          </div>
        </div>
      </div>

      <div v-if="error" class="error-msg" style="margin-top: 14px">{{ error }}</div>

      <div v-if="done" class="step-actions">
        <button class="secondary" @click="$emit('more')">Write more drives</button>
        <button class="primary" @click="$emit('complete')">Continue →</button>
      </div>
    </div>

    <div class="log-panel" style="margin-top: 16px" ref="logEl">
      <div v-for="(l, i) in logs" :key="i" :class="'log-' + (l.level || 'info')">{{ l.msg }}</div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick, toRaw } from 'vue'
import { sendCommand, store } from '../stores/bridge.js'

const props = defineProps({
  imageFile: String,
  drives: Array,
  model: Object,
  tempFiles: Array
})
defineEmits(['complete', 'more', 'back'])

const started = ref(false)
const done = ref(false)
const error = ref('')
const logs = ref([])
const cancelling = ref(false)
const cancelDone = ref(false)

const progressPct = computed(() => {
  const { current, total } = store.progress
  return total ? Math.round((current / total) * 100) : 0
})

function formatBytes(n) {
  if (!n) return '0 B'
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(n) / Math.log(1024))
  return `${(n / Math.pow(1024, i)).toFixed(1)} ${sizes[i]}`
}
const logEl = ref(null)

watch(() => store.logs.length, async () => {
  const last = store.logs[store.logs.length - 1]
  if (last) logs.value.push(last)
  await nextTick()
  if (logEl.value) logEl.value.scrollTop = logEl.value.scrollHeight
})

async function cancel() {
  cancelling.value = true
  try {
    await sendCommand({ cmd: 'cleanup', files: toRaw(props.tempFiles ?? []) })
  } catch (_) {}
  cancelDone.value = true
  setTimeout(() => window.close(), 800)
}

async function apply() {
  started.value = true
  error.value = ''
  try {
    await sendCommand({
      cmd: 'apply_image',
      image_file: props.imageFile,
      devices: toRaw(props.drives)
    })
    done.value = true
  } catch (e) {
    error.value = e.message
  }
}
</script>

<style scoped>
.subtitle { color: var(--text-muted); margin-top: 6px; }
.drive-item { font-family: monospace; padding: 4px 0; }
code { background: var(--surface-2); padding: 2px 6px; border-radius: 3px; font-size: 12px; }
.phase-block {
  padding: 16px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
}
.phase-block.phase-active { border-color: var(--warning); }
.phase-block.phase-done { border-color: var(--success); }
.phase-block.phase-error { border-color: var(--error); }
.phase-header { display: flex; align-items: center; justify-content: space-between; }
.badge { padding: 2px 10px; border-radius: 20px; font-size: 11px; font-weight: 600; background: var(--surface-2); color: var(--text-muted); }
.badge-success { background: #1a3d1a; color: var(--success); }
.badge-warning { background: #3d2e1a; color: var(--warning); }
.badge-error { background: #3d1a1a; color: var(--error); }
.progress-bar { height: 6px; background: var(--surface-2); border-radius: 3px; overflow: hidden; }
.progress-bar-fill { height: 100%; background: var(--warning); transition: width 0.3s ease; }
.progress-label { font-size: 12px; color: var(--text-muted); margin-top: 6px; display: flex; justify-content: space-between; }
</style>
