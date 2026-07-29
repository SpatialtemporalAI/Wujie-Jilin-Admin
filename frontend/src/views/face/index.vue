<script setup lang="ts">
import { computed, h, onMounted, reactive, ref, watch } from 'vue';
import type { VNode } from 'vue';
import { NButton, NCard, NDataTable, NInput, NPopconfirm, NSelect, NSpace, NTabPane, NTabs } from 'naive-ui';
import type { SelectOption } from 'naive-ui';
import {
  fetchAddFaceEntity,
  fetchCreateFaceDb,
  fetchDeleteFaceEntity,
  fetchGetFaceDbList,
  fetchGetFaceEntityList
} from '@/service/api';
import { useAppStore } from '@/store/modules/app';
import { defaultTransform, useNaivePaginatedTable } from '@/hooks/common/table';
import { useAuth } from '@/hooks/business/auth';
import { $t } from '@/locales';
import FaceEntityFacesDrawer from './modules/face-entity-faces-drawer.vue';
import FaceSearch from './modules/face-search.vue';
import FaceDetect from './modules/face-detect.vue';

const appStore = useAppStore();
const { hasAuth } = useAuth();

// ------------------------------ 人脸库选择 ------------------------------
const dbList = ref<string[]>([]);
const dbLoading = ref(false);
const selectedDb = ref<string | null>(null);
const newDbName = ref('');

const dbSelectOptions = computed<SelectOption[]>(() => dbList.value.map(d => ({ label: d, value: d })));

async function loadDbs() {
  dbLoading.value = true;
  const { data, error } = await fetchGetFaceDbList();
  if (!error && data) {
    dbList.value = data.db_list;
    if (!selectedDb.value && data.db_list.length > 0) {
      selectedDb.value = data.db_list[0];
    }
  }
  dbLoading.value = false;
}

async function handleCreateDb() {
  const name = newDbName.value.trim();
  if (!name) return;
  const { error } = await fetchCreateFaceDb(name);
  if (!error) {
    window.$message?.success($t('common.addSuccess'));
    newDbName.value = '';
    await loadDbs();
    selectedDb.value = name;
  }
}

// ------------------------------ 实体表格 ------------------------------
const searchParams = reactive<{ page: number; page_size: number }>({ page: 1, page_size: 10 });
const newEntityId = ref('');

const { columns, data, loading, getDataByPage, mobilePagination } = useNaivePaginatedTable({
  api: () => fetchGetFaceEntityList({ ...searchParams, db_name: selectedDb.value as string }),
  transform: response => defaultTransform(response),
  immediate: false,
  onPaginationParamsChange: params => {
    searchParams.page = params.page ?? 1;
    searchParams.page_size = params.pageSize ?? 10;
  },
  columns: () => [
    { key: 'index', title: $t('common.index'), width: 64, align: 'center', render: (_, index) => index + 1 },
    { key: 'entity_id', title: $t('page.manage.face.entityId'), minWidth: 160 },
    { key: 'face_count', title: $t('page.manage.face.faceCount'), width: 100, align: 'center' },
    { key: 'labels', title: $t('page.manage.face.labels'), minWidth: 120, ellipsis: { tooltip: true } },
    { key: 'created_at', title: $t('page.manage.face.createdAt'), minWidth: 160 },
    {
      key: 'operate',
      title: $t('common.operate'),
      align: 'center',
      width: 200,
      render: (row: Api.Face.FaceEntity) => {
        const ops: VNode[] = [];
        if (hasAuth('face:entity:list')) {
          ops.push(
            h(
              NButton,
              { type: 'primary', text: true, size: 'small', onClick: () => openFaces(row) },
              { default: () => $t('page.manage.face.viewFaces') }
            )
          );
        }
        if (hasAuth('face:entity:delete')) {
          ops.push(
            h(
              NPopconfirm,
              { onPositiveClick: () => handleDeleteEntity(row) },
              {
                default: () => $t('common.confirmDelete'),
                trigger: () =>
                  h(NButton, { type: 'error', text: true, size: 'small' }, { default: () => $t('common.delete') })
              }
            )
          );
        }
        return h('div', { class: 'flex flex-wrap justify-center gap-8px' }, ops);
      }
    }
  ]
});

