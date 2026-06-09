<script setup lang="tsx">
import { ref, watch } from 'vue';
import { NButton, NDataTable, NPopconfirm, NSpace, NTab, NTabs } from 'naive-ui';
import { defaultTransform, useNaivePaginatedTable } from '@/hooks/common/table';
import {
  fetchGetMapAnnotations,
  fetchDeleteMapAnnotation,
  fetchGetMapObjects,
  fetchDeleteMapObject
} from '@/service/api';
import SceneMapAnnotationModal from './scene-map-annotation-modal.vue';
import SceneMapObjectModal from './scene-map-object-modal.vue';

defineOptions({
  name: 'SceneMapDetailDrawer'
});

interface Props {
  mapData?: Api.Scene.SceneMap | null;
}

const props = defineProps<Props>();

const visible = defineModel<boolean>('visible', {
  default: false
});

/** 当前激活的Tab */
const activeTab = ref('annotation');

/** ========== 标注管理 ========== */
const annotationSearchParams = ref<{ page: number; page_size: number }>({ page: 1, page_size: 10 });

const annotationModalVisible = ref(false);
const editingAnnotation = ref<Api.Scene.SceneMapAnnotation | null>(null);

const {
  columns: annotationColumns,
  data: annotationData,
  getData: getAnnotationData,
  getDataByPage: getAnnotationDataByPage,
  loading: annotationLoading,
  mobilePagination: annotationPagination
} = useNaivePaginatedTable({
  api: () => fetchGetMapAnnotations(props.mapData?.id ?? 0, annotationSearchParams.value),
  transform: response => defaultTransform(response),
  onPaginationParamsChange: params => {
    annotationSearchParams.value.page = params.page;
    annotationSearchParams.value.page_size = params.pageSize;
  },
  columns: () => [
    {
      key: 'index',
      title: '序号',
      align: 'center',
      width: 64,
      render: (_, index) => index + 1
    },
    {
      key: 'name',
      title: '标注名称',
      align: 'center',
      minWidth: 120,
      ellipsis: { tooltip: true }
    },
    {
      key: 'type',
      title: '类型',
      align: 'center',
      width: 100
    },
    {
      key: 'x',
      title: 'X坐标',
      align: 'center',
      width: 80
    },
    {
      key: 'y',
      title: 'Y坐标',
      align: 'center',
      width: 80
    },
    {
      key: 'angle',
      title: '角度',
      align: 'center',
      width: 80
    },
    {
      key: 'operate',
      title: '操作',
      align: 'center',
      width: 150,
      render: (row: any) => {
        return (
          <NSpace size="small" justify="center">
            <NButton type="primary" ghost size="small" onClick={() => handleEditAnnotation(row)}>
              编辑
            </NButton>
            <NPopconfirm onPositiveClick={() => handleDeleteAnnotation(row.id)}>
              {{
                default: () => '确认删除？',
                trigger: () => (
                  <NButton type="error" ghost size="small">
                    删除
                  </NButton>
                )
              }}
            </NPopconfirm>
          </NSpace>
        );
      }
    }
  ]
});

function handleAddAnnotation() {
  editingAnnotation.value = null;
  annotationModalVisible.value = true;
}

function handleEditAnnotation(row: Api.Scene.SceneMapAnnotation) {
  editingAnnotation.value = { ...row };
  annotationModalVisible.value = true;
}

async function handleDeleteAnnotation(id: number) {
  try {
    await fetchDeleteMapAnnotation(props.mapData?.id ?? 0, id);
    window.$message?.success('删除成功');
    getAnnotationDataByPage();
  } catch (error) {
    console.error('删除标注失败:', error);
  }
}

/** ========== 物体管理 ========== */
const objectSearchParams = ref<{ page: number; page_size: number }>({ page: 1, page_size: 10 });

const objectModalVisible = ref(false);
const editingObject = ref<Api.Scene.SceneMapObject | null>(null);

const {
  columns: objectColumns,
  data: objectData,
  getData: getObjectData,
  getDataByPage: getObjectDataByPage,
  loading: objectLoading,
  mobilePagination: objectPagination
} = useNaivePaginatedTable({
  api: () => fetchGetMapObjects(props.mapData?.id ?? 0, objectSearchParams.value),
  transform: response => defaultTransform(response),
  onPaginationParamsChange: params => {
    objectSearchParams.value.page = params.page;
    objectSearchParams.value.page_size = params.pageSize;
  },
  columns: () => [
    {
      key: 'index',
      title: '序号',
      align: 'center',
      width: 64,
      render: (_, index) => index + 1
    },
    {
      key: 'type',
      title: '类型',
      align: 'center',
      width: 100
    },
    {
      key: 'x',
      title: 'X坐标',
      align: 'center',
      width: 80
    },
    {
      key: 'y',
      title: 'Y坐标',
      align: 'center',
      width: 80
    },
    {
      key: 'width',
      title: '宽度',
      align: 'center',
      width: 80
    },
    {
      key: 'height',
      title: '高度',
      align: 'center',
      width: 80
    },
    {
      key: 'operate',
      title: '操作',
      align: 'center',
      width: 150,
      render: (row: any) => {
        return (
          <NSpace size="small" justify="center">
            <NButton type="primary" ghost size="small" onClick={() => handleEditObject(row)}>
              编辑
            </NButton>
            <NPopconfirm onPositiveClick={() => handleDeleteObject(row.id)}>
              {{
                default: () => '确认删除？',
                trigger: () => (
                  <NButton type="error" ghost size="small">
                    删除
                  </NButton>
                )
              }}
            </NPopconfirm>
          </NSpace>
        );
      }
    }
  ]
});

