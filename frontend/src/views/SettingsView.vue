<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Check, RefreshLeft } from '@element-plus/icons-vue'
import { fetchSettings, updateSettings } from '../api/settings'

// Defaults from config/default.yaml
const DEFAULTS = {
  detect_confidence: 0.35,
  downward_ratio: 0.55,
  min_vertical_distance: 50,
  min_track_frames: 5,
  roi_required_ratio: 0.5,
  alarm_cooldown_seconds: 10,
  imgsz: 960,
}

const RULES = {
  detect_confidence: { min: 0.1, max: 1.0, label: '检测置信度' },
  downward_ratio: { min: 0.1, max: 1.0, label: '下降帧占比' },
  min_vertical_distance: { min: 10, max: 500, label: '最小垂直位移' },
  min_track_frames: { min: 1, max: 100, label: '最小跟踪帧数' },
  roi_required_ratio: { min: 0, max: 1.0, label: 'ROI内轨迹占比' },
  alarm_cooldown_seconds: { min: 0, max: 300, label: '报警冷却秒数' },
  imgsz: { min: 320, max: 1920, label: '推理图像尺寸' },
}

const TOOLTIPS = {
  detect_confidence: 'YOLO检测置信度阈值，低于此值的检测框将被丢弃（0.1-1.0）',
  downward_ratio: '基于线性回归斜率判定下降的阈值（越大越严格）',
  min_vertical_distance: '目标累计垂直下降位移最小值(像素)，低于此不触发（10-500）',
  min_track_frames: '目标最少被连续跟踪的帧数，低于此不触发（1-100）',
  roi_required_ratio: '轨迹点必须在ROI内的最低占比（0-1.0）',
  alarm_cooldown_seconds: '同一track_id两次报警的最小间隔秒数（0-300）',
  imgsz: 'YOLO推理时的输入图像尺寸，须与训练时一致（320-1920）',
}

const form = reactive({ ...DEFAULTS })
const loading = ref(false)
const saving = ref(false)

async function load() {
  loading.value = true
  try {
    const res = await fetchSettings()
    if (res.data) {
      Object.keys(DEFAULTS).forEach(k => {
        if (res.data[k] !== undefined) form[k] = res.data[k]
      })
    }
  } catch {
    // Backend may not be ready — keep defaults
  } finally {
    loading.value = false
  }
}

function reset() {
  Object.assign(form, DEFAULTS)
}

async function save() {
  // Validate
  for (const [key, rule] of Object.entries(RULES)) {
    const val = form[key]
    if (typeof val !== 'number' || isNaN(val)) {
      ElMessage.warning(`${rule.label} 必须为数字`)
      return
    }
    if (val < rule.min || val > rule.max) {
      ElMessage.warning(`${rule.label} 范围: ${rule.min}-${rule.max}`)
      return
    }
  }

  saving.value = true
  try {
    await updateSettings({ ...form })
    ElMessage.success('参数已保存')
  } catch {
    ElMessage.warning('保存失败，后端可能未就绪')
  } finally {
    saving.value = false
  }
}

onMounted(load)

defineOptions({ name: 'SettingsView' })
</script>

<template>
  <div class="settings-page">


    <div class="form-card" v-loading="loading">
      <div class="form-grid">
        <div v-for="(rule, key) in RULES" :key="key" class="form-item">
          <div class="form-label">
            <span>{{ rule.label }}</span>
            <el-tooltip :content="TOOLTIPS[key]" placement="top">
              <span class="info-icon">?</span>
            </el-tooltip>
          </div>
          <el-input-number
            v-model="form[key]"
            :min="rule.min"
            :max="rule.max"
            :step="key === 'imgsz' ? 32 : key.includes('ratio') || key.includes('confidence') ? 0.05 : 1"
            :precision="key.includes('ratio') || key.includes('confidence') ? 2 : 0"
            size="small"
            controls-position="right"
            style="width:100%"
          />
          <span class="range-hint">{{ rule.min }} – {{ rule.max }}</span>
        </div>
      </div>

      <div class="form-actions">
        <el-button type="primary" :icon="Check" :loading="saving" @click="save">保存参数</el-button>
        <el-button :icon="RefreshLeft" @click="reset">恢复默认</el-button>
      </div>
    </div>

    <div class="desc-card">
      <h3 class="section-title">参数说明</h3>
      <div class="desc-list">
        <div v-for="(rule, key) in RULES" :key="'d' + key" class="desc-row">
          <span class="desc-name">{{ rule.label }}</span>
          <span class="desc-text">{{ TOOLTIPS[key] }}</span>
          <span class="desc-current">当前: {{ form[key] }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.settings-page { max-width: 800px; }

.page-heading {
  margin: 4px 0 24px;
  color: #eaf6ff;
  font-size: 24px;
  font-weight: 700;
}

/* Form */
.form-card {
  background: #101f33;
  border: 1px solid #1e3a5f;
  border-radius: 8px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.24);
  padding: 24px 28px;
  margin-bottom: 24px;
}
.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px 32px;
}
.form-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.form-label {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #eaf6ff;
  font-size: 14px;
  font-weight: 600;
}
.info-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: #1e3a5f;
  color: #91a8c7;
  font-size: 10px;
  cursor: help;
}
.range-hint {
  color: #52657f;
  font-size: 11px;
}
.form-actions {
  margin-top: 24px;
  display: flex;
  gap: 12px;
}

/* Desc */
.desc-card {
  background: #101f33;
  border: 1px solid #1e3a5f;
  border-radius: 8px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.24);
  padding: 18px 22px;
}
.section-title {
  margin: 0 0 14px;
  color: #eaf6ff;
  font-size: 15px;
  font-weight: 600;
}
.desc-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.desc-row {
  display: grid;
  grid-template-columns: 120px 1fr 120px;
  gap: 16px;
  align-items: center;
  padding-bottom: 10px;
  border-bottom: 1px solid #1e3a5f;
}
.desc-name {
  color: #eaf6ff;
  font-size: 13px;
  font-weight: 600;
}
.desc-text {
  color: #91a8c7;
  font-size: 12px;
}
.desc-current {
  color: #00d8ff;
  font-size: 12px;
  font-weight: 600;
  text-align: right;
}
</style>
