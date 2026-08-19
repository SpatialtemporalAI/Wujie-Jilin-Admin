<script setup lang="ts">
import { computed } from 'vue';
import { createReusableTemplate } from '@vueuse/core';
import { useThemeStore } from '@/store/modules/theme';
import { $t } from '@/locales';

defineOptions({
  name: 'VoiceConsultationStatCards' });

interface Props {
  stats: Api.VoiceConsultation.Stats | null;
  loading?: boolean;
}

const props = defineProps<Props>();

const themeStore = useThemeStore();

interface CardItem {
  key: string;
  title: string;
  value: string;
  trend: string | null;
  trendUp: boolean | null;
  gradientColor: string;
  icon: string;
}

function formatDuration(seconds: number | null): string {
  if (seconds == null) return '-';
  if (seconds < 60) return `${Math.round(seconds)} 秒`;
  const minutes = Math.floor(seconds / 60);
  const rest = Math.round(seconds % 60);
  return rest > 0 ? `${minutes} 分 ${rest} 秒` : `${minutes} 分`;
}

const cards = computed<CardItem[]>(() => {
  const stats = props.stats;
  const prefix = 'page.manage.voiceConsultation';
  const build = (
    key: string,
    title: string,
    value: string,
    trendPct: number | null,
    trendUnit: string,
    start: string,
    end: string,
    icon: string
  ): CardItem => ({
    key,
    title,
    value,
    trend:
      trendPct == null
        ? null
        : `${trendPct > 0 ? '+' : ''}${trendPct}${trendUnit}${trendPct > 0 ? ' ↑' : trendPct < 0 ? ' ↓' : ''} ${$t(`${prefix}.vsLastWeek`)}`,
    trendUp: trendPct == null ? null : trendPct >= 0,
    gradientColor: `linear-gradient(to bottom right, ${start}, ${end})`,
    icon
  });

  return [
    build(
      'total',
      $t(`${prefix}.totalInteractions`),
      stats ? String(stats.total) : '-',
      null,
      '',
      '#56cdf3',
      '#719de3',
      'ant-design:message-outlined'
    ),
    build(
      'today',
      $t(`${prefix}.todayInteractions`),
      stats ? String(stats.today_count) : '-',
      stats?.today_delta_pct ?? null,
      '%',
      '#36cfc9',
      '#1a9e8f',
      'ant-design:rise-outlined'
    ),
    build(
      'avgDuration',
      $t(`${prefix}.avgDuration`),
      formatDuration(stats?.avg_duration ?? null),
      stats?.avg_duration_delta_pct ?? null,
      '%',
      '#865ec0',
      '#5144b4',
      'ant-design:clock-circle-outlined'
    )
  ];
});

interface GradientBgProps {
  gradientColor: string;
}

const [DefineGradientBg, GradientBg] = createReusableTemplate<GradientBgProps>();
</script>

<template>
  <NCard :bordered="false" size="small" class="card-wrapper">
    <DefineGradientBg v-slot="{ $slots, gradientColor }">
      <div
        class="px-16px pb-8px pt-12px text-white"
        :style="{ backgroundImage: gradientColor, borderRadius: themeStore.themeRadius + 'px' }"
      >
        <component :is="$slots.default" />
      </div>
    </DefineGradientBg>

    <NGrid cols="s:1 m:2 l:3" responsive="screen" :x-gap="12" :y-gap="12">
      <NGi v-for="item in cards" :key="item.key">
        <GradientBg :gradient-color="item.gradientColor" class="flex-1">
          <div class="flex items-center justify-between">
            <h3 class="text-15px font-normal">{{ item.title }}</h3>
            <SvgIcon :icon="item.icon" class="text-26px" />
          </div>
          <NSpin v-if="loading" size="small" class="pt-8px">
            <div class="h-32px"></div>
          </NSpin>
          <template v-else>
            <div class="pt-4px text-28px font-500">{{ item.value }}</div>
            <div v-if="item.trend" class="pt-2px text-12px opacity-90">{{ item.trend }}</div>
          </template>
        </GradientBg>
      </NGi>
    </NGrid>
  </NCard>
</template>

<style scoped></style>