function handleAddObject() {
  editingObject.value = null;
  objectModalVisible.value = true;
}

function handleEditObject(row: Api.Scene.SceneMapObject) {
  editingObject.value = { ...row };
  objectModalVisible.value = true;
}

async function handleDeleteObject(id: number) {
  try {
    await fetchDeleteMapObject(props.mapData?.id ?? 0, id);
    window.$message?.success('删除成功');
    getObjectDataByPage();
  } catch (error) {
    console.error('删除物体失败:', error);
  }
}

/** 抽屉打开时加载数据 */
watch(visible, () => {
  if (visible.value && props.mapData?.id) {
    activeTab.value = 'annotation';
    annotationSearchParams.value = { page: 1, page_size: 10 };
    objectSearchParams.value = { page: 1, page_size: 10 };
    getAnnotationData();
    getObjectData();
  }
});

function closeDrawer() {
  visible.value = false;
}
</script>

<template>
  <NDrawer v-model:show="visible" display-directive="show" :width="'80%'">
    <NDrawerContent title="场景地图详情" :native-scrollbar="false" closable>
      <!-- 地图图片预览 -->
      <div v-if="mapData?.image_id" class="mb-16px">
        <NImage
          :src="`/uploads/${mapData.image_id}`"
          :alt="mapData.name"
          object-fit="contain"
          class="max-h-400px"
          width="100%"
        />
      </div>
      <div v-else class="mb-16px">
        <NEmpty description="暂无地图图片" />
      </div>

      <!-- 地图基本信息 -->
      <NDescriptions bordered :column="3" label-placement="left" size="small" class="mb-16px">
        <NDescriptionsItem label="地图名称">{{ mapData?.name || '-' }}</NDescriptionsItem>
        <NDescriptionsItem label="所属分组">{{ mapData?.group_name || '-' }}</NDescriptionsItem>
        <NDescriptionsItem label="尺寸">{{ mapData?.width && mapData?.height ? `${mapData.width} x ${mapData.height}` : '-' }}</NDescriptionsItem>
      </NDescriptions>

      <!-- 标签页 -->
      <NTabs v-model:value="activeTab" type="line">
        <NTab name="annotation">标注信息</NTab>
        <NTab name="object">物体信息</NTab>
      </NTabs>

      <!-- 标注列表 -->
      <div v-show="activeTab === 'annotation'" class="mt-12px">
        <div class="mb-12px">
          <NButton type="primary" size="small" @click="handleAddAnnotation">
            <template #icon>
              <icon-ic-round-plus class="text-icon" />
            </template>
            新增标注
          </NButton>
        </div>
        <NDataTable
          :columns="annotationColumns"
          :data="annotationData"
          size="small"
          :loading="annotationLoading"
          remote
          :row-key="(row: any) => row.id"
          :pagination="annotationPagination"
        />
      </div>

      <!-- 物体列表 -->
      <div v-show="activeTab === 'object'" class="mt-12px">
        <div class="mb-12px">
          <NButton type="primary" size="small" @click="handleAddObject">
            <template #icon>
              <icon-ic-round-plus class="text-icon" />
            </template>
            新增物体
          </NButton>
        </div>
        <NDataTable
          :columns="objectColumns"
          :data="objectData"
          size="small"
          :loading="objectLoading"
          remote
          :row-key="(row: any) => row.id"
          :pagination="objectPagination"
        />
      </div>

      <template #footer>
        <NSpace :size="16">
          <NButton @click="closeDrawer">关闭</NButton>
        </NSpace>
      </template>
    </NDrawerContent>
  </NDrawer>

  <!-- 标注弹窗 -->
  <SceneMapAnnotationModal
    v-model:visible="annotationModalVisible"
    :map-id="mapData?.id ?? 0"
    :edit-data="editingAnnotation"
    @submitted="getAnnotationDataByPage"
  />

  <!-- 物体弹窗 -->
  <SceneMapObjectModal
    v-model:visible="objectModalVisible"
    :map-id="mapData?.id ?? 0"
    :edit-data="editingObject"
    @submitted="getObjectDataByPage"
  />
</template>

<style scoped></style>