async function handleAddEntity() {
  if (!selectedDb.value) {
    window.$message?.warning($t('page.manage.face.selectDbFirst'));
    return;
  }
  const entityId = newEntityId.value.trim();
  if (!entityId) {
    window.$message?.warning($t('page.manage.face.entityIdPlaceholder'));
    return;
  }
  const { error } = await fetchAddFaceEntity(selectedDb.value, entityId);
  if (!error) {
    window.$message?.success($t('common.addSuccess'));
    newEntityId.value = '';
    getDataByPage();
  }
}

async function handleDeleteEntity(row: Api.Face.FaceEntity) {
  if (!selectedDb.value) return;
  const { error } = await fetchDeleteFaceEntity(selectedDb.value, row.entity_id);
  if (!error) {
    window.$message?.success($t('common.deleteSuccess'));
    getDataByPage();
  }
}

// 切换人脸库时重新加载实体（重置到第 1 页）
watch(selectedDb, v => {
  if (v) getDataByPage();
});

// ------------------------------ 人脸图片抽屉 ------------------------------
const facesVisible = ref(false);
const facesEntity = ref<Api.Face.FaceEntity | null>(null);

function openFaces(row: Api.Face.FaceEntity) {
  facesEntity.value = row;
  facesVisible.value = true;
}

onMounted(() => {
  loadDbs();
});
</script>

<template>
  <div class="min-h-500px flex-col-stretch gap-16px overflow-hidden lt-sm:overflow-auto">
    <NTabs
      type="line"
      animated
      class="h-full min-h-0 flex flex-col"
      pane-wrapper-class="min-h-0 flex-1"
      pane-class="h-full min-h-0"
    >
      <!-- 人脸库管理 -->
      <NTabPane name="manage" :tab="$t('page.manage.face.title')">
        <div class="h-full min-h-0 flex flex-col gap-16px">
          <NCard :bordered="false" size="small" class="card-wrapper">
            <NSpace align="center" :wrap="true" :size="12">
              <span class="text-14px">{{ $t('page.manage.face.selectDb') }}</span>
              <NSelect
                v-model:value="selectedDb"
                :options="dbSelectOptions"
                :loading="dbLoading"
                :placeholder="$t('page.manage.face.selectDb')"
                style="width: 240px"
              />
              <NButton @click="loadDbs">
                <template #icon>
                  <icon-ic-round-refresh class="text-icon" />
                </template>
                {{ $t('common.refresh') }}
              </NButton>
              <NInput
                v-model:value="newDbName"
                :placeholder="$t('page.manage.face.dbNamePlaceholder')"
                style="width: 220px"
              />
              <NButton v-if="hasAuth('face:db:create')" type="primary" @click="handleCreateDb">
                {{ $t('page.manage.face.createDb') }}
              </NButton>
            </NSpace>
          </NCard>

          <NCard
            :title="$t('page.manage.face.title')"
            :bordered="false"
            size="small"
            class="min-h-0 card-wrapper sm:flex-1-hidden"
          >
            <template #header-extra>
              <NSpace align="center" :size="8">
                <NInput
                  v-model:value="newEntityId"
                  :placeholder="$t('page.manage.face.entityIdPlaceholder')"
                  style="width: 220px"
                />
                <NButton v-if="hasAuth('face:entity:add')" type="primary" @click="handleAddEntity">
                  {{ $t('page.manage.face.addEntity') }}
                </NButton>
              </NSpace>
            </template>
            <NDataTable
              :columns="columns"
              :data="data"
              size="small"
              :flex-height="!appStore.isMobile"
              :scroll-x="900"
              :loading="loading"
              remote
              :row-key="(row: Api.Face.FaceEntity) => row.entity_id"
              :pagination="mobilePagination"
              class="sm:h-full"
            />
          </NCard>
        </div>
      </NTabPane>

      <!-- 人脸搜索 -->
      <NTabPane name="search" :tab="$t('page.manage.face.searchTitle')">
        <FaceSearch :db-options="dbList" :db-name="selectedDb" />
      </NTabPane>

      <!-- 人脸检测 -->
      <NTabPane name="detect" :tab="$t('page.manage.face.detectTitle')">
        <FaceDetect />
      </NTabPane>
    </NTabs>

    <FaceEntityFacesDrawer
      v-if="facesEntity"
      v-model="facesVisible"
      :db-name="selectedDb || ''"
      :entity-id="facesEntity.entity_id"
    />
  </div>
</template>
