<script setup lang="tsx">
import { reactive, ref } from 'vue';
import { NButton, NPopconfirm, NTag, useMessage } from 'naive-ui';
import { enableStatusRecord, userGenderRecord } from '@/constants/business';
import { fetchGetUserList, fetchDeleteUser } from '@/service/api';
import { useAppStore } from '@/store/modules/app';
import { defaultTransform, useNaivePaginatedTable, useTableOperate } from '@/hooks/common/table';
import UserOperateDrawer from './modules/user-operate-drawer.vue';
import UserPasswordDrawer from './modules/user-password-drawer.vue';
import UserSearch from './modules/user-search.vue';
import { $t } from '@/locales';

const appStore = useAppStore();
const message = useMessage();

// 密码修改相关状态
const passwordDrawerVisible = ref(false);
const currentUserId = ref(0);

const searchParams: Api.SystemManage.UserSearchParams = reactive({
  page: 1,
  page_size: 10,
  status: null,
  username: null,
  nickname: null,
  phone: null,
  email: null,
  isSuperuser: null
});

const { columns, columnChecks, data, getData, getDataByPage, loading, mobilePagination } = useNaivePaginatedTable({
  api: () => fetchGetUserList(searchParams),
  transform: response => defaultTransform(response),
  onPaginationParamsChange: params => {
    searchParams.page = params.page;
    searchParams.page_size = params.pageSize;
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
      key: 'username',
      title: $t('page.manage.user.userName'),
      align: 'center',
      minWidth: 100
    },
    {
      key: 'nickname',
      title: $t('page.manage.user.nickName'),
      align: 'center',
      minWidth: 100
    },
    {
      key: 'phone',
      title: $t('page.manage.user.userPhone'),
      align: 'center',
      width: 120
    },
    {
      key: 'email',
      title: $t('page.manage.user.userEmail'),
      align: 'center',
      minWidth: 200
    },
    {
      key: 'last_login_at',
      title: $t('page.manage.user.lastLoginTime'),
      align: 'center',
      minWidth: 100
    },
    {
      key: 'last_login_ip',
      title: $t('page.manage.user.lastLoginIp'),
      align: 'center',
      minWidth: 100
    },
    {
      key: 'status',
      title: $t('page.manage.user.userStatus'),
      align: 'center',
      width: 100,
      render: row => {
        if (row.status === null) {
          return null;
        }

        // let status: Api.Common.EnableStatus = row.status ? '1' : '2';

        const tagMap: Record<Api.Common.EnableStatus, NaiveUI.ThemeColor> = {
          '1': 'success',
          '2': 'warning'
        };

        const label = $t(enableStatusRecord[row.status]);

        return <NTag type={tagMap[row.status]}>{label}</NTag>;
      }
    },
    {
      key: 'operate',
      title: $t('common.operate'),
      align: 'center',
      width: 130,
      render: row => {
        if (row.is_superuser === true) {
          return null;
        }
        return <div class="flex-center gap-8px">
          <NButton type="primary" ghost size="small" onClick={() => edit(row.id)}>
            {$t('common.edit')}
          </NButton>
          <NButton type="info" ghost size="small" onClick={() => openPasswordDrawer(row.id)}>
            {$t('common.changePassword')}
          </NButton>
          <NPopconfirm onPositiveClick={() => handleDelete(row.id)}>
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
      }
    }
  ]
});

const {
  drawerVisible,
  operateType,
  editingData,
  handleAdd,
  handleEdit,
  checkedRowKeys,
  onBatchDeleted,
  onDeleted
  // closeDrawer
} = useTableOperate(data, 'id', getData);

async function handleBatchDelete() {
  if (checkedRowKeys.value.length === 0) {
    message.warning($t('common.selectAtLeastOne'));
    return;
  }

  try {
    for (const id of checkedRowKeys.value) {
      await fetchDeleteUser(Number(id));
    }
    onBatchDeleted();
  } catch (error) {
    message.error($t('common.deleteFailed'));
    console.error('Batch delete users failed:', error);
  }
}

async function handleDelete(id: number) {
  try {
    await fetchDeleteUser(id);
    onDeleted();
  } catch (error) {
    message.error($t('common.deleteFailed'));
    console.error('Delete user failed:', error);
  }
}

function edit(id: number) {
  handleEdit(id);
}

// 打开修改密码抽屉
function openPasswordDrawer(id: number) {
  currentUserId.value = id;
  passwordDrawerVisible.value = true;
}
</script>

<template>
  <div class="min-h-500px flex-col-stretch gap-16px overflow-hidden lt-sm:overflow-auto">
    <UserSearch v-model:model="searchParams" @search="getDataByPage" />
    <NCard :title="$t('page.manage.user.title')" :bordered="false" size="small" class="card-wrapper sm:flex-1-hidden">
      <template #header-extra>
        <TableHeaderOperation v-model:columns="columnChecks" :disabled-delete="checkedRowKeys.length === 0"
          :loading="loading" @add="handleAdd" @delete="handleBatchDelete" @refresh="getData" />
      </template>
      <NDataTable v-model:checked-row-keys="checkedRowKeys" :columns="columns" :data="data" size="small"
        :flex-height="!appStore.isMobile" :scroll-x="962" :loading="loading" remote :row-key="row => row.id"
        :pagination="mobilePagination" class="sm:h-full" />
      <UserOperateDrawer v-model:visible="drawerVisible" :operate-type="operateType" :row-data="editingData"
        @submitted="getDataByPage" />
      <UserPasswordDrawer v-model:visible="passwordDrawerVisible" :user-id="currentUserId" @submitted="getDataByPage" />
    </NCard>
  </div>
</template>

<style scoped></style>
