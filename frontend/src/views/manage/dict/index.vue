<script setup lang="tsx">
import { reactive, ref, watch } from 'vue';
import { NButton, NCard, NDataTable, NPopconfirm, NTabPane, NTabs, NTag, useMessage } from 'naive-ui';
import { enableStatusRecord } from '@/constants/business';
import {
  fetchCreateDict,
  fetchCreateDictItem,
  fetchDeleteDict,
  fetchDeleteDictItem,
  fetchGetDictItemList,
  fetchGetDictList,
  fetchUpdateDict,
  fetchUpdateDictItem
} from '@/service/api';
import { useAppStore } from '@/store/modules/app';
import { defaultTransform, useNaivePaginatedTable, useTableOperate } from '@/hooks/common/table';
import { $t } from '@/locales';
import DictOperateDrawer from './modules/dict-operate-drawer.vue';
import DictItemOperateDrawer from './modules/dict-item-operate-drawer.vue';
import DictSearch from './modules/dict-search.vue';

const appStore = useAppStore();
const message = useMessage();

/** 字典搜索参数 */
const dictSearchParams: Api.SystemManage.DictSearchParams = reactive({
  page: 1,
  page_size: 10,
  name: null,
  code: null,
  status: null,
  is_system: null
});

/** 当前选中的字典 */
const selectedDict = ref<Api.SystemManage.Dict | null>(null);

/** 字典项搜索参数 */
const dictItemSearchParams: Api.SystemManage.DictItemSearchParams = reactive({
  page: 1,
  page_size: 10,
  dict_id: null,
  label: null,
  value: null,
  status: null
});

/** 字典表格 */
const {
  columns: dictColumns,
  columnChecks: dictColumnChecks,
  data: dictData,
  getData: getDictData,
  getDataByPage: getDictDataByPage,
  loading: dictLoading,
  mobilePagination: dictMobilePagination
} = useNaivePaginatedTable({
  api: () => fetchGetDictList(dictSearchParams),
  transform: response => defaultTransform(response),
  onPaginationParamsChange: params => {
    dictSearchParams.page = params.page;
    dictSearchParams.page_size = params.pageSize;
  },
  columns: () => [
    {
      type: 'selection',
      align: 'center',
      width: 48
    },
    {
      key: 'index',
      title: $t('common.index'),
      align: 'center',
      width: 64,
      render: (_, index) => index + 1
    },
    {
      key: 'name',
      title: $t('page.manage.dict.dictName'),
      align: 'center',
      minWidth: 120
    },
    {
      key: 'code',
      title: $t('page.manage.dict.dictCode'),
      align: 'center',
      minWidth: 120
    },
    {
      key: 'description',
      title: $t('page.manage.dict.dictDesc'),
      align: 'center',
      minWidth: 200
    },
    {
      key: 'status',
      title: $t('page.manage.dict.dictStatus'),
      align: 'center',
      width: 100,
      render: row => {
        const status: Api.Common.EnableStatus = row.status ? '1' : '2';
        const tagMap: Record<Api.Common.EnableStatus, NaiveUI.ThemeColor> = {
          '1': 'success',
          '2': 'warning'
        };
        const label = $t(enableStatusRecord[status]);
        return <NTag type={tagMap[status]}>{label}</NTag>;
      }
    },
    {
      key: 'is_system',
      title: $t('page.manage.dict.isSystem'),
      align: 'center',
      width: 100,
      render: row => {
        return <NTag type={row.is_system ? 'info' : 'default'}>{row.is_system ? $t('common.yesOrNo.yes') : $t('common.yesOrNo.no')}</NTag>;
      }
    },
    {
      key: 'sort',
      title: $t('page.manage.dict.sort'),
      align: 'center',
      width: 80
    },
    {
      key: 'operate',
      title: $t('common.operate'),
      align: 'center',
      width: 180,
      render: row => {
        return (
          <div class="flex-center gap-8px">
            <NButton type="primary" ghost size="small" onClick={() => handleSelectDict(row)}>
              {$t('page.manage.dict.itemManage')}
            </NButton>
            <NButton type="info" ghost size="small" onClick={() => editDict(row.id)}>
              {$t('common.edit')}
            </NButton>
            {!row.is_system && (
              <NPopconfirm onPositiveClick={() => handleDeleteDict(row.id)}>
                {{
                  default: () => $t('common.confirmDelete'),
                  trigger: () => (
                    <NButton type="error" ghost size="small">
                      {$t('common.delete')}
                    </NButton>
                  )
                }}
              </NPopconfirm>
            )}
          </div>
        );
      }
    }
  ]
});

