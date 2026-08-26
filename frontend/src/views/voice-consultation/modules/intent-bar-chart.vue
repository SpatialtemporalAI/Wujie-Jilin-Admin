<script setup lang="ts">
import { computed, watch } from 'vue';
import { useAppStore } from '@/store/modules/app';
import { useEcharts } from '@/hooks/common/echarts';
import { $t } from '@/locales';

defineOptions({
  name: 'VoiceConsultationIntentBarChart'
});

interface Props {
  data: Api.VoiceConsultation.DistributionItem[];
}

const props = defineProps<Props>();

const appStore = useAppStore();

// 意图展示顺序与配色（绿/橙/蓝/粉/青/紫，对应参考图）
const INTENT_ORDER: Api.VoiceConsultation.IntentType[] = [
  'indoor_navigation',
  'triage_qa',
  'medical_guide',
  'health_check_notice',
  'insurance_guide',
  'admission_notice'
];

const INTENT_COLORS: Record<string, string> = {
  indoor_navigation: '#36cfc9',
  triage_qa: '#ffa940',
  medical_guide: '#5da8ff',
  health_check_notice: '#ff85c0',
  insurance_guide: '#5cdbd3',
  admission_notice: '#b37feb'
};

const chartData = computed(() => {
  const countMap = new Map(props.data.map(item => [item.type, item.count]));
  const known = INTENT_ORDER.map(type => ({
    type,
    label: $t(`page.manage.voiceConsultation.intentType.${type}`),
    count: countMap.get(type) ?? 0
  }));
  // 未知意图 code 兜底追加
  const extras = props.data
    .filter(item => !INTENT_ORDER.includes(item.type as Api.VoiceConsultation.IntentType))
    .map(item => ({ type: item.type, label: item.type, count: item.count }));
  return [...known, ...extras];
});

const { domRef, updateOptions } = useEcharts(() => ({
  tooltip: {
    trigger: 'axis' as const,
    axisPointer: {
      type: 'shadow' as const
    }
  },
  grid: {
    left: '2%',
    right: '6%',
    bottom: '3%',
    top: '5%',
    containLabel: true
  },
  xAxis: {
    type: 'value' as const,
    minInterval: 1
  },
  yAxis: {
    type: 'category' as const,
    inverse: true,
    data: [] as string[]
  },
  series: [
    {
      name: $t('page.manage.voiceConsultation.intentDistribution'),
      type: 'bar' as const,
      barWidth: '55%',
      label: {
        show: true,
        position: 'right' as const
      },
      itemStyle: {
        borderRadius: [0, 4, 4, 0]
      },
      data: [] as { value: number; itemStyle: { color: string } }[]
    }
  ]
}));

watch(
  chartData,
  val => {
    updateOptions((opts, factory) => {
      const originOpts = factory();
      opts.series[0].name = originOpts.series[0].name;
      opts.yAxis.data = val.map(item => item.label);
      opts.series[0].data = val.map(item => ({
        value: item.count,
        itemStyle: { color: INTENT_COLORS[item.type] ?? '#8c8c8c' }
      }));
      return opts;
    });
  },
  { immediate: true, deep: true }
);

watch(
  () => appStore.locale,
  () => {
    updateOptions((opts, factory) => {
      const originOpts = factory();
      opts.series[0].name = originOpts.series[0].name;
      return opts;
    });
  }
);
</script>

<template>
  <NCard :bordered="false" size="small" class="card-wrapper" :title="$t('page.manage.voiceConsultation.intentDistribution')">
    <div ref="domRef" class="h-320px overflow-hidden"></div>
  </NCard>
</template>

<style scoped></style>
