<template>
  <div v-if="message" class="alert" :class="type">{{ message }}</div>
</template>

<script setup lang="ts">
defineProps<{
  message: string;
  type: "error" | "info" | "success";
}>();
</script>

<style scoped>
.alert {
  border-radius: 8px;
  padding: 10px 12px;
  margin: 10px 0;
  font-size: 14px;
}
.error {
  background: #ffe4e6;
  color: #9f1239;
}
.info {
  background: #e0f2fe;
  color: #075985;
}
.success {
  background: #dcfce7;
  color: #166534;
}
</style>