/** 字典操作 */
const {
  drawerVisible: dictDrawerVisible,
  operateType: dictOperateType,
  editingData: editingDictData,
  handleAdd: handleAddDict,
  handleEdit: handleEditDict,
  checkedRowKeys: checkedDictRowKeys,
  onBatchDeleted: onDictBatchDeleted,
  onDeleted: onDictDeleted
} = useTableOperate(dictData, 'id', getDictData);

/** 字典项表格 */
const {
  columns: dictItemColumns,
  columnChecks: dictItemColumnChecks,
  data: dictItemData,
  getData: getDictItemData,
  getDataByPage: getDictItemDataByPage,
  loading: dictItemLoading,
  mobilePagination: dictItemMobilePagination
} = useNaivePaginatedTable({
  api: () => fetchGetDictItemList(dictItemSearchParams),
  transform: response => defaultTransform(response),
  onPaginationParamsChange: params => {
    dictItemSearchParams.page = params.page;
    dictItemSearchParams.page_size = params.pageSize;
  },
  columns: () => [
    {
      type: 'selection',
      align: 'center',
      width: 48
    },
    {
      key: 'index',
      title: $t('common.index'),
      align: 'center',
      width: 64,
      render: (_, index) => index + 1
    },
    {
      key: 'value',
      title: $t('page.manage.dict.itemValue'),
      align: 'center',
      minWidth: 120
    },
    {
      key: 'label',
      title: $t('page.manage.dict.itemLabel'),
      align: 'center',
      minWidth: 120
    },
    {
      key: 'description',
      title: $t('page.manage.dict.itemDesc'),
      align: 'center',
      minWidth: 200
    },
    {
      key: 'status',
      title: $t('page.manage.dict.itemStatus'),
      align: 'center',
      width: 100,
      render: row => {
        const status: Api.Common.EnableStatus = row.status ? '1' : '2';
        const tagMap: Record<Api.Common.EnableStatus, NaiveUI.ThemeColor> = {
          '1': 'success',
          '2': 'warning'
        };
        const label = $t(enableStatusRecord[status]);
        return <NTag type={tagMap[status]}>{label}</NTag>;
      }
    },
    {
      key: 'sort',
      title: $t('page.manage.dict.sort'),
      align: 'center',
      width: 80
    },
    {
      key: 'operate',
      title: $t('common.operate'),
      align: 'center',
      width: 150,
      render: row => {
        return (
          <div class="flex-center gap-8px">
            <NButton type="info" ghost size="small" onClick={() => editDictItem(row.id)}>
              {$t('common.edit')}
            </NButton>
            <NPopconfirm onPositiveClick={() => handleDeleteDictItem(row.id)}>
              {{
                default: () => $t('common.confirmDelete'),
                trigger: () => (
                  <NButton type="error" ghost size="small">
                    {$t('common.delete')}
                  </NButton>
                )
              }}
            </NPopconfirm>
          </div>
        );
      }
    }
  ]
});

/** 字典项操作 */
const {
  drawerVisible: dictItemDrawerVisible,
  operateType: dictItemOperateType,
  editingData: editingDictItemData,
  handleAdd: handleAddDictItem,
  handleEdit: handleEditDictItem,
  checkedRowKeys: checkedDictItemRowKeys,
  onBatchDeleted: onDictItemBatchDeleted,
  onDeleted: onDictItemDeleted
} = useTableOperate(dictItemData, 'id', getDictItemData);

/** 选中字典 */
function handleSelectDict(row: Api.SystemManage.Dict) {
  selectedDict.value = row;
  dictItemSearchParams.dict_id = row.id;
  dictItemSearchParams.page = 1;
  getDictItemDataByPage();
}

/** 编辑字典 */
function editDict(id: number) {
  handleEditDict(id);
}

