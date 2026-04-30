<template>
  <div class="home-container">
    <div class="hero-section">
      <h1 class="hero-title">笔迹解码</h1>
      <p class="hero-subtitle">展示OCR手稿识别项目全流程：数据标注 → 模型训练 → 人工校对</p>
    </div>

    <div class="network-info-panel" v-if="networkInfo">
      <div class="network-info-header">
        <span>🌐 网络访问信息</span>
      </div>
      <div class="network-info-body">
        <div class="public-url-box" v-if="networkInfo.public_url">
          <div class="public-url-label">公网访问地址</div>
          <div class="public-url-main">
            <a :href="networkInfo.public_url" target="_blank">{{ networkInfo.public_url }}</a>
          </div>
          <button class="btn-copy" @click="copyUrl(networkInfo.public_url)">📋 复制链接</button>
          <div class="public-url-hint">任何设备均可通过此地址访问</div>
        </div>
        <div class="access-addresses" v-if="networkInfo.local_ip">
          <div class="access-title">局域网访问</div>
          <div class="access-list">
            <div class="access-item">
              <span class="access-label">本机：</span>
              <a class="access-link" href="http://localhost:5000">http://localhost:5000</a>
            </div>
            <div class="access-item">
              <span class="access-label">局域网：</span>
              <a class="access-link" :href="'http://' + networkInfo.local_ip + ':5000'">
                http://{{ networkInfo.local_ip }}:5000
              </a>
              <span class="campus-tag" v-if="networkInfo.is_campus">校园网</span>
            </div>
          </div>
          <div class="campus-note" v-if="networkInfo.is_campus">
            ⚠️ 检测到校园网环境，WiFi设备间可能无法互通，建议使用公网地址或手机热点
          </div>
        </div>
      </div>
    </div>

    <div class="cards-grid">
      <router-link to="/annotation" class="card card-annotation">
        <div class="card-icon">🏷️</div>
        <div class="card-title">数据标注</div>
        <div class="card-desc">展示原始手稿图片及对应的图结构JSON标注文件，支持节点、边关系的可视化展示</div>
        <div class="card-features">
          <span class="feature-tag">图片展示</span>
          <span class="feature-tag">JSON标注</span>
          <span class="feature-tag">图结构</span>
        </div>
      </router-link>

      <router-link to="/training" class="card card-training">
        <div class="card-icon">🤖</div>
        <div class="card-title">模型训练</div>
        <div class="card-desc">展示大模型训练的配置参数、训练指标、损失曲线和识别效果样例</div>
        <div class="card-features">
          <span class="feature-tag">训练配置</span>
          <span class="feature-tag">性能指标</span>
          <span class="feature-tag">效果对比</span>
        </div>
      </router-link>

      <router-link to="/proofreading" class="card card-proofreading">
        <div class="card-icon">✅</div>
        <div class="card-title">人工校对</div>
        <div class="card-desc">展示专业人员校对后的结果，对比原始识别与校对差异，统计错误类型分布</div>
        <div class="card-features">
          <span class="feature-tag">文本对比</span>
          <span class="feature-tag">错误标注</span>
          <span class="feature-tag">统计分析</span>
        </div>
      </router-link>
    </div>

    <div class="workflow-section">
      <h2 class="section-title">项目工作流程</h2>
      <div class="workflow-steps">
        <div class="workflow-step">
          <div class="step-number">1</div>
          <div class="step-content">
            <h3>数据标注</h3>
            <p>对手稿图片进行图结构标注，标注文本、印章、签名等节点及关系</p>
          </div>
        </div>
        <div class="step-arrow">→</div>
        <div class="workflow-step">
          <div class="step-number">2</div>
          <div class="step-content">
            <h3>模型训练</h3>
            <p>使用标注数据微调大模型，评估识别效果和性能指标</p>
          </div>
        </div>
        <div class="step-arrow">→</div>
        <div class="workflow-step">
          <div class="step-number">3</div>
          <div class="step-content">
            <h3>人工校对</h3>
            <p>专业人员校对模型输出，修正错误并统计质量指标</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { networkApi } from '../api'

const networkInfo = ref(null)

onMounted(async () => {
  try {
    const resp = await networkApi.info()
    networkInfo.value = resp.data
  } catch (e) {
    console.error('获取网络信息失败:', e)
  }
})

function copyUrl(url) {
  navigator.clipboard.writeText(url).then(() => {
    alert('链接已复制到剪贴板！')
  })
}
</script>
