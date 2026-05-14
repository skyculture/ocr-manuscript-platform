<template>
  <div class="graph-annotation-view">
    <div class="graph-summary">
      <div class="summary-cards">
        <div class="summary-card">
          <div class="summary-value">{{ data.length }}</div>
          <div class="summary-label">节点总数</div>
        </div>
        <div class="summary-card">
          <div class="summary-value">{{ edgeCount }}</div>
          <div class="summary-label">边总数</div>
        </div>
        <div class="summary-card">
          <div class="summary-value">{{ typeCount }}</div>
          <div class="summary-label">节点类型</div>
        </div>
      </div>
      <div class="type-stats">
        <span v-for="(count, type) in typeStats" :key="type"
              class="type-stat-badge" :class="getTypeClass(type)">
          {{ getTypeLabel(type) }}: {{ count }}
        </span>
      </div>
    </div>

    <div class="graph-sections">
      <div class="graph-section">
        <details class="json-details">
          <summary>点击查看节点列表</summary>
          <div class="nodes-table-wrapper">
            <table class="nodes-table">
              <thead>
                <tr>
                  <th>node_id</th>
                  <th>类型</th>
                  <th>转写文本</th>
                  <th>位置 (points)</th>
                  <th>属性</th>
                  <th>边</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="node in data" :key="node.node_id">
                  <td class="cell-id">{{ node.node_id }}</td>
                  <td><span class="type-badge" :class="getTypeClass(node.type)">{{ getTypeLabel(node.type) }}</span></td>
                  <td class="cell-transcription">{{ node.transcription || '' }}</td>
                  <td class="cell-points">{{ formatPoints(node.points) }}</td>
                  <td class="cell-attrs">{{ formatAttrs(node.attributes) }}</td>
                  <td class="cell-edges" v-html="formatEdges(node.edges)"></td>
                </tr>
              </tbody>
            </table>
          </div>
        </details>
      </div>

      <div class="graph-section">
        <details class="json-details">
          <summary>点击查看边关系</summary>
          <div class="edges-table-wrapper">
            <table v-if="allEdges.length > 0" class="edges-table">
              <thead><tr><th>源节点</th><th>关系</th><th>目标节点</th></tr></thead>
              <tbody>
                <tr v-for="edge in allEdges" :key="edge.source + edge.target + edge.relation">
                  <td class="cell-id">{{ edge.source }}</td>
                  <td><span class="relation-badge">{{ edge.relation }}</span></td>
                  <td class="cell-id">{{ edge.target }}</td>
                </tr>
              </tbody>
            </table>
            <p v-else class="no-edges">无边关系</p>
          </div>
        </details>
      </div>

      <div class="graph-section" v-if="item.image_url">
        <div class="section-subtitle-row">
          <h3 class="section-subtitle">🖼️ 图片预览</h3>
          <div class="view-controls">
            <div class="view-toggle">
              <button class="toggle-btn" :class="{ active: viewMode === 'original' }" @click="viewMode = 'original'">原始图片</button>
              <button class="toggle-btn" :class="{ active: viewMode === 'annotated' }" @click="viewMode = 'annotated'">标注图片</button>
            </div>
            <label v-if="viewMode === 'annotated'" class="label-toggle">
              <input type="checkbox" v-model="showLabels" @change="drawAnnotations()">
              <span class="label-toggle-text">显示标注文字</span>
            </label>
          </div>
        </div>
        <div class="annotation-image-viewer">
          <img v-if="viewMode === 'original'" :src="item.image_url" :alt="item.name" loading="lazy">
          <div v-else class="annotated-canvas-wrapper">
            <canvas ref="annotatedCanvas"></canvas>
            <div v-if="canvasLoading" class="canvas-loading">加载标注中...</div>
          </div>
        </div>
      </div>

      <div class="graph-section">
        <h3 class="section-subtitle">📋 原始JSON</h3>
        <details class="json-details">
          <summary>点击展开查看原始JSON数据</summary>
          <pre class="json-display"><code v-html="highlightedJson"></code></pre>
        </details>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch, nextTick } from 'vue'

const props = defineProps({
  item: Object,
  data: Array
})

const viewMode = ref('original')
const showLabels = ref(true)
const annotatedCanvas = ref(null)
const canvasLoading = ref(false)

const typeColorMap = {
  'TEXT': { border: '#2196F3', bg: 'rgba(33,150,243,0.12)', label: '#1565C0' },
  'MAIN_TEXT': { border: '#1976D2', bg: 'rgba(25,118,210,0.12)', label: '#0D47A1' },
  'SIGNATURE': { border: '#FF9800', bg: 'rgba(255,152,0,0.12)', label: '#E65100' },
  'SEAL': { border: '#F44336', bg: 'rgba(244,67,54,0.12)', label: '#C62828' },
  'SYMBOL_PLACEHOLDER': { border: '#9C27B0', bg: 'rgba(156,39,176,0.12)', label: '#6A1B9A' },
  'ILLUSTRATION': { border: '#4CAF50', bg: 'rgba(76,175,80,0.12)', label: '#2E7D32' },
  'MARGINALIA': { border: '#FF5722', bg: 'rgba(255,87,34,0.12)', label: '#BF360C' },
  'PAGE_NUMBER': { border: '#607D8B', bg: 'rgba(96,125,139,0.12)', label: '#37474F' },
  'HEADER': { border: '#795548', bg: 'rgba(121,85,72,0.12)', label: '#4E342E' },
  'FOOTER': { border: '#795548', bg: 'rgba(121,85,72,0.12)', label: '#4E342E' },
  'DELETE_TEXT': { border: '#B71C1C', bg: 'rgba(183,28,28,0.12)', label: '#B71C1C' }
}

