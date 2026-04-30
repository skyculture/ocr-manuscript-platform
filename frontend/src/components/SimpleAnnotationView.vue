<template>
  <div class="detail-panels-vertical">
    <div class="detail-panel">
      <div class="panel-header">原始图片</div>
      <div class="image-viewer">
        <img v-if="item.image_url" :src="item.image_url" :alt="item.name">
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
import { computed } from 'vue'

const props = defineProps({
  item: Object
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
