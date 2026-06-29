<script setup lang="ts">
import { h, ref } from 'vue';
import { NButton, NDataTable, NEmpty, NInputNumber, NSpace, NStatistic, NTag, NUpload } from 'naive-ui';
import type { DataTableColumns, UploadCustomRequestOptions } from 'naive-ui';
import { fetchDetectFace } from '@/service/api';
import { $t } from '@/locales';

const maxFaceNum = ref(10);
const loading = ref(false);
const detected = ref(false);
const results = ref<Api.Face.FaceDetectItem[]>([]);

const columns: DataTableColumns<Api.Face.FaceDetectItem> = [
  { key: 'index', title: $t('common.index'), width: 64, align: 'center', render: (_, index) => index + 1 },
  {
    key: 'face_rect',
    title: $t('page.manage.face.faceRect'),
    minWidth: 200,
    render: row => row.face_rect.join(', ')
  },
  {
    key: 'face_probability',
    title: $t('page.manage.face.probability'),
    width: 140,
    align: 'center',
    render: row => h(NTag, { type: 'info' }, { default: () => row.face_probability.toFixed(3) })
  }
];

async function handleUpload({ file }: UploadCustomRequestOptions) {
  if (!file.file) return;
  loading.value = true;
  try {
    const { data, error } = await fetchDetectFace({ file: file.file, max_face_num: maxFaceNum.value });
    if (!error && data) {
      results.value = data.results;
      detected.value = true;
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
        <span class="text-14px">{{ $t('page.manage.face.maxFaceNum') }}</span>
        <NInputNumber v-model:value="maxFaceNum" :min="1" :max="100" style="width: 120px" />
        <NUpload :show-file-list="false" :custom-request="handleUpload" accept="image/*">
          <NButton type="primary" :loading="loading">{{ $t('page.manage.face.uploadImage') }}</NButton>
        </NUpload>
      </NSpace>
      <div class="mt-8px text-13px text-gray-500">{{ $t('page.manage.face.detectTip') }}</div>
    </NCard>

    <NCard :title="$t('page.manage.face.detectTitle')" :bordered="false" size="small" class="card-wrapper">
      <template v-if="detected" #header-extra>
        <NStatistic :label="$t('page.manage.face.faceCount')" :value="results.length" />
      </template>
      <NEmpty v-if="detected && !results.length" :description="$t('page.manage.face.noFace')" />
      <NDataTable
        v-else-if="results.length"
        :columns="columns"
        :data="results"
        size="small"
        :row-key="(row: Api.Face.FaceDetectItem) => `${row.face_rect[0]}-${row.face_rect[1]}`"
      />
      <NEmpty v-else />
    </NCard>
  </NSpace>
</template>
