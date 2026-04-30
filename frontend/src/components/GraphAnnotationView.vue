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
        <h3 class="section-subtitle">📋 节点列表</h3>
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
      </div>

      <div class="graph-section">
        <h3 class="section-subtitle">🔗 边关系</h3>
        <div class="edges-table-wrapper">
          <table v-if="allEdges.length > 0" class="edges-table">
            <thead><tr><th>源节点</th><th>关系</th><th>目标节点</th></tr></thead>
            <tbody>
              <tr v-for="edge in allEdges" :key="edge.source + edge.target + edge.relation">
                <td class="cell-id">{{ edge.source }}</td>
                <td><span class="relation-badge">{{ getRelationLabel(edge.relation) }}</span></td>
                <td class="cell-id">{{ edge.target }}</td>
              </tr>
            </tbody>
          </table>
          <p v-else class="no-edges">无边关系</p>
        </div>
      </div>

      <div class="graph-section" v-if="item.image_url">
        <h3 class="section-subtitle">🖼️ 原始图片</h3>
        <div class="annotation-image-viewer">
          <img :src="item.image_url" :alt="item.name" loading="lazy">
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
import { computed } from 'vue'

const props = defineProps({
  item: Object,
  data: Array
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
    'TEXT': '文本', 'SIGNATURE': '签名', 'SEAL': '印章',
    'SYMBOL_PLACEHOLDER': '符号占位', 'ILLUSTRATION': '插图',
    'MARGINALIA': '批注', 'PAGE_NUMBER': '页码', 'HEADER': '页眉', 'FOOTER': '页脚'
  }
  return labels[type] || type
}

function getTypeClass(type) {
  const map = {
    'TEXT': 'type-text', 'SIGNATURE': 'type-signature', 'SEAL': 'type-seal',
    'SYMBOL_PLACEHOLDER': 'type-symbol', 'ILLUSTRATION': 'type-illustration', 'MARGINALIA': 'type-marginalia'
  }
  return map[type] || 'type-other'
}

function getRelationLabel(relation) {
  const labels = {
    'READS_AFTER': '续读', 'REPRESENTS': '代表', 'BELONGS_TO': '属于',
    'AUTHORED': '作者', 'CONTAINS': '包含', 'REFERENCES': '引用', 'ANNOTATES': '批注'
  }
  return labels[relation] || relation
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
  return edges.map(e => `→${escapeHtml(e.target)}(${getRelationLabel(e.relation)})`).join('<br>')
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
