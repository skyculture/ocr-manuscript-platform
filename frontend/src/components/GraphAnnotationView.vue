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
          </div>
        </div>
        <div class="annotation-image-viewer">
          <img v-if="viewMode === 'original'" :src="item.image_url" :alt="item.name" loading="lazy">
          <div v-else class="annotated-canvas-wrapper">
            <canvas ref="annotatedCanvas" @click="handleCanvasClick"></canvas>
            <div v-if="canvasLoading" class="canvas-loading">加载标注中...</div>
            <div v-if="selectedNodeInfo" class="node-info-tooltip" :style="tooltipStyle">
              <div class="node-info-type">{{ selectedNodeInfo.type }}</div>
              <div class="node-info-transcription">{{ selectedNodeInfo.transcription }}</div>
            </div>
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
const annotatedCanvas = ref(null)
const canvasLoading = ref(false)
const selectedIndex = ref(-1)
const tooltipStyle = ref({})

const typeColorMap = {
  'TEXT': { border: '#1565C0', bg: 'rgba(21,101,192,0.25)', unselected: 'rgba(21,101,192,0.1)' },
  'MAIN_TEXT': { border: '#0D47A1', bg: 'rgba(13,71,161,0.25)', unselected: 'rgba(13,71,161,0.1)' },
  'SIGNATURE': { border: '#E65100', bg: 'rgba(230,81,0,0.25)', unselected: 'rgba(230,81,0,0.1)' },
  'SEAL': { border: '#C62828', bg: 'rgba(198,40,40,0.25)', unselected: 'rgba(198,40,40,0.1)' },
  'SYMBOL_PLACEHOLDER': { border: '#6A1B9A', bg: 'rgba(106,27,154,0.25)', unselected: 'rgba(106,27,154,0.1)' },
  'ILLUSTRATION': { border: '#2E7D32', bg: 'rgba(46,125,50,0.25)', unselected: 'rgba(46,125,50,0.1)' },
  'MARGINALIA': { border: '#BF360C', bg: 'rgba(191,54,12,0.25)', unselected: 'rgba(191,54,12,0.1)' },
  'PAGE_NUMBER': { border: '#0277BD', bg: 'rgba(2,119,189,0.3)', unselected: 'rgba(2,119,189,0.12)' },
  'HEADER': { border: '#4E342E', bg: 'rgba(78,52,46,0.3)', unselected: 'rgba(78,52,46,0.12)' },
  'FOOTER': { border: '#4E342E', bg: 'rgba(78,52,46,0.3)', unselected: 'rgba(78,52,46,0.12)' },
  'DELETE_TEXT': { border: '#880E4F', bg: 'rgba(136,14,79,0.25)', unselected: 'rgba(136,14,79,0.1)' }
}

function getNodeColor(type) {
  return typeColorMap[type] || { border: '#757575', bg: 'rgba(117,117,117,0.25)', unselected: 'rgba(117,117,117,0.1)' }
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

    nodesWithPoints.forEach((node, index) => {
      const pts = node.points
      const color = getNodeColor(node.type)
      const isSelected = selectedIndex.value === index

      const xs = pts.map(p => p[0])
      const ys = pts.map(p => p[1])
      const minX = Math.min(...xs)
      const minY = Math.min(...ys)
      const maxX = Math.max(...xs)
      const maxY = Math.max(...ys)

      ctx.fillStyle = isSelected ? color.bg : color.unselected
      ctx.fillRect(minX, minY, maxX - minX, maxY - minY)

      ctx.strokeStyle = color.border
      ctx.lineWidth = isSelected ? Math.max(4, Math.round(img.naturalWidth / 350)) : Math.max(2, Math.round(img.naturalWidth / 600))
      
      if (isSelected) {
        ctx.shadowColor = color.border
        ctx.shadowBlur = 10
        ctx.shadowOffsetX = 0
        ctx.shadowOffsetY = 0
      }
      ctx.strokeRect(minX, minY, maxX - minX, maxY - minY)
      
      if (isSelected) {
        ctx.shadowBlur = 0
      }
    })

    canvasLoading.value = false
  }
  img.onerror = () => {
    canvasLoading.value = false
  }
  img.src = props.item.image_url
}

