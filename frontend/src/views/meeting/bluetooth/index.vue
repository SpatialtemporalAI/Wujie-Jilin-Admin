<script setup lang="ts">
defineOptions({
  name: 'MeetingBluetooth'
});
</script>

<template>
  <div class="min-h-500px flex-col-stretch gap-16px overflow-hidden lt-sm:overflow-auto">
    <NCard :bordered="false" size="small" class="card-wrapper sm:flex-1-hidden">
      <NEmpty class="h-full" description="蓝牙设备连接功能正在开发中，敬请期待">
        <template #icon>
          <SvgIcon icon="mdi:bluetooth" class="text-56px text-primary" />
        </template>
      </NEmpty>
    </NCard>
  </div>
</template>

<style scoped></style>
