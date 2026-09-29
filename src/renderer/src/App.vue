<template>
  <div class="layout">
    <header class="topbar">
      <span class="title">newBits</span>
      <div class="steps-nav">
        <span
          v-for="(s, i) in stepList"
          :key="s.key"
          class="step-dot"
          :class="{
            active: step === s.key,
            done: stepIndex > i,
            disabled: stepIndex < i
          }"
        >{{ s.label }}</span>
      </div>
    </header>

    <main class="content">
      <StepPrivilege
        v-if="step === 'privilege'"
        @complete="onPrivilegeDone"
      />
      <StepModelSelect
        v-else-if="step === 'model'"
        @selected="onModelSelected"
      />
      <StepUSBSelect
        v-else-if="step === 'usb'"
        @selected="onUSBSelected"
      />
      <StepDownload
        v-else-if="step === 'download'"
        :model="selectedModel"
        @complete="onDownloadDone"
      />
      <StepApply
        v-else-if="step === 'apply'"
        :image-file="imageFile"
        :drives="selectedDrives"
        :model="selectedModel"
        @complete="onApplyDone"
        @more="onMoreDrives"
      />
      <StepCleanup
        v-else-if="step === 'cleanup'"
        :files="tempFiles"
        @done="onCleanupDone"
      />
      <div v-else-if="step === 'finished'" class="finished">
        <div class="finished-icon">✓</div>
        <h2>All done!</h2>
        <p>Your USB drive(s) are ready. You can safely remove them.</p>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { initBridge } from './stores/bridge.js'
import StepPrivilege from './components/StepPrivilege.vue'
import StepModelSelect from './components/StepModelSelect.vue'
import StepUSBSelect from './components/StepUSBSelect.vue'
import StepDownload from './components/StepDownload.vue'
import StepApply from './components/StepApply.vue'
import StepCleanup from './components/StepCleanup.vue'

const stepList = [
  { key: 'privilege', label: 'Privileges' },
  { key: 'model',     label: 'Model'      },
  { key: 'usb',       label: 'USB'        },
  { key: 'download',  label: 'Download'   },
  { key: 'apply',     label: 'Apply'      },
  { key: 'cleanup',   label: 'Cleanup'    },
]

const step = ref('privilege')
const stepIndex = computed(() => stepList.findIndex(s => s.key === step.value))

// Cross-step state
const selectedModel = ref(null)
const selectedDrives = ref([])
const imageFile = ref('')
const tempFiles = ref([])

onMounted(() => {
  initBridge()
})

onUnmounted(() => {
  window.api.removeAllBridgeListeners()
})

function onPrivilegeDone() {
  step.value = 'model'
}

function onModelSelected(model) {
  selectedModel.value = model
  step.value = 'usb'
}

function onUSBSelected(drives) {
  selectedDrives.value = drives
  step.value = imageFile.value ? 'apply' : 'download'
}

function onDownloadDone({ imagePath, zipPath }) {
  imageFile.value = imagePath
  tempFiles.value = [zipPath, imagePath]
  step.value = 'apply'
}

function onApplyDone() {
  step.value = 'cleanup'
}

function onMoreDrives() {
  selectedDrives.value = []
  step.value = 'usb'
}

function onCleanupDone() {
  step.value = 'finished'
}
</script>

<style scoped>
.layout {
  display: flex;
  flex-direction: column;
  height: 100vh;
}

.topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 24px;
  background: var(--surface);
  border-bottom: 1px solid var(--border);
  flex-shrink: 0;
}

.title {
  font-weight: 700;
  font-size: 15px;
  color: var(--accent);
  letter-spacing: 0.5px;
}

.steps-nav {
  display: flex;
  align-items: center;
  gap: 6px;
}

.step-dot {
  padding: 3px 12px;
  border-radius: 20px;
  font-size: 11px;
  font-weight: 500;
  background: var(--surface-2);
  color: var(--text-muted);
  border: 1px solid var(--border);
}
.step-dot.active {
  background: var(--accent);
  color: #fff;
  border-color: var(--accent);
}
.step-dot.done {
  background: #1a3d1a;
  color: var(--success);
  border-color: var(--success);
}

.content {
  flex: 1;
  overflow-y: auto;
  padding: 28px 32px;
}

.finished {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  gap: 16px;
  text-align: center;
}
.finished-icon {
  font-size: 64px;
  color: var(--success);
}
</style>
