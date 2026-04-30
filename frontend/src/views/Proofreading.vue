<template>
  <div class="page-container">
    <div class="page-header">
      <h1 class="page-title">✅ 人工校对结果展示</h1>
      <p class="page-subtitle">查看专业人员校对后的结果，对比原始识别与校对差异</p>
    </div>
    <div class="toolbar">
      <div class="toolbar-left">
        <button class="btn btn-primary" @click="loadData">🔄 刷新数据</button>
        <span class="data-count">共 {{ items.length }} 条记录</span>
      </div>
      <div class="toolbar-right">
        <button class="btn btn-secondary" @click="showUpload = !showUpload">📤 上传校对结果</button>
      </div>
    </div>

    <div class="upload-panel" v-if="showUpload">
      <h3>上传校对结果</h3>
      <form @submit.prevent="uploadResult">
        <div class="form-group">
          <label>JSON结果文件（必需）：</label>
          <input type="file" name="json_file" accept=".json" required ref="jsonInput">
        </div>
        <div class="form-group">
          <label>校对图片（可选）：</label>
          <input type="file" name="image_file" accept="image/*" ref="imageInput">
        </div>
        <button type="submit" class="btn btn-primary">上传</button>
      </form>
    </div>

    <div v-if="items.length === 0" class="empty-state">
      <div class="empty-icon">📭</div>
      <p>暂无校对结果，请上传校对数据</p>
    </div>

    <div v-else class="proofreading-cards">
      <div v-for="item in items" :key="item.name" class="proofreading-card">
        <div class="proofreading-card-header">
          <div style="display:flex;justify-content:space-between;align-items:flex-start;">
            <div>
              <h2 class="proofreading-card-title">{{ item.data.document_name || item.name }}</h2>
              <div class="proofreading-meta">
                <span class="meta-item">👤 校对人员：{{ item.data.proofreader || '未知' }}</span>
                <span class="meta-item">📅 校对日期：{{ item.data.proofread_date || '未知' }}</span>
              </div>
            </div>
            <button class="btn-delete" @click="deleteItem(item.name)" title="删除">✕</button>
          </div>
        </div>
        <div class="proofreading-card-body">
          <div class="proofreading-section" v-if="Object.keys(item.data.statistics || {}).length > 0">
            <h3 class="section-subtitle">📊 校对统计</h3>
            <div class="stats-grid">
              <div v-if="item.data.statistics.total_chars !== undefined" class="stat-card">
                <div class="stat-value">{{ item.data.statistics.total_chars }}</div>
                <div class="stat-label">总字符数</div>
              </div>
              <div v-if="item.data.statistics.error_chars !== undefined" class="stat-card stat-error">
                <div class="stat-value">{{ item.data.statistics.error_chars }}</div>
                <div class="stat-label">错误字符数</div>
              </div>
              <div v-if="item.data.statistics.accuracy !== undefined" class="stat-card stat-success">
                <div class="stat-value">{{ (item.data.statistics.accuracy * 100).toFixed(1) }}%</div>
                <div class="stat-label">准确率</div>
              </div>
            </div>
            <div class="error-types" v-if="Object.keys(item.data.statistics.error_types || {}).length > 0">
              <h4>错误类型分布</h4>
              <div class="error-types-chart">
                <div v-for="(count, type) in item.data.statistics.error_types" :key="type" class="error-type-row">
                  <span class="error-type-name">{{ type }}</span>
                  <div class="error-type-bar-bg">
                    <div class="error-type-bar" :style="{ width: (count / maxErrorCount(item.data.statistics.error_types) * 100) + '%' }"></div>
                  </div>
                  <span class="error-type-count">{{ count }}</span>
                </div>
              </div>
            </div>
          </div>

          <div class="proofreading-section" v-if="item.data.original_text || item.data.corrected_text">
            <h3 class="section-subtitle">📝 文本对比</h3>
            <div class="text-compare">
              <div class="text-panel">
                <div class="text-panel-header">原始识别文本</div>
                <div class="text-panel-body">{{ item.data.original_text || '' }}</div>
              </div>
              <div class="text-panel">
                <div class="text-panel-header">校对后文本</div>
                <div class="text-panel-body" v-html="generateDiff(item.data.original_text || '', item.data.corrected_text || '')"></div>
              </div>
            </div>
          </div>

          <div class="proofreading-section" v-if="(item.data.corrections || []).length > 0">
            <h3 class="section-subtitle">🔍 修改详情（共 {{ item.data.corrections.length }} 处）</h3>
            <div class="corrections-table">
              <div class="corrections-header">
                <span>位置</span><span>原文</span><span>修改为</span><span>类型</span><span>说明</span>
              </div>
              <div v-for="(c, ci) in item.data.corrections" :key="ci" class="corrections-row">
                <span class="corr-pos">{{ c.position !== undefined ? c.position : '-' }}</span>
                <span class="corr-orig">{{ c.original || '' }}</span>
                <span class="corr-fixed">{{ c.corrected || '' }}</span>
                <span><span class="type-badge" :class="'type-' + getErrorTypeClass(c.type)">{{ c.type || '-' }}</span></span>
                <span class="corr-note">{{ c.note || '-' }}</span>
              </div>
            </div>
          </div>

          <div class="proofreading-section" v-if="item.has_image">
            <h3 class="section-subtitle">🖼️ 校对图片</h3>
            <div class="proofreading-image">
              <img :src="item.image_url" :alt="item.name" loading="lazy">
            </div>
          </div>

          <div class="proofreading-section">
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
import { proofreadingApi } from '../api'

