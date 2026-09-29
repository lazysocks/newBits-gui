<template>
  <div>
    <h1>Cleanup</h1>
    <p class="subtitle">Remove temporary files from <code>/tmp/tmp.newbits</code>.</p>

    <div class="card" style="margin-top: 20px">
      <div v-for="f in files" :key="f" class="file-item">
        <span class="file-status">{{ cleaned.includes(f) ? '✓' : '·' }}</span>
        <code>{{ f }}</code>
      </div>
    </div>

    <div v-if="error" class="error-msg" style="margin-top: 14px">{{ error }}</div>

    <div class="step-actions">
      <button class="primary" :disabled="cleaning || done" @click="clean">
        {{ done ? 'Cleaned' : cleaning ? 'Cleaning…' : 'Delete Temp Files' }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, toRaw } from 'vue'
import { sendCommand } from '../stores/bridge.js'

const props = defineProps({ files: Array })
const emit = defineEmits(['done'])

const cleaning = ref(false)
const done = ref(false)
const cleaned = ref([])
const error = ref('')

async function clean() {
  cleaning.value = true
  error.value = ''
  try {
    await sendCommand({ cmd: 'cleanup', files: toRaw(props.files) })
    cleaned.value = [...props.files]
    done.value = true
    setTimeout(() => emit('done'), 800)
  } catch (e) {
    error.value = e.message
  } finally {
    cleaning.value = false
  }
}
</script>

<style scoped>
.subtitle { color: var(--text-muted); margin-top: 6px; }
.file-item { display: flex; align-items: center; gap: 10px; padding: 6px 0; font-size: 13px; }
.file-status { color: var(--success); font-weight: bold; width: 14px; }
code { background: var(--surface-2); padding: 2px 6px; border-radius: 3px; font-size: 12px; }
</style>
