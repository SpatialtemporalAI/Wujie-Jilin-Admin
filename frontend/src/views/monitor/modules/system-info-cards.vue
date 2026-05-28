<script setup lang="ts">
import { computed } from 'vue';
import { $t } from '@/locales';

interface Props {
  bootTime?: string;
  processCount?: number;
  pythonVersion?: string;
}

const props = withDefaults(defineProps<Props>(), {
  bootTime: '',
  processCount: 0,
  pythonVersion: ''
});

const uptime = computed(() => {
  if (!props.bootTime) return '-';
  const boot = new Date(props.bootTime);
  const now = new Date();
  const diff = Math.floor((now.getTime() - boot.getTime()) / 1000);
  const days = Math.floor(diff / 86400);
  const hours = Math.floor((diff % 86400) / 3600);
  const minutes = Math.floor((diff % 3600) / 60);
  return `${days}${$t('page.monitor.day')} ${hours}${$t('page.monitor.hour')} ${minutes}${$t('page.monitor.minute')}`;
});

const cards = computed(() => [
  {
    key: 'uptime',
    title: $t('page.monitor.uptime'),
    value: uptime.value,
    icon: 'mdi:clock-outline'
  },
  {
    key: 'processCount',
    title: $t('page.monitor.processCount'),
    value: String(props.processCount),
    icon: 'mdi:application-cog-outline'
  },
  {
    key: 'pythonVersion',
    title: $t('page.monitor.pythonVersion'),
    value: props.pythonVersion || '-',
    icon: 'mdi:language-python'
  }
]);
</script>

<template>
  <NGrid cols="s:1 m:3" responsive="screen" :x-gap="16" :y-gap="16">
    <NGi v-for="item in cards" :key="item.key">
      <NCard size="small">
        <div class="flex items-center gap-12px">
          <div class="h-48px w-48px flex items-center justify-center rounded-full bg-primary bg-opacity-10">
            <SvgIcon :icon="item.icon" class="text-24px text-primary" />
          </div>
          <div>
            <div class="text-14px text-gray">{{ item.title }}</div>
            <div class="text-18px font-bold">{{ item.value }}</div>
          </div>
        </div>
      </NCard>
    </NGi>
  </NGrid>
</template>

<style scoped></style>
