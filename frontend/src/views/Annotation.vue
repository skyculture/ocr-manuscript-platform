<template>
  <div class="page-container">
    <div class="page-header">
      <h1 class="page-title">🏷️ 数据标注展示</h1>
      <p class="page-subtitle">查看原始手稿图片及对应的图结构JSON标注文件</p>
    </div>
    <div class="toolbar">
      <div class="toolbar-left">
        <button class="btn btn-primary" @click="loadData">🔄 刷新数据</button>
        <span class="data-count">共 {{ items.length }} 条数据</span>
      </div>
      <div class="toolbar-right">
        <button class="btn btn-secondary" @click="showImageUpload = !showImageUpload">📤 上传图片</button>
        <button class="btn btn-secondary" @click="showJsonUpload = !showJsonUpload">📄 上传JSON</button>
      </div>
    </div>

    <div class="upload-panel" v-if="showImageUpload">
      <h3>上传原始图片</h3>
      <form @submit.prevent="uploadImage">
        <input type="file" name="image" accept="image/*" required ref="imageInput">
        <button type="submit" class="btn btn-primary">上传</button>
      </form>
    </div>

    <div class="upload-panel" v-if="showJsonUpload">
      <h3>上传标注JSON文件</h3>
      <form @submit.prevent="uploadJson">
        <input type="file" name="json_file" accept=".json" required ref="jsonInput">
        <p class="upload-hint">JSON文件名需与对应图片文件名一致（如图片为 sample.png，JSON为 sample.json）</p>
        <button type="submit" class="btn btn-primary">上传</button>
      </form>
    </div>

    <div v-if="items.length === 0" class="empty-state">
      <div class="empty-icon">📭</div>
      <p>暂无数据，请上传图片和标注文件</p>
    </div>

    <div class="split-view" v-else>
      <div class="split-list">
        <div class="split-list-header">文件列表</div>
        <div class="split-list-body">
          <div v-for="(item, idx) in items" :key="item.name"
               class="annotation-list-item"
               :class="{ selected: idx === selectedIndex }"
               @click="selectedIndex = idx">
            <div class="list-item-info">
              <div class="list-item-name">{{ item.name }}</div>
              <span v-if="item.has_json" class="status-badge status-done">已标注</span>
              <span v-else class="status-badge status-pending">未标注</span>
            </div>
          </div>
        </div>
      </div>
      <div class="split-detail-wide">
        <template v-if="selectedItem">
          <template v-if="selectedItem.has_json && isGraphFormat(selectedItem.json_data)">
            <GraphAnnotationView :item="selectedItem" :data="selectedItem.json_data" />
          </template>
          <template v-else>
            <SimpleAnnotationView :item="selectedItem" />
          </template>
        </template>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { annotationApi } from '../api'
import GraphAnnotationView from '../components/GraphAnnotationView.vue'
import SimpleAnnotationView from '../components/SimpleAnnotationView.vue'

const items = ref([])
const selectedIndex = ref(0)
const showImageUpload = ref(false)
const showJsonUpload = ref(false)
const imageInput = ref(null)
const jsonInput = ref(null)

const selectedItem = computed(() => items.value[selectedIndex.value] || null)

function isGraphFormat(data) {
  return Array.isArray(data) && data.length > 0 && data[0].node_id !== undefined
}

async function loadData() {
  try {
    const resp = await annotationApi.list()
    items.value = resp.data
  } catch (e) {
    console.error('加载数据失败:', e)
  }
}

async function uploadImage() {
  const form = imageInput.value.closest('form')
  const formData = new FormData(form)
  try {
    const resp = await annotationApi.uploadImage(formData)
    if (resp.data.success) {
      alert('图片上传成功！')
      showImageUpload.value = false
      loadData()
    } else {
      alert('上传失败：' + (resp.data.error || '未知错误'))
    }
  } catch (err) {
    alert('上传出错：' + err.message)
  }
}

async function uploadJson() {
  const form = jsonInput.value.closest('form')
  const formData = new FormData(form)
  try {
    const resp = await annotationApi.uploadJson(formData)
    if (resp.data.success) {
      alert('JSON上传成功！')
      showJsonUpload.value = false
      loadData()
    } else {
      alert('上传失败：' + (resp.data.error || '未知错误'))
    }
  } catch (err) {
    alert('上传出错：' + err.message)
  }
}

onMounted(loadData)
</script>
