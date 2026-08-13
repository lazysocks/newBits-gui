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

    <div v-if="!started" class="step-actions" style="margin-top: 20px">
      <button class="danger" @click="apply">Write Image Now</button>
    </div>

    <div v-else style="margin-top: 20px">
      <div class="phase-block" :class="{ 'phase-done': done, 'phase-error': !!error, 'phase-active': started && !done && !error }">
        <div class="phase-header">
          <h3>Writing…</h3>
          <span class="badge" :class="done ? 'badge-success' : error ? 'badge-error' : 'badge-warning'">
            {{ done ? 'Done' : error ? 'Error' : 'Running' }}
          </span>
        </div>
        <p v-if="!done && !error" style="font-size: 12px; color: var(--text-muted); margin-top: 8px">
          dd is writing in parallel to all selected drives. This may take several minutes.
        </p>
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
import { ref, watch, nextTick, toRaw } from 'vue'
import { sendCommand, store } from '../stores/bridge.js'

const props = defineProps({
  imageFile: String,
  drives: Array,
  model: Object
})
defineEmits(['complete', 'more'])

const started = ref(false)
const done = ref(false)
const error = ref('')
const logs = ref([])
const logEl = ref(null)

watch(() => store.logs.length, async () => {
  const last = store.logs[store.logs.length - 1]
  if (last) logs.value.push(last)
  await nextTick()
  if (logEl.value) logEl.value.scrollTop = logEl.value.scrollHeight
})

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
</style>
