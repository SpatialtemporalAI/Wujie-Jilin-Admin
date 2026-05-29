<script setup lang="ts">
import UploadDemo from './modules/upload-demo.vue';
</script>

<template>
  <NSpace vertical :size="16">
    <NCard :bordered="false" :title="$t('page.demo.upload.singleUpload')" class="card-wrapper">
      <UploadDemo :multiple="false" />
    </NCard>

    <NCard :bordered="false" :title="$t('page.demo.upload.multiUpload')" class="card-wrapper">
      <UploadDemo :multiple="true" />
    </NCard>
  </NSpace>
</template>

<style scoped></style>
