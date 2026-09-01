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
    trendLabelKey: string,
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
        : `${trendPct > 0 ? '+' : ''}${trendPct}${trendUnit}${trendPct > 0 ? ' ↑' : trendPct < 0 ? ' ↓' : ''} ${$t(
            trendLabelKey as App.I18n.I18nKey
          )}`,
    trendUp: trendPct == null ? null : trendPct >= 0,
    gradientColor: `linear-gradient(to bottom right, ${start}, ${end})`,
    icon
  });

  return [
    build(
      'total',
      $t(`${prefix}.totalInteractions`),
      stats ? String(stats.total) : '-',
      stats?.total_delta_pct ?? null,
      '%',
      `${prefix}.vsLastSunday`,
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
      `${prefix}.vsYesterday`,
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
      `${prefix}.vsYesterday`,
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

    <NGrid cols="s:1 m:3 l:3" responsive="screen" :x-gap="12" :y-gap="12">
      <NGi v-for="item in cards" :key="item.key">
        <GradientBg :gradient-color="item.gradientColor" class="min-h-104px flex-1">
          <div class="flex items-center justify-between">
            <h3 class="text-15px font-normal">{{ item.title }}</h3>
            <SvgIcon :icon="item.icon" class="text-26px" />
          </div>
          <!-- 数字固定高度，loading 时用空白占位，避免刷新时高度抖动 -->
          <div class="h-36px flex items-center pt-4px">
            <span v-if="!loading" class="text-28px font-500">{{ item.value }}</span>
            <span v-else class="invisible text-28px font-500">&nbsp;</span>
          </div>
          <!-- 趋势行固定占位（无数据显示空白），保证三张卡片等高 -->
          <div class="h-18px pt-2px text-12px leading-18px opacity-90">
            <template v-if="!loading">{{ item.trend || ' ' }}</template>
          </div>
        </GradientBg>
      </NGi>
    </NGrid>
  </NCard>
</template>

<style scoped></style>