const items = ref([])
const showUpload = ref(false)
const jsonInput = ref(null)
const imageInput = ref(null)

async function loadData() {
  try {
    const resp = await proofreadingApi.list()
    items.value = resp.data
  } catch (e) {
    console.error('加载数据失败:', e)
  }
}

async function uploadResult() {
  const form = jsonInput.value.closest('form')
  const formData = new FormData(form)
  try {
    const resp = await proofreadingApi.upload(formData)
    if (resp.data.success) {
      alert('校对结果上传成功！')
      showUpload.value = false
      loadData()
    } else {
      alert('上传失败：' + (resp.data.error || '未知错误'))
    }
  } catch (err) {
    alert('上传出错：' + err.message)
  }
}

function maxErrorCount(errorTypes) {
  return Math.max(...Object.values(errorTypes))
}

function getErrorTypeClass(type) {
  const map = {
    '错别字': 'typo', '漏字': 'missing', '多字': 'extra',
    '标点错误': 'punctuation', '格式错误': 'format'
  }
  return map[type] || 'other'
}

function escapeHtml(text) {
  const div = document.createElement('div')
  div.textContent = text
  return div.innerHTML
}

function generateDiff(original, corrected) {
  if (!original && !corrected) return ''
  let html = ''
  let i = 0, j = 0
  while (i < original.length || j < corrected.length) {
    if (i < original.length && j < corrected.length && original[i] === corrected[j]) {
      html += escapeHtml(corrected[j])
      i++; j++
    } else {
      let oChar = i < original.length ? escapeHtml(original[i]) : ''
      let cChar = j < corrected.length ? escapeHtml(corrected[j]) : ''
      if (oChar && cChar) {
        html += `<span class="diff-removed" title="原文：${oChar}">${oChar}</span>`
        html += `<span class="diff-added" title="修改为：${cChar}">${cChar}</span>`
        i++; j++
      } else if (oChar) {
        html += `<span class="diff-removed">${oChar}</span>`
        i++
      } else {
        html += `<span class="diff-added">${cChar}</span>`
        j++
      }
    }
  }
  return html
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
  if (!confirm(`确定删除校对结果 "${name}"？`)) return
  try {
    const resp = await proofreadingApi.delete(name)
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
