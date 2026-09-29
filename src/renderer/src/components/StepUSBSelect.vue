<template>
  <div>
    <h1>Select USB Drive(s)</h1>
    <p class="subtitle">
      Only removable USB storage devices are listed.
      <strong style="color: var(--warning)">All data will be erased.</strong>
    </p>

    <div v-if="loading" style="margin-top: 20px; color: var(--text-muted)">Scanning for USB devices…</div>

    <div v-else-if="error" class="error-msg" style="margin-top: 20px">{{ error }}</div>

    <div v-else-if="Object.keys(drives).length === 0" class="card" style="margin-top: 20px">
      No USB drives detected. Plug in a drive and
      <button class="secondary" style="display: inline-flex; padding: 4px 10px; margin-left: 6px" @click="refresh">
        Refresh
      </button>
    </div>

    <div v-else style="margin-top: 20px">
      <div style="display: flex; justify-content: flex-end; margin-bottom: 8px">
        <button class="secondary" style="padding: 4px 12px; font-size: 12px" @click="toggleSelectAll">
          {{ allSelected ? 'Deselect All' : 'Select All' }}
        </button>
      </div>
      <div class="drive-list">
        <label
          v-for="(info, dev) in drives"
          :key="dev"
          class="drive-row"
          :class="{ selected: selectedDrives.includes(dev) }"
        >
          <input
            type="checkbox"
            :value="dev"
            v-model="selectedDrives"
            style="margin-right: 12px"
          />
          <div class="drive-info">
            <div class="drive-name">{{ info.vendor }} {{ info.model }}</div>
            <div class="drive-meta">
              <code>/dev/{{ dev }}</code>
              <span class="sep">·</span>
              <span>{{ info.human_readable_size }}</span>
            </div>
          </div>
        </label>
      </div>

      <div class="warning-box" v-if="selectedDrives.length">
        Writing to {{ selectedDrives.length }} device(s):
        {{ selectedDrives.map(d => '/dev/' + d).join(', ') }}
      </div>

      <div class="step-actions">
        <button class="secondary" @click="$emit('back')">← Back</button>
        <button class="secondary" @click="refresh">Refresh</button>
        <button class="secondary" @click="quit()">Quit</button>
        <button
          class="danger"
          :disabled="selectedDrives.length === 0"
          @click="$emit('selected', selectedDrives)"
        >
          Proceed — Erase &amp; Flash →
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { sendCommand } from '../stores/bridge.js'

defineEmits(['selected', 'back'])

function quit() { window.close() }

const loading = ref(true)
const drives = ref({})
const selectedDrives = ref([])
const error = ref('')

const allSelected = computed(() => {
  const keys = Object.keys(drives.value)
  return keys.length > 0 && keys.every(d => selectedDrives.value.includes(d))
})

function toggleSelectAll() {
  if (allSelected.value) {
    selectedDrives.value = []
  } else {
    selectedDrives.value = Object.keys(drives.value)
  }
}

async function refresh() {
  loading.value = true
  error.value = ''
  selectedDrives.value = []
  try {
    const data = await sendCommand({ cmd: 'get_usb_drives' })
    drives.value = data.drives
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

onMounted(refresh)
</script>

<style scoped>
.subtitle { color: var(--text-muted); margin-top: 6px; }
.drive-list { display: flex; flex-direction: column; gap: 8px; }
.drive-row {
  display: flex;
  align-items: center;
  padding: 14px 16px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  cursor: pointer;
}
.drive-row:hover { border-color: var(--warning); }
.drive-row.selected { border-color: var(--warning); background: #3d2e1a; }
.drive-name { font-weight: 600; }
.drive-meta { font-size: 12px; color: var(--text-muted); margin-top: 3px; display: flex; gap: 6px; align-items: center; }
.sep { opacity: 0.4; }
code { background: var(--surface-2); padding: 1px 5px; border-radius: 3px; font-size: 11px; }
.warning-box {
  margin-top: 14px;
  padding: 10px 14px;
  background: #3d2e1a;
  border: 1px solid var(--warning);
  border-radius: var(--radius);
  color: var(--warning);
  font-size: 13px;
}
</style>