function handleCanvasClick(event) {
  const canvas = annotatedCanvas.value
  if (!canvas) return

  const rect = canvas.getBoundingClientRect()
  const scaleX = canvas.width / rect.width
  const scaleY = canvas.height / rect.height
  const x = (event.clientX - rect.left) * scaleX
  const y = (event.clientY - rect.top) * scaleY

  const nodesWithPoints = props.data.filter(node => node.points && Array.isArray(node.points) && node.points.length >= 2)
  let clickedIndex = -1

  for (let i = 0; i < nodesWithPoints.length; i++) {
    const node = nodesWithPoints[i]
    const pts = node.points
    const xs = pts.map(p => p[0])
    const ys = pts.map(p => p[1])
    const minX = Math.min(...xs)
    const minY = Math.min(...ys)
    const maxX = Math.max(...xs)
    const maxY = Math.max(...ys)

    if (x >= minX && x <= maxX && y >= minY && y <= maxY) {
      clickedIndex = i
      break
    }
  }

  if (clickedIndex >= 0 && selectedIndex.value === clickedIndex) {
    selectedIndex.value = -1
  } else {
    selectedIndex.value = clickedIndex
    if (clickedIndex >= 0) {
      const clickedNode = nodesWithPoints[clickedIndex]
      const pts = clickedNode.points
      const xs = pts.map(p => p[0])
      const ys = pts.map(p => p[1])
      const minX = Math.min(...xs)
      const minY = Math.min(...ys)
      const maxX = Math.max(...xs)
      const maxY = Math.max(...ys)

      const textLength = (clickedNode.type?.length || 0) + (clickedNode.transcription?.length || 0)
      const tooltipHeight = Math.min(40 + Math.ceil(textLength / 10) * 16, 120)
      const labelWidth = Math.max(120, Math.min((maxX - minX) * 1.2, Math.min(textLength * 8 + 60, 320)))
      
      const baseGap = 12
      const extraGap = Math.min(Math.floor(textLength / 15) * 8, 28)
      const gap = baseGap + extraGap

      let tooltipX = minX
      let tooltipY = minY - tooltipHeight - gap

      if (tooltipY < 12) {
        tooltipY = maxY + gap
      }

      if (tooltipY + tooltipHeight > canvas.height - 12) {
        tooltipY = canvas.height - tooltipHeight - 12
        if (tooltipY < maxY + gap) {
          tooltipX = maxX + gap
          tooltipY = Math.max(12, Math.min(minY, canvas.height - tooltipHeight - 12))
        }
      }

      if (tooltipX + labelWidth > canvas.width - 12) {
        tooltipX = Math.max(12, minX - labelWidth - gap)
      }

      tooltipStyle.value = {
        left: `${tooltipX}px`,
        top: `${tooltipY}px`,
        maxWidth: `${labelWidth}px`,
        borderColor: getNodeColor(clickedNode.type).border
      }
    }
  }
  drawAnnotations()
}

const selectedNodeInfo = computed(() => {
  if (selectedIndex.value < 0) return null
  const nodesWithPoints = props.data.filter(node => node.points && Array.isArray(node.points) && node.points.length >= 2)
  const node = nodesWithPoints[selectedIndex.value]
  if (!node) return null
  return {
    type: node.type,
    transcription: node.transcription || ''
  }
})

watch(viewMode, async (val) => {
  if (val === 'annotated') {
    await nextTick()
    drawAnnotations()
  }
})

watch(() => props.data, () => {
  selectedIndex.value = -1
}, { deep: true })

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
  return type || ''
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
