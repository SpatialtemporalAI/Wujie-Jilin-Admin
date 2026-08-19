<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { useDebounceFn } from '@vueuse/core';
import { NDatePicker, NInput, NSelect } from 'naive-ui';
import dayjs from 'dayjs';
import { fetchGetAllRobots } from '@/service/api/robot';
import { $t } from '@/locales';

defineOptions({
  name: 'VoiceConsultationSessionSearch'
});

interface Emits {
  (e: 'search'): void;
}

const model = defineModel<Api.VoiceConsultation.SessionSearchParams>('model', { required: true });

const emit = defineEmits<Emits>();

const robotOptions = ref<{ label: string; value: number }[]>([]);

const statusOptions = (['in_progress', 'completed', 'interrupted'] as const).map(value => ({
  label: $t(`page.manage.voiceConsultation.statusLabel.${value}`),
  value
}));

const timeRange = computed<[number, number] | null>({
  get() {
    const start = model.value.start_time ? dayjs(model.value.start_time).valueOf() : null;
    const end = model.value.end_time ? dayjs(model.value.end_time).valueOf() : null;
    return start && end ? [start, end] : null;
  },
  set(val: [number, number] | null) {
    if (val) {
      model.value.start_time = dayjs(val[0]).format();
      model.value.end_time = dayjs(val[1]).format();
    } else {
      model.value.start_time = undefined;
      model.value.end_time = undefined;
    }
  }
});

async function loadRobotOptions() {
  try {
    const { data } = await fetchGetAllRobots();
    if (data) {
      robotOptions.value = data.map(r => ({ label: r.name, value: r.id }));
    }
  } catch {
    robotOptions.value = [];
  }
}

function handleSearch() {
  model.value.page = 1;
  emit('search');
}

const debouncedSearch = useDebounceFn(() => {
  handleSearch();
}, 500);

onMounted(() => {
  loadRobotOptions();
});
</script>

<template>
  <div class="flex-y-center flex-wrap gap-12px">
    <NDatePicker
      v-model:value="timeRange"
      type="daterange"
      :start-placeholder="$t('page.manage.voiceConsultation.form.startTime')"
      :end-placeholder="$t('page.manage.voiceConsultation.form.endTime')"
      clearable
      :style="{ width: '260px' }"
      @update:value="handleSearch"
    />
    <NSelect
      v-model:value="model.robot_id"
      :options="robotOptions"
      :placeholder="$t('page.manage.voiceConsultation.allRobots')"
      clearable
      filterable
      :style="{ width: '150px' }"
      @update:value="handleSearch"
    />
    <NSelect
      v-model:value="model.status"
      :options="statusOptions"
      :placeholder="$t('page.manage.voiceConsultation.allStatuses')"
      clearable
      :style="{ width: '130px' }"
      @update:value="handleSearch"
    />
    <NInput
      v-model:value="model.keyword"
      :placeholder="$t('page.manage.voiceConsultation.keywordPlaceholder')"
      clearable
      :style="{ width: '220px' }"
      @update:value="debouncedSearch"
    />
  </div>
</template>
