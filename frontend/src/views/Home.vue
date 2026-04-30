<template>
  <div class="home-container">
    <div class="hero-section">
      <div class="hero-deco-top"></div>
      <h1 class="hero-title">笔迹解码</h1>
      <p class="hero-subtitle">古籍手稿智能识别全流程展示</p>
      <div class="hero-seal">
        <span>智</span>
      </div>
      <div class="hero-deco-bottom"></div>
    </div>

    <div class="scroll-section">
      <div class="scroll-rod top-rod"></div>
      <div class="scroll-body">
        <div class="scroll-content">
          <router-link to="/annotation" class="scroll-card scroll-card-annotation">
            <div class="scroll-card-number">壹</div>
            <div class="scroll-card-main">
              <div class="scroll-card-icon">🏷️</div>
              <div class="scroll-card-text">
                <h3>数据标注</h3>
                <p>展示原始手稿图片及对应的图结构JSON标注文件，支持节点、边关系的可视化展示</p>
              </div>
              <div class="scroll-card-tags">
                <span>图片展示</span>
                <span>JSON标注</span>
                <span>图结构</span>
              </div>
            </div>
            <div class="scroll-card-arrow">›</div>
          </router-link>

          <div class="scroll-connector">
            <div class="connector-line"></div>
            <div class="connector-dot"></div>
            <div class="connector-line"></div>
          </div>

          <router-link to="/training" class="scroll-card scroll-card-training">
            <div class="scroll-card-number">贰</div>
            <div class="scroll-card-main">
              <div class="scroll-card-icon">🤖</div>
              <div class="scroll-card-text">
                <h3>模型训练</h3>
                <p>展示大模型训练的配置参数、训练指标、损失曲线和识别效果样例</p>
              </div>
              <div class="scroll-card-tags">
                <span>训练配置</span>
                <span>性能指标</span>
                <span>效果对比</span>
              </div>
            </div>
            <div class="scroll-card-arrow">›</div>
          </router-link>

          <div class="scroll-connector">
            <div class="connector-line"></div>
            <div class="connector-dot"></div>
            <div class="connector-line"></div>
          </div>

          <router-link to="/proofreading" class="scroll-card scroll-card-proofreading">
            <div class="scroll-card-number">叁</div>
            <div class="scroll-card-main">
              <div class="scroll-card-icon">✅</div>
              <div class="scroll-card-text">
                <h3>人工校对</h3>
                <p>展示专业人员校对后的结果，对比原始识别与校对差异，统计错误类型分布</p>
              </div>
              <div class="scroll-card-tags">
                <span>文本对比</span>
                <span>错误标注</span>
                <span>统计分析</span>
              </div>
            </div>
            <div class="scroll-card-arrow">›</div>
          </router-link>
        </div>

        <div class="scroll-footer" v-if="networkInfo">
          <details class="network-details">
            <summary class="network-summary">🌐 访问地址</summary>
            <div class="network-detail-body">
              <div class="network-url-row" v-if="networkInfo.public_url">
                <span class="network-label">公网</span>
                <a class="network-link" :href="networkInfo.public_url" target="_blank">{{ networkInfo.public_url }}</a>
                <button class="network-copy-btn" @click.prevent="copyUrl(networkInfo.public_url)">复制</button>
              </div>
              <div class="network-url-row" v-if="networkInfo.local_ip">
                <span class="network-label">本机</span>
                <a class="network-link" href="http://localhost:5000">localhost:5000</a>
              </div>
              <div class="network-url-row" v-if="networkInfo.local_ip">
                <span class="network-label">局域网</span>
                <a class="network-link" :href="'http://' + networkInfo.local_ip + ':5000'">{{ networkInfo.local_ip }}:5000</a>
                <span class="campus-tag" v-if="networkInfo.is_campus">校园网</span>
              </div>
              <div class="campus-note" v-if="networkInfo.is_campus">
                ⚠️ 校园网WiFi设备间可能无法互通，建议使用公网地址
              </div>
            </div>
          </details>
        </div>
      </div>
      <div class="scroll-rod bottom-rod"></div>
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
