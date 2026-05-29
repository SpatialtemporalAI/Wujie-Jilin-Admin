<script setup lang="ts">
import { ref } from 'vue';
import type { UploadFileInfo } from 'naive-ui';
import { fetchUploadFile, fetchUploadFiles } from '@/service/api/file';

interface Props {
  multiple?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  multiple: false
});

interface UploadResult {
  name: string;
  size: number;
  status: 'success' | 'error';
  message?: string;
}

const results = ref<UploadResult[]>([]);
const uploading = ref(false);

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

async function handleUpload({ file, onFinish, onError }: { file: UploadFileInfo; onFinish: () => void; onError: () => void }) {
  if (!file.file) {
    onError();
    return;
  }

  try {
    const { data, error } = await fetchUploadFile(file.file);
    if (!error && data) {
      results.value.unshift({
        name: data.original_name,
        size: data.file_size,
        status: 'success'
      });
      onFinish();
    } else {
      results.value.unshift({
        name: file.name,
        size: file.file?.size ?? 0,
        status: 'error',
        message: error?.msg || 'Upload failed'
      });
      onError();
    }
  } catch {
    results.value.unshift({
      name: file.name,
      size: file.file?.size ?? 0,
      status: 'error',
      message: 'Network error'
    });
    onError();
  }
}

async function handleBatchUpload({ fileList, onFinish, onError }: { fileList: UploadFileInfo[]; onFinish: () => void; onError: () => void }) {
  const files = fileList.map(f => f.file).filter((f): f is File => f !== null);
  if (files.length === 0) {
    onError();
    return;
  }

  uploading.value = true;
  try {
    const { data, error } = await fetchUploadFiles(files);
    if (!error && data) {
      data.forEach(f => {
        results.value.unshift({
          name: f.original_name,
          size: f.file_size,
          status: 'success'
        });
      });
      onFinish();
    } else {
      onError();
    }
  } catch {
    onError();
  } finally {
    uploading.value = false;
  }
}
</script>

<template>
  <NSpace vertical :size="12">
    <NUpload
      :multiple="props.multiple"
      :custom-request="props.multiple ? undefined : handleUpload"
      @change="props.multiple ? undefined : undefined"
      :directory-dnd="true"
    >
      <NUploadDragger>
        <div style="padding: 20px 0">
          <NIcon size="48" :depth="3" style="margin-bottom: 8px">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
              <path d="M11 20H6.5a3.5 3.5 0 0 1 0-7h.05A5 5 0 0 1 16 8.05A4.5 4.5 0 0 1 20 12.5a4.5 4.5 0 0 1-4.5 4.5H13v3a1 1 0 0 1-2 0v-3zm1-8a1 1 0 0 1 1 1v3h2.5a2.5 2.5 0 0 0 0-5h-.5l-.05-.5a3 3 0 0 0-5.67-1.21l-.21.71H7.5a1.5 1.5 0 0 0 0 3H11v-1a1 1 0 0 1 1-1z"/>
            </svg>
          </NIcon>
          <NText style="font-size: 16px">{{ $t('page.demo.upload.dragOrClick') }}</NText>
        </div>
      </NUploadDragger>
    </NUpload>

    <NButton
      v-if="props.multiple"
      type="primary"
      :loading="uploading"
      @click="() => {
        const input = document.createElement('input');
        input.type = 'file';
        input.multiple = true;
        input.onchange = async (e) => {
          const files = Array.from((e.target as HTMLInputElement).files || []);
          if (files.length === 0) return;
          uploading.value = true;
          try {
            const { data, error } = await fetchUploadFiles(files);
            if (!error && data) {
              data.forEach(f => {
                results.value.unshift({ name: f.original_name, size: f.file_size, status: 'success' });
              });
              window.$message?.success($t('page.demo.upload.uploadSuccess'));
            }
          } finally {
            uploading.value = false;
          }
        };
        input.click();
      }"
    >
      {{ $t('page.demo.upload.selectFiles') }}
    </NButton>

    <NDataTable
      v-if="results.length > 0"
      :columns="[
        { title: $t('page.demo.upload.fileName'), key: 'name' },
        { title: $t('page.demo.upload.fileSize'), key: 'size', render: (row: UploadResult) => formatFileSize(row.size) },
        { title: $t('page.demo.upload.status'), key: 'status', render: (row: UploadResult) => h(NTag, { type: row.status === 'success' ? 'success' : 'error', size: 'small' }, { default: () => row.status === 'success' ? $t('page.demo.upload.uploadSuccess') : $t('page.demo.upload.uploadFailed') }) },
        { title: 'Message', key: 'message', render: (row: UploadResult) => row.message || '-' }
      ]"
      :data="results"
      :bordered="false"
      size="small"
    />
  </NSpace>
</template>

<script lang="ts">
import { h } from 'vue';
</script>
