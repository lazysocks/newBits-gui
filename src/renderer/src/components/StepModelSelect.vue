<template>
  <div>
    <h1>Select Chromebook Model</h1>
    <p class="subtitle">Search by the model string shown on your Chromebook's recovery screen.</p>

    <!-- Download phase -->
    <div v-if="phase === 'download'" class="card" style="margin-top: 20px">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px">
        <h2 style="margin: 0">Fetching recovery list…</h2>
        <button class="secondary" style="padding: 4px 12px; font-size: 12px" @click="quit()">Quit</button>
      </div>
      <div>
        <div class="progress-bar">
          <div
            class="progress-bar-fill"
            :style="{ width: progressPct + '%' }"
          ></div>
        </div>
        <div class="progress-label">
          {{ store.progress.desc || 'Downloading…' }}
          <span v-if="store.progress.total">
            {{ formatBytes(store.progress.current) }} / {{ formatBytes(store.progress.total) }}
          </span>
        </div>
      </div>
      <div v-if="error" class="error-msg" style="margin-top: 14px">{{ error }}</div>
    </div>

    <!-- Search phase -->
    <div v-else-if="phase === 'search'" style="margin-top: 20px">
      <div style="display: flex; gap: 10px; margin-bottom: 16px">
        <input
          v-model="searchQuery"
          type="text"
          placeholder="Type HWID pattern (e.g. ATLAS, OCTOPUS) or leave blank for all…"
          @keyup.enter="runSearch"
        />
        <button class="primary" @click="runSearch" :disabled="searching">
          {{ searching ? 'Searching…' : 'Search' }}
        </button>
      </div>

      <div v-if="error" class="error-msg" style="margin-bottom: 14px">{{ error }}</div>

      <div v-if="results.length === 0 && searched" class="card">
        No STABLE models found matching that pattern.
      </div>

      <div v-else class="results-list">
        <div
          v-for="m in results"
          :key="m.index"
          class="model-row"
          :class="{ selected: selected?.index === m.index }"
          @click="selected = m"
        >
          <div class="model-name">{{ m.model }}</div>
          <div class="model-meta">
            <span>{{ m.manufacturer }}</span>
            <span class="sep">·</span>
            <span>Chrome {{ m.chrome_version }}</span>
            <span class="sep">·</span>
            <span class="badge badge-success">STABLE</span>
          </div>
        </div>
      </div>

      <div class="step-actions">
        <span v-if="results.length" style="color: var(--text-muted); font-size: 12px; align-self: center">
          {{ results.length }} result(s)
        </span>
        <button class="secondary" @click="quit()">Quit</button>
        <button
          class="primary"
          :disabled="!selected"
          @click="$emit('selected', selected)"
        >
          Select Model →
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { sendCommand, store } from '../stores/bridge.js'

const emit = defineEmits(['selected'])

function quit() { window.close() }

const phase = ref('download')
const recoveryListPath = ref('')
const searchQuery = ref('')
const results = ref([])
const selected = ref(null)
const searching = ref(false)
const searched = ref(false)
const error = ref('')

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

onMounted(async () => {
  const workdir = await window.api.getWorkdir()
  try {
    const data = await sendCommand({ cmd: 'fetch_recovery_list', workdir })
    recoveryListPath.value = data.dest
    phase.value = 'search'
  } catch (e) {
    error.value = e.message
  }
})

async function runSearch() {
  if (!recoveryListPath.value) return
  searching.value = true
  searched.value = false
  selected.value = null
  error.value = ''
  try {
    const data = await sendCommand({
      cmd: 'search_models',
      json_path: recoveryListPath.value,
      pattern: searchQuery.value.trim()
    })
    results.value = data.models
    searched.value = true
  } catch (e) {
    error.value = e.message
  } finally {
    searching.value = false
  }
}
</script>

<style scoped>
.subtitle { color: var(--text-muted); margin-top: 6px; }
.progress-label { font-size: 12px; color: var(--text-muted); margin-top: 6px; display: flex; justify-content: space-between; }
.results-list { display: flex; flex-direction: column; gap: 6px; max-height: 360px; overflow-y: auto; }
.model-row {
  padding: 12px 16px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  cursor: pointer;
  transition: border-color 0.15s;
}
.model-row:hover { border-color: var(--accent); }
.model-row.selected { border-color: var(--accent); background: #1a2a3d; }
.model-name { font-weight: 600; }
.model-meta { font-size: 12px; color: var(--text-muted); margin-top: 4px; display: flex; gap: 6px; align-items: center; }
.sep { opacity: 0.4; }
</style>
