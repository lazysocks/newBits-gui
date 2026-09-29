<template>
  <div>
    <h1>Download &amp; Verify Image</h1>
    <p class="subtitle">Downloading recovery image for <strong>{{ model.model }}</strong></p>

    <div class="card" style="margin-top: 20px">
      <div class="meta-grid">
        <span>Manufacturer</span><span>{{ model.manufacturer }}</span>
        <span>Version</span><span>{{ model.chrome_version }}</span>
        <span>File size</span><span>{{ formatBytes(model.filesize) }}</span>
      </div>
    </div>

    <div style="margin-top: 20px; display: flex; flex-direction: column; gap: 14px">
      <!-- Download progress -->
      <div class="phase-block" :class="phaseClass('download')">
        <div class="phase-header">
          <h3>Download</h3>
          <span class="badge" :class="badgeClass(phases.download)">{{ phases.download }}</span>
        </div>
        <div v-if="phases.download === 'running'" style="margin-top: 10px">
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

      <!-- Verify -->
      <div class="phase-block" :class="phaseClass('verify')">
        <div class="phase-header">
          <h3>SHA1 Verify</h3>
          <span class="badge" :class="badgeClass(phases.verify)">{{ phases.verify }}</span>
        </div>
      </div>

      <!-- Unzip -->
      <div class="phase-block" :class="phaseClass('unzip')">
        <div class="phase-header">
          <h3>Extract</h3>
          <span class="badge" :class="badgeClass(phases.unzip)">{{ phases.unzip }}</span>
        </div>
      </div>
    </div>

    <div v-if="error" class="error-msg" style="margin-top: 16px">{{ error }}</div>

    <div class="step-actions">
      <button v-if="!started" class="secondary" @click="$emit('back')">← Back</button>
      <button
        v-if="!started"
        class="primary"
        @click="start"
      >
        Start Download
      </button>
    </div>

    <div class="log-panel" style="margin-top: 16px" ref="logEl">
      <div
        v-for="(l, i) in logs"
        :key="i"
        :class="'log-' + (l.level || 'info')"
      >{{ l.msg }}</div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick, onMounted } from 'vue'
import { sendCommand, store } from '../stores/bridge.js'

const props = defineProps({ model: Object })
const emit = defineEmits(['complete', 'back'])

const workdir = ref('')
onMounted(async () => {
  workdir.value = await window.api.getWorkdir()
})

const started = ref(false)
const error = ref('')
const logs = ref([])
const logEl = ref(null)

const phases = ref({
  download: 'pending',
  verify: 'pending',
  unzip: 'pending'
})

const progressPct = computed(() => {
  const { current, total } = store.progress
  return total ? Math.round((current / total) * 100) : 0
})

watch(() => store.logs.length, async () => {
  const lastLog = store.logs[store.logs.length - 1]
  if (lastLog) logs.value.push(lastLog)
  await nextTick()
  if (logEl.value) logEl.value.scrollTop = logEl.value.scrollHeight
})

function formatBytes(n) {
  if (!n) return '0 B'
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(n) / Math.log(1024))
  return `${(n / Math.pow(1024, i)).toFixed(1)} ${sizes[i]}`
}

function phaseClass(p) {
  return {
    'phase-active': phases.value[p] === 'running',
    'phase-done': phases.value[p] === 'done',
    'phase-error': phases.value[p] === 'error'
  }
}

function badgeClass(state) {
  if (state === 'done') return 'badge-success'
  if (state === 'running') return 'badge-warning'
  if (state === 'error') return 'badge-error'
  return ''
}

async function start() {
  started.value = true
  error.value = ''

  const zipPath = `${workdir.value}/${props.model.file}.zip`
  const imagePath = `${workdir.value}/${props.model.file}`

  // Download
  phases.value.download = 'running'
  try {
    await sendCommand({
      cmd: 'download_image',
      url: props.model.url,
      filename: props.model.file + '.zip',
      dest: zipPath,
      sha1: props.model.sha1
    })
    phases.value.download = 'done'
    phases.value.verify = 'done'
  } catch (e) {
    phases.value.download = 'error'
    error.value = e.message
    return
  }

  // Unzip
  phases.value.unzip = 'running'
  try {
    await sendCommand({
      cmd: 'unzip_image',
      zipfile: zipPath,
      workdir: workdir.value,
      imagefile: imagePath,
      filesize: props.model.filesize
    })
    phases.value.unzip = 'done'
  } catch (e) {
    phases.value.unzip = 'error'
    error.value = e.message
    return
  }

  emit('complete', { imagePath, zipPath })
}
</script>

<style scoped>
.subtitle { color: var(--text-muted); margin-top: 6px; }
.meta-grid { display: grid; grid-template-columns: 120px 1fr; gap: 6px 14px; font-size: 13px; }
.meta-grid span:nth-child(odd) { color: var(--text-muted); }
.phase-block {
  padding: 14px 16px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  transition: border-color 0.2s;
}
.phase-block.phase-active { border-color: var(--warning); }
.phase-block.phase-done { border-color: var(--success); }
.phase-block.phase-error { border-color: var(--error); }
.phase-header { display: flex; align-items: center; justify-content: space-between; }
.progress-label { font-size: 12px; color: var(--text-muted); margin-top: 6px; display: flex; justify-content: space-between; }
.badge { padding: 2px 10px; border-radius: 20px; font-size: 11px; font-weight: 600; background: var(--surface-2); color: var(--text-muted); }
</style>
