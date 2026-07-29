<script setup lang="ts">
import { h, ref, watch } from 'vue';
import { NButton, NDataTable, NEmpty, NPopconfirm, NSpace, NSpin, NUpload } from 'naive-ui';
import type { DataTableColumns, UploadCustomRequestOptions } from 'naive-ui';
import { fetchAddFaceImage, fetchDeleteFaceImage, fetchGetFaceEntityDetail } from '@/service/api';
import { useAuth } from '@/hooks/business/auth';
import { $t } from '@/locales';

const props = defineProps<{
  dbName: string;
  entityId: string;
}>();

const visible = defineModel<boolean>({ required: true });

const { hasAuth } = useAuth();

const loading = ref(false);
const uploading = ref(false);
const faces = ref<Api.Face.FaceEntityFace[]>([]);

const columns: DataTableColumns<Api.Face.FaceEntityFace> = [
  { key: 'index', title: $t('common.index'), width: 64, align: 'center', render: (_, index) => index + 1 },
  { key: 'face_id', title: $t('page.manage.face.faceId'), minWidth: 200, ellipsis: { tooltip: true } },
  {
    key: 'operate',
    title: $t('common.operate'),
    width: 100,
    align: 'center',
    render: row => {
      if (!hasAuth('face:image:delete')) return null;
      return h(
        NPopconfirm,
        { onPositiveClick: () => handleDelete(row.face_id) },
        {
          default: () => $t('common.confirmDelete'),
          trigger: () =>
            h(NButton, { type: 'error', text: true, size: 'small' }, { default: () => $t('common.delete') })
        }
      );
    }
  }
];

async function loadDetail() {
  if (!props.entityId) return;
  loading.value = true;
  const { data, error } = await fetchGetFaceEntityDetail(props.dbName, props.entityId);
  if (!error && data) {
    faces.value = data.faces;
  }
  loading.value = false;
}

async function handleDelete(faceId: string) {
  const { error } = await fetchDeleteFaceImage(props.dbName, faceId);
  if (!error) {
    window.$message?.success($t('common.deleteSuccess'));
    loadDetail();
  }
}

async function handleUpload({ file }: UploadCustomRequestOptions) {
  if (!file.file) return;
  uploading.value = true;
  try {
    const { error } = await fetchAddFaceImage(props.dbName, props.entityId, file.file);
    if (!error) {
      window.$message?.success($t('common.addSuccess'));
      loadDetail();
    }
  } finally {
    uploading.value = false;
  }
}

watch(visible, v => {
  if (v) {
    faces.value = [];
    loadDetail();
  }
});
</script>

<template>
  <NDrawer v-model:show="visible" :width="520">
    <NDrawerContent :title="$t('page.manage.face.facesTitle')" closable>
      <NSpin :show="loading || uploading">
        <NSpace vertical :size="12">
          <div class="text-14px">
            {{ $t('page.manage.face.facesSub') }}:
            <span class="font-500">{{ entityId }}</span>
          </div>
          <NUpload
            v-if="hasAuth('face:image:add')"
            :show-file-list="false"
            :custom-request="handleUpload"
            accept="image/*"
          >
            <NButton type="primary">{{ $t('page.manage.face.uploadFace') }}</NButton>
          </NUpload>
          <NEmpty v-if="!faces.length" :description="$t('page.manage.face.noFaces')" />
          <NDataTable
            v-else
            :columns="columns"
            :data="faces"
            size="small"
            :row-key="(r: Api.Face.FaceEntityFace) => r.face_id"
          />
        </NSpace>
      </NSpin>
    </NDrawerContent>
  </NDrawer>
</template>
