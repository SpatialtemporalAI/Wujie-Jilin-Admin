<script setup lang="ts">
import { computed, watch } from 'vue';
import { useAppStore } from '@/store/modules/app';
import { useEcharts } from '@/hooks/common/echarts';
import { $t } from '@/locales';

defineOptions({
  name: 'VoiceConsultationTriggerPieChart'
});

interface Props {
  data: Api.VoiceConsultation.DistributionItem[];
}

const props = defineProps<Props>();

const appStore = useAppStore();

// 蓝/紫配色，对应参考图（唤醒词-蓝，人脸识别-紫）
const TRIGGER_ORDER: Api.VoiceConsultation.TriggerMethod[] = ['wake_word', 'face_recognition'];
const TRIGGER_COLORS: Record<string, string> = {
  wake_word: '#5da8ff',
  face_recognition: '#b37feb'
};

const chartData = computed(() => {
  const countMap = new Map(props.data.map(item => [item.type, item.count]));
  const known = TRIGGER_ORDER.map(type => ({
    type,
    label: $t(`page.manage.voiceConsultation.triggerMethod.${type}`),
    count: countMap.get(type) ?? 0
  }));
  const extras = props.data
    .filter(item => !TRIGGER_ORDER.includes(item.type as Api.VoiceConsultation.TriggerMethod))
    .map(item => ({ type: item.type, label: item.type, count: item.count }));
  return [...known, ...extras];
});

const { domRef, updateOptions } = useEcharts(() => ({
  tooltip: {
    trigger: 'item' as const
  },
  legend: {
    bottom: '1%',
    left: 'center',
    itemStyle: {
      borderWidth: 0
    }
  },
  series: [
    {
      name: $t('page.manage.voiceConsultation.triggerDistribution'),
      type: 'pie' as const,
      radius: ['45%', '75%'],
      avoidLabelOverlap: false,
      itemStyle: {
        borderRadius: 10,
        borderColor: '#fff',
        borderWidth: 1
      },
      label: {
        show: false,
        position: 'center' as const
      },
      emphasis: {
        label: {
          show: true,
          fontSize: '12'
        }
      },
      labelLine: {
        show: false
      },
      data: [] as { name: string; value: number; itemStyle: { color: string } }[]
    }
  ]
}));

watch(
  chartData,
  val => {
    updateOptions((opts, factory) => {
      const originOpts = factory();
      opts.series[0].name = originOpts.series[0].name;
      opts.series[0].data = val.map(item => ({
        name: item.label,
        value: item.count,
        itemStyle: { color: TRIGGER_COLORS[item.type] ?? '#8c8c8c' }
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
  <NCard :bordered="false" size="small" class="card-wrapper"
    :title="$t('page.manage.voiceConsultation.triggerDistribution')">
    <div ref="domRef" class="h-320px overflow-hidden"></div>
  </NCard>
</template>

<style scoped></style>
