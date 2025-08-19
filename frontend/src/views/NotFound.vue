<template>
  <div class="not-found-container">
    <div class="content">
      <h1>{{ $t('notFound.title') }}</h1>
      <h2>{{ $t('notFound.subtitle') }}</h2>
      <p>{{ $t('notFound.description') }}</p>
      <el-button type="primary" @click="$router.push('/')">{{ $t('notFound.backToHome') }}</el-button>
    </div>
  </div>
</template>

<style scoped>
.not-found-container {
  height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background-color: var(--bg-color);
}

.content {
  text-align: center;
}

h1 {
  font-size: 120px;
  margin: 0;
  color: #409EFF;
}

h2 {
  font-size: 30px;
  margin: 20px 0;
  color: var(--text-color);
}

p {
  font-size: 16px;
  color: var(--text-secondary);
  margin-bottom: 30px;
}
</style>