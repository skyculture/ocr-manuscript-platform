<template>
  <div class="detail-panels-vertical">
    <div class="detail-panel">
      <div class="panel-header-row">
        <div class="panel-header">图片预览</div>
        <div class="view-controls" v-if="item.image_url && hasAnnotationData">
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
      <div class="image-viewer">
        <template v-if="item.image_url">
          <img v-if="viewMode === 'original'" :src="item.image_url" :alt="item.name">
          <div v-else class="annotated-canvas-wrapper">
            <canvas ref="annotatedCanvas"></canvas>
            <div v-if="canvasLoading" class="canvas-loading">加载标注中...</div>
          </div>
        </template>
        <div v-else class="no-json">暂无图片</div>
      </div>
    </div>
    <div class="detail-panel">
      <div class="panel-header">标注数据 (JSON)</div>
      <div class="json-viewer">
        <template v-if="item.has_json && item.json_data">
          <details class="json-details">
            <summary>点击展开查看JSON数据</summary>
            <pre class="json-display"><code v-html="highlightedJson"></code></pre>
          </details>
        </template>
        <div v-else class="no-json">暂无标注数据</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch, nextTick } from 'vue'

const props = defineProps({
  item: Object
})

const viewMode = ref('original')
const showLabels = ref(true)
const annotatedCanvas = ref(null)
const canvasLoading = ref(false)

const annotationItems = computed(() => {
  if (!props.item.json_data) return []
  const data = props.item.json_data
  let itemsList = []
  if (Array.isArray(data)) {
    itemsList = data
  } else if (data && typeof data === 'object' && Array.isArray(data.nodes)) {
    itemsList = data.nodes
  }
  return itemsList.filter(item => {
    const points = extractPoints(item)
    return points !== null
  }).map(item => ({
    points: extractPoints(item),
    label: extractLabel(item)
  }))
})

const hasAnnotationData = computed(() => annotationItems.value.length > 0)

function extractPoints(item) {
  if (!item || typeof item !== 'object') return null
  if (item.points && Array.isArray(item.points) && item.points.length >= 2) {
    return item.points
  }
  if (item.bbox && Array.isArray(item.bbox) && item.bbox.length === 4) {
    const [x1, y1, x2, y2] = item.bbox
    return [[x1, y1], [x2, y1], [x2, y2], [x1, y2]]
  }
  if (item.bounding_box && Array.isArray(item.bounding_box) && item.bounding_box.length === 4) {
    const [x1, y1, x2, y2] = item.bounding_box
    return [[x1, y1], [x2, y1], [x2, y2], [x1, y2]]
  }
  if (item.position && typeof item.position === 'object') {
    const p = item.position
    if (p.x !== undefined && p.y !== undefined && p.width !== undefined && p.height !== undefined) {
      return [[p.x, p.y], [p.x + p.width, p.y], [p.x + p.width, p.y + p.height], [p.x, p.y + p.height]]
    }
  }
  return null
}

function extractLabel(item) {
  return item.transcription || item.text || item.label || item.type || ''
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

    const items = annotationItems.value
    const colors = [
      { border: '#2196F3', bg: 'rgba(33,150,243,0.12)' },
      { border: '#F44336', bg: 'rgba(244,67,54,0.12)' },
      { border: '#4CAF50', bg: 'rgba(76,175,80,0.12)' },
      { border: '#FF9800', bg: 'rgba(255,152,0,0.12)' },
      { border: '#9C27B0', bg: 'rgba(156,39,176,0.12)' },
      { border: '#FF5722', bg: 'rgba(255,87,34,0.12)' }
    ]

    items.forEach((item, idx) => {
      const pts = item.points
      const color = colors[idx % colors.length]

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

      if (showLabels.value && item.label) {
        const displayLabel = item.label.length > 15 ? item.label.substring(0, 15) + '...' : item.label
        const fontSize = Math.max(14, Math.round(img.naturalWidth / 60))
        ctx.font = `bold ${fontSize}px "Noto Sans SC", sans-serif`
        const textMetrics = ctx.measureText(displayLabel)
        const labelH = fontSize + 8
        const labelW = textMetrics.width + 12

        let labelX = minX
        let labelY = minY - labelH
        if (labelY < 0) labelY = minY

        ctx.fillStyle = color.border
        ctx.fillRect(labelX, labelY, labelW, labelH)

        ctx.fillStyle = '#FFFFFF'
        ctx.textBaseline = 'middle'
        ctx.fillText(displayLabel, labelX + 6, labelY + labelH / 2)
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

const highlightedJson = computed(() => {
  if (!props.item.json_data) return ''
  return syntaxHighlight(JSON.stringify(props.item.json_data, null, 2))
})

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
