<template>
  <div>
    <h1>Privilege Check</h1>
    <p class="subtitle">This tool requires root access to write to USB devices.</p>

    <div v-if="checking" class="status">Checking privileges…</div>

    <div v-else-if="isRoot" class="card" style="margin-top: 20px">
      <div style="display: flex; align-items: center; gap: 12px">
        <span class="badge badge-success">Root</span>
        <span>Running with administrator privileges.</span>
      </div>
      <div class="step-actions">
        <button class="primary" @click="$emit('complete')">Continue →</button>
      </div>
    </div>

    <div v-else class="card" style="margin-top: 20px">
      <div class="error-msg" style="margin-bottom: 16px">
        Not running as root. Disk writes will fail without elevated privileges.
      </div>
      <p style="color: var(--text-muted); margin-bottom: 16px">
        Click <strong>Elevate with pkexec</strong> to restart the backend with root
        access via a system privilege dialog, or launch this app with <code>sudo</code>.
      </p>
      <div class="step-actions" style="justify-content: flex-start">
        <button class="primary" @click="elevate" :disabled="elevating">
          {{ elevating ? 'Requesting…' : 'Elevate with pkexec' }}
        </button>
        <button class="secondary" @click="proceed">
          Continue Anyway (read-only mode)
        </button>
      </div>
      <div v-if="error" class="error-msg" style="margin-top: 12px">{{ error }}</div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { sendCommand, restartBridge } from '../stores/bridge.js'

const emit = defineEmits(['complete'])

const checking = ref(true)
const isRoot = ref(false)
const elevating = ref(false)
const error = ref('')

onMounted(async () => {
  try {
    const data = await sendCommand({ cmd: 'check_sudo' })
    isRoot.value = data.is_root
  } catch (e) {
    error.value = e.message
  } finally {
    checking.value = false
  }
})

async function elevate() {
  elevating.value = true
  error.value = ''
  try {
    await restartBridge(true)
    const data = await sendCommand({ cmd: 'check_sudo' })
    isRoot.value = data.is_root
    if (!isRoot.value) error.value = 'Elevation failed — bridge is still not root.'
  } catch (e) {
    error.value = e.message
  } finally {
    elevating.value = false
  }
}

function proceed() {
  emit('complete')
}
</script>

<style scoped>
.subtitle { color: var(--text-muted); margin-top: 6px; }
.status { margin-top: 20px; color: var(--text-muted); }
code { background: var(--surface-2); padding: 2px 6px; border-radius: 4px; font-size: 12px; }
</style>
