<script setup lang="ts">
import { computed, h, ref, watch } from 'vue';
import { NButton, NDataTable, NEmpty, NInputNumber, NSelect, NSpace, NTag, NUpload } from 'naive-ui';
import type { DataTableColumns, SelectOption, UploadCustomRequestOptions } from 'naive-ui';
import { fetchSearchFace } from '@/service/api';
import { $t } from '@/locales';

const props = defineProps<{
  dbOptions: string[];
  dbName: string | null;
}>();

const localDb = ref<string | null>(props.dbName);
const limit = ref(3);
const loading = ref(false);
const searched = ref(false);
const results = ref<Api.Face.FaceSearchItem[]>([]);

watch(
  () => props.dbName,
  v => {
    if (v && !localDb.value) localDb.value = v;
  }
);

const dbSelectOptions = computed<SelectOption[]>(() => props.dbOptions.map(d => ({ label: d, value: d })));

const columns: DataTableColumns<Api.Face.FaceSearchItem> = [
  { key: 'index', title: $t('common.index'), width: 64, align: 'center', render: (_, index) => index + 1 },
  { key: 'entity_id', title: $t('page.manage.face.entityId'), minWidth: 160 },
  {
    key: 'confidence',
    title: $t('page.manage.face.confidence'),
    width: 140,
    align: 'center',
    render: row => h(NTag, { type: 'success' }, { default: () => row.confidence.toFixed(2) })
  }
];

async function handleUpload({ file }: UploadCustomRequestOptions) {
  if (!file.file) return;
  if (!localDb.value) {
    window.$message?.warning($t('page.manage.face.selectDbFirst'));
    return;
  }
  loading.value = true;
  try {
    const { data, error } = await fetchSearchFace({ db_name: localDb.value, file: file.file, limit: limit.value });
    if (!error && data) {
      results.value = data.results;
      searched.value = true;
    }
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <NSpace vertical :size="16">
    <NCard :bordered="false" size="small" class="card-wrapper">
      <NSpace align="center" :wrap="true" :size="12">
        <span class="text-14px">{{ $t('page.manage.face.selectDb') }}</span>
        <NSelect
          v-model:value="localDb"
          :options="dbSelectOptions"
          :placeholder="$t('page.manage.face.selectDb')"
          style="width: 240px"
        />
        <span class="text-14px">{{ $t('page.manage.face.limit') }}</span>
        <NInputNumber v-model:value="limit" :min="1" :max="10" style="width: 120px" />
        <NUpload :show-file-list="false" :custom-request="handleUpload" accept="image/*">
          <NButton type="primary" :loading="loading">{{ $t('page.manage.face.uploadImage') }}</NButton>
        </NUpload>
      </NSpace>
      <div class="mt-8px text-13px text-gray-500">{{ $t('page.manage.face.searchTip') }}</div>
    </NCard>

    <NCard :title="$t('page.manage.face.searchTitle')" :bordered="false" size="small" class="card-wrapper">
      <NEmpty v-if="searched && !results.length" :description="$t('page.manage.face.noMatch')" />
      <NDataTable
        v-else-if="results.length"
        :columns="columns"
        :data="results"
        size="small"
        :row-key="(r: Api.Face.FaceSearchItem) => r.entity_id"
      />
      <NEmpty v-else />
    </NCard>
  </NSpace>
</template>