function getNodeColor(type) {
  return typeColorMap[type] || { border: '#9E9E9E', bg: 'rgba(158,158,158,0.12)', label: '#616161' }
}

function drawAnnotations() {
  const canvas = annotatedCanvas.value
  if (!canvas || !props.item.image_url) return

  canvasLoading.value = true
  const img = new Image()
  img.crossOrigin = 'anonymous'
  img.onload = () => {
    const ctx = canvas.getContext('2d')
    canvas.width = img.naturalWidth
    canvas.height = img.naturalHeight

    ctx.drawImage(img, 0, 0)

    const nodesWithPoints = props.data.filter(node => node.points && Array.isArray(node.points) && node.points.length >= 2)

    nodesWithPoints.forEach(node => {
      const pts = node.points
      const color = getNodeColor(node.type)

      const xs = pts.map(p => p[0])
      const ys = pts.map(p => p[1])
      const minX = Math.min(...xs)
      const minY = Math.min(...ys)
      const maxX = Math.max(...xs)
      const maxY = Math.max(...ys)

      ctx.fillStyle = color.bg
      ctx.fillRect(minX, minY, maxX - minX, maxY - minY)

      ctx.strokeStyle = color.border
      ctx.lineWidth = Math.max(2, Math.round(img.naturalWidth / 500))
      ctx.strokeRect(minX, minY, maxX - minX, maxY - minY)

      if (showLabels.value) {
        const label = getTypeLabel(node.type) + (node.transcription ? `: ${node.transcription.substring(0, 12)}` : '')
        const fontSize = Math.max(14, Math.round(img.naturalWidth / 60))
        ctx.font = `bold ${fontSize}px "Noto Sans SC", sans-serif`
        const textMetrics = ctx.measureText(label)
        const labelH = fontSize + 8
        const labelW = textMetrics.width + 12

        let labelX = minX
        let labelY = minY - labelH
        if (labelY < 0) labelY = minY

        ctx.fillStyle = color.border
        ctx.fillRect(labelX, labelY, labelW, labelH)

        ctx.fillStyle = '#FFFFFF'
        ctx.textBaseline = 'middle'
        ctx.fillText(label, labelX + 6, labelY + labelH / 2)
      }
    })

    canvasLoading.value = false
  }
  img.onerror = () => {
    canvasLoading.value = false
  }
  img.src = props.item.image_url
}

watch(viewMode, async (val) => {
  if (val === 'annotated') {
    await nextTick()
    drawAnnotations()
  }
})

const typeStats = computed(() => {
  const stats = {}
  props.data.forEach(node => {
    stats[node.type] = (stats[node.type] || 0) + 1
  })
  return stats
})

const edgeCount = computed(() => {
  let count = 0
  props.data.forEach(node => {
    count += (node.edges || []).length
  })
  return count
})

const typeCount = computed(() => Object.keys(typeStats.value).length)

const allEdges = computed(() => {
  const edges = []
  props.data.forEach(node => {
    (node.edges || []).forEach(edge => {
      edges.push({ source: node.node_id, target: edge.target, relation: edge.relation })
    })
  })
  return edges
})

const highlightedJson = computed(() => {
  return syntaxHighlight(JSON.stringify(props.data, null, 2))
})

function getTypeLabel(type) {
  const labels = {
    'TEXT': '文本', 'MAIN_TEXT': '正文', 'SIGNATURE': '签名', 'SEAL': '印章',
    'SYMBOL_PLACEHOLDER': '符号占位', 'ILLUSTRATION': '插图',
    'MARGINALIA': '批注', 'PAGE_NUMBER': '页码', 'HEADER': '页眉', 'FOOTER': '页脚',
    'DELETE_TEXT': '删除文本'
  }
  return labels[type] || type
}

function getTypeClass(type) {
  const map = {
    'TEXT': 'type-text', 'MAIN_TEXT': 'type-text', 'SIGNATURE': 'type-signature', 'SEAL': 'type-seal',
    'SYMBOL_PLACEHOLDER': 'type-symbol', 'ILLUSTRATION': 'type-illustration', 'MARGINALIA': 'type-marginalia',
    'DELETE_TEXT': 'type-seal'
  }
  return map[type] || 'type-other'
}

function formatPoints(points) {
  if (!points || !Array.isArray(points)) return '-'
  return points.map(p => `(${p[0]},${p[1]})`).join(' → ')
}

function formatAttrs(attrs) {
  if (!attrs || Object.keys(attrs).length === 0) return '-'
  return Object.entries(attrs).map(([k, v]) => `${k}=${v}`).join(', ')
}

function formatEdges(edges) {
  if (!edges || edges.length === 0) return '-'
  return edges.map(e => `→${escapeHtml(e.target)}(${e.relation})`).join('<br>')
}

function escapeHtml(text) {
  const div = document.createElement('div')
  div.textContent = String(text)
  return div.innerHTML
}

function syntaxHighlight(json) {
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
</script>