/** 删除字典 */
async function handleDeleteDict(id: number) {
  try {
    await fetchDeleteDict(id);
    message.success($t('common.deleteSuccess'));
    onDictDeleted();
  } catch (error) {
    console.error('删除字典失败:', error);
  }
}

/** 编辑字典项 */
function editDictItem(id: number) {
  handleEditDictItem(id);
}

/** 删除字典项 */
async function handleDeleteDictItem(id: number) {
  try {
    await fetchDeleteDictItem(id);
    message.success($t('common.deleteSuccess'));
    onDictItemDeleted();
  } catch (error) {
    console.error('删除字典项失败:', error);
  }
}

/** 批量删除字典 */
async function handleBatchDeleteDict() {
  console.log('批量删除字典:', checkedDictRowKeys.value);
  onDictBatchDeleted();
}

/** 批量删除字典项 */
async function handleBatchDeleteDictItem() {
  console.log('批量删除字典项:', checkedDictItemRowKeys.value);
  onDictItemBatchDeleted();
}
</script>

<template>
  <div class="min-h-500px flex-col-stretch gap-16px overflow-hidden lt-sm:overflow-auto">
    <NTabs type="line">
      <NTabPane name="dict" :tab="$t('page.manage.dict.dictManage')">
        <DictSearch v-model:model="dictSearchParams" @search="getDictDataByPage" />
        <NCard :title="$t('page.manage.dict.title')" :bordered="false" size="small" class="card-wrapper sm:flex-1-hidden">
          <template #header-extra>
            <TableHeaderOperation
              v-model:columns="dictColumnChecks"
              :disabled-delete="checkedDictRowKeys.length === 0"
              :loading="dictLoading"
              @add="handleAddDict"
              @delete="handleBatchDeleteDict"
              @refresh="getDictData"
            />
          </template>
          <NDataTable
            v-model:checked-row-keys="checkedDictRowKeys"
            :columns="dictColumns"
            :data="dictData"
            size="small"
            :flex-height="!appStore.isMobile"
            :scroll-x="962"
            :loading="dictLoading"
            remote
            :row-key="row => row.id"
            :pagination="dictMobilePagination"
            class="sm:h-full"
          />
          <DictOperateDrawer
            v-model:visible="dictDrawerVisible"
            :operate-type="dictOperateType"
            :row-data="editingDictData"
            @submitted="getDictDataByPage"
          />
        </NCard>
      </NTabPane>
      <NTabPane name="dictItem" :tab="$t('page.manage.dict.itemManage')" :disabled="!selectedDict">
        <div class="mb-16px">
          <NButton type="info" ghost size="small" @click="selectedDict = null; dictItemSearchParams.dict_id = null">
            {{ $t('common.back') }}
          </NButton>
          <span class="ml-8px">{{ selectedDict ? `${$t('page.manage.dict.dictName')}: ${selectedDict.name}` : '' }}</span>
        </div>
        <NCard :title="$t('page.manage.dict.itemTitle')" :bordered="false" size="small" class="card-wrapper sm:flex-1-hidden">
          <template #header-extra>
            <TableHeaderOperation
              v-model:columns="dictItemColumnChecks"
              :disabled-delete="checkedDictItemRowKeys.length === 0"
              :loading="dictItemLoading"
              :disabled-add="!selectedDict"
              @add="handleAddDictItem"
              @delete="handleBatchDeleteDictItem"
              @refresh="getDictItemData"
            />
          </template>
          <NDataTable
            v-model:checked-row-keys="checkedDictItemRowKeys"
            :columns="dictItemColumns"
            :data="dictItemData"
            size="small"
            :flex-height="!appStore.isMobile"
            :scroll-x="962"
            :loading="dictItemLoading"
            remote
            :row-key="row => row.id"
            :pagination="dictItemMobilePagination"
            class="sm:h-full"
          />
          <DictItemOperateDrawer
            v-model:visible="dictItemDrawerVisible"
            :operate-type="dictItemOperateType"
            :row-data="editingDictItemData"
            :dict-id="selectedDict?.id"
            @submitted="getDictItemDataByPage"
          />
        </NCard>
      </NTabPane>
    </NTabs>
  </div>
</template>

<style scoped></style>
