<template>
  <div class="app">
    <nav class="navbar">
      <div class="nav-brand">
        <span class="nav-icon">📜</span>
        <span class="nav-title">笔迹解码</span>
      </div>
      <div class="nav-links">
        <router-link to="/" class="nav-link">🏠 首页</router-link>
        <router-link to="/annotation" class="nav-link">🏷️ 数据标注</router-link>
        <router-link to="/training" class="nav-link">🤖 模型训练</router-link>
        <router-link to="/proofreading" class="nav-link">✅ 人工校对</router-link>
      </div>
    </nav>
    <main class="main-content">
      <router-view />
    </main>
    <footer class="footer">
      笔迹解码 &copy; 2026
    </footer>
  </div>
</template>

<script setup>
</script>
