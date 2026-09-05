<template>
  <div class="resume-page">
    <div class="resume-greeting-wrap">
      <PageGreeting tip="快来优化你的简历，让机会主动找上你吧！" />
    </div>
    <Resume />
  </div>
</template>

<script setup lang="ts">
import Resume from '@/components/resume.vue'
import PageGreeting from '@/components/PageGreeting.vue'
</script>

<style scoped>
.resume-page {
  display: flex;
  flex-direction: column;
}

.resume-greeting-wrap {
  padding: 16px 24px 0;
}
</style>
