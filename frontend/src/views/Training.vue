<template>
  <div class="page-container">
    <div class="page-header">
      <h1 class="page-title">🤖 模型训练结果展示</h1>
      <p class="page-subtitle">查看大模型训练的配置、指标和识别效果</p>
    </div>
    <div class="toolbar">
      <div class="toolbar-left">
        <button class="btn btn-primary" @click="loadData">🔄 刷新数据</button>
        <span class="data-count">共 {{ items.length }} 条记录</span>
      </div>
      <div class="toolbar-right">
        <button class="btn btn-secondary" @click="showUpload = !showUpload">📤 上传训练结果</button>
      </div>
    </div>

    <div class="upload-panel" v-if="showUpload">
      <h3>上传训练结果</h3>
      <form @submit.prevent="uploadResult">
        <div class="form-group">
          <label>JSON结果文件（必需）：</label>
          <input type="file" name="json_file" accept=".json" required ref="jsonInput">
        </div>
        <div class="form-group">
          <label>效果对比图（可选）：</label>
          <input type="file" name="image_file" accept="image/*" ref="imageInput">
        </div>
        <button type="submit" class="btn btn-primary">上传</button>
      </form>
    </div>

    <div v-if="items.length === 0" class="empty-state">
      <div class="empty-icon">📭</div>
      <p>暂无训练结果，请上传训练数据</p>
    </div>

    <div v-else class="training-cards">
      <div v-for="(item, idx) in items" :key="item.name" class="training-card">
        <div class="training-card-header">
          <div style="display:flex;justify-content:space-between;align-items:flex-start;">
            <div>
              <h2 class="training-card-title">{{ item.data.model_name || item.name }}</h2>
              <span class="training-card-filename">{{ item.filename }}</span>
            </div>
            <button class="btn-delete" @click="deleteItem(item.name)" title="删除">✕</button>
          </div>
        </div>
        <div class="training-card-body">
          <div class="training-section" v-if="Object.keys(item.data.training_config || {}).length > 0">
            <h3 class="section-subtitle">⚙️ 训练配置</h3>
            <div class="config-table">
              <div v-for="(value, key) in item.data.training_config" :key="key" class="config-row">
                <span class="config-key">{{ getConfigLabel(key) }}</span>
                <span class="config-value">{{ value }}</span>
              </div>
            </div>
          </div>

          <div class="training-section" v-if="Object.keys(item.data.metrics || {}).length > 0">
            <h3 class="section-subtitle">📊 训练指标</h3>
            <div class="metrics-grid">
              <div v-for="(value, key) in item.data.metrics" :key="key" class="metric-card">
                <div class="metric-value">{{ formatMetric(value) }}</div>
                <div class="metric-label">{{ getMetricLabel(key) }}</div>
              </div>
            </div>
          </div>

          <div class="training-section" v-if="item.has_image">
            <h3 class="section-subtitle">🖼️ 效果对比图</h3>
            <div class="training-image">
              <img :src="item.image_url" :alt="item.name" loading="lazy">
            </div>
          </div>

          <div class="training-section" v-if="(item.data.sample_outputs || []).length > 0">
            <h3 class="section-subtitle">🔍 识别样例</h3>
            <div class="samples-list">
              <div v-for="(s, si) in item.data.sample_outputs" :key="si" class="sample-item">
                <div class="sample-row"><span class="sample-label">输入：</span>{{ s.input || '-' }}</div>
                <div class="sample-row"><span class="sample-label">识别：</span><span class="sample-output">{{ s.output || '-' }}</span></div>
                <div class="sample-row"><span class="sample-label">真实：</span><span class="sample-ground">{{ s.ground_truth || '-' }}</span></div>
              </div>
            </div>
          </div>

          <div class="training-section">
            <h3 class="section-subtitle">📋 完整数据</h3>
            <details class="json-details">
              <summary>查看原始JSON数据</summary>
              <pre class="json-display"><code v-html="highlightJson(item.data)"></code></pre>
            </details>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { trainingApi } from '../api'

const items = ref([])
const showUpload = ref(false)
const jsonInput = ref(null)
const imageInput = ref(null)

async function loadData() {
  try {
    const resp = await trainingApi.list()
    items.value = resp.data
  } catch (e) {
    console.error('加载数据失败:', e)
  }
}

async function uploadResult() {
  const form = jsonInput.value.closest('form')
  const formData = new FormData(form)
  try {
    const resp = await trainingApi.upload(formData)
    if (resp.data.success) {
      alert('训练结果上传成功！')
      showUpload.value = false
      loadData()
    } else {
      alert('上传失败：' + (resp.data.error || '未知错误'))
    }
  } catch (err) {
    alert('上传出错：' + err.message)
  }
}

function formatMetric(value) {
  if (typeof value !== 'number') return value
  return value < 1 ? (value * 100).toFixed(1) + '%' : value.toFixed(4)
}

function getMetricLabel(key) {
  const labels = {
    'accuracy': '准确率', 'precision': '精确率', 'recall': '召回率',
    'f1_score': 'F1分数', 'cer': '字符错误率', 'wer': '词错误率',
    'loss': '损失值', 'val_loss': '验证损失', 'val_accuracy': '验证准确率'
  }
  return labels[key] || key
}

function getConfigLabel(key) {
  const labels = {
    'base_model': '基础模型', 'learning_rate': '学习率', 'epochs': '训练轮数',
    'batch_size': '批大小', 'optimizer': '优化器', 'dropout': 'Dropout',
    'max_length': '最大长度', 'warmup_steps': '预热步数', 'weight_decay': '权重衰减'
  }
  return labels[key] || key
}

function highlightJson(data) {
  let json = JSON.stringify(data, null, 2)
  json = json.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
  return json.replace(/("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?)/g, function (match) {
    let cls = 'json-number'
    if (/^"/.test(match)) {
      if (/:$/.test(match)) { cls = 'json-key' } else { cls = 'json-string' }
    } else if (/true|false/.test(match)) { cls = 'json-boolean' }
    else if (/null/.test(match)) { cls = 'json-null' }
    return '<span class="' + cls + '">' + match + '</span>'
  })
}

async function deleteItem(name) {
  if (!confirm(`确定删除训练结果 "${name}"？`)) return
  try {
    const resp = await trainingApi.delete(name)
    if (resp.data.success) {
      loadData()
    } else {
      alert('删除失败：' + (resp.data.error || '未知错误'))
    }
  } catch (err) {
    alert('删除出错：' + err.message)
  }
}

onMounted(loadData)
</script>
