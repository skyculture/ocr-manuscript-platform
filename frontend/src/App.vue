<template>
  <div class="app">
    <nav class="navbar">
      <div class="nav-brand">
        <span class="nav-title">笔迹解码</span>
      </div>
      <div class="nav-links">
        <router-link to="/" class="nav-link">卷首</router-link>
        <router-link to="/annotation" class="nav-link">标注</router-link>
        <router-link to="/training" class="nav-link">训练</router-link>
        <router-link to="/proofreading" class="nav-link">校对</router-link>
      </div>
    </nav>
    <main class="main-content">
      <router-view />
    </main>
    <footer class="footer">
      笔迹解码 &copy; 2026 · 古籍智能识别平台
    </footer>
  </div>
</template>

<script setup>
</script>
