<template>
  <section class="panel">
    <h3>{{ title }}</h3>
    <slot />
  </section>
</template>

<script setup lang="ts">
defineProps<{ title: string }>();
</script>

<style scoped>
.panel {
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 14px;
  background: #fff;
  margin-bottom: 12px;
}
h3 {
  margin: 0 0 10px;
  font-size: 16px;
}
</style>

