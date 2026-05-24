<script setup lang="tsx">
import { reactive } from 'vue';
import { NButton, NCard, NDataTable, NPopconfirm, NTag, useMessage } from 'naive-ui';
import { fetchGetOnlineUserList, fetchKickUser, fetchKickAllSessions } from '@/service/api';
import { useAppStore } from '@/store/modules/app';
import { defaultTransform, useNaivePaginatedTable } from '@/hooks/common/table';
import { $t } from '@/locales';
import OnlineUserSearch from './modules/online-user-search.vue';

const appStore = useAppStore();
const message = useMessage();

const searchParams: Api.SystemManage.OnlineUserSearchParams = reactive({
  page: 1,
  page_size: 10,
  username: null,
  ip: null
});

const {
  columns,
  columnChecks,
  data,
  getData,
  getDataByPage,
  loading,
  mobilePagination
} = useNaivePaginatedTable({
  api: () => fetchGetOnlineUserList(searchParams),
  transform: response => defaultTransform(response),
  onPaginationParamsChange: params => {
    searchParams.page = params.page;
    searchParams.page_size = params.pageSize;
  },
  columns: () => [
    {
      key: 'index',
      title: $t('common.index'),
      align: 'center',
      width: 64,
      render: (_, index) => index + 1
    },
    {
      key: 'username',
      title: $t('page.log.onlineUser.username'),
      align: 'center',
      minWidth: 100
    },
    {
      key: 'nickname',
      title: $t('page.log.onlineUser.nickname'),
      align: 'center',
      minWidth: 100
    },
    {
      key: 'ip',
      title: $t('page.log.onlineUser.ip'),
      align: 'center',
      minWidth: 120
    },
    {
      key: 'user_agent',
      title: $t('page.log.onlineUser.userAgent'),
      align: 'center',
      minWidth: 200,
      ellipsis: { tooltip: true }
    },
    {
      key: 'login_time',
      title: $t('page.log.onlineUser.loginTime'),
      align: 'center',
      minWidth: 160
    },
    {
      key: 'operate',
      title: $t('common.operate'),
      align: 'center',
      width: 160,
      render: row => {
        return (
          <NSpace justify="center">
            <NPopconfirm onPositiveClick={() => handleKick(row)}>
              {{
                default: () => $t('page.log.onlineUser.kickConfirm'),
                trigger: () => (
                  <NButton type="warning" text size="small">
                    {$t('page.log.onlineUser.kick')}
                  </NButton>
                )
              }}
            </NPopconfirm>
            <NPopconfirm onPositiveClick={() => handleKickAll(row)}>
              {{
                default: () => $t('page.log.onlineUser.kickAllConfirm'),
                trigger: () => (
                  <NButton type="error" text size="small">
                    {$t('page.log.onlineUser.kickAll')}
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

async function handleKick(row: Api.SystemManage.OnlineUser) {
  try {
    await fetchKickUser({ user_id: row.user_id, session_id: row.session_id });
    message.success($t('page.log.onlineUser.kickSuccess'));
    getData();
  } catch (error) {
    message.error($t('common.updateFailed'));
  }
}

async function handleKickAll(row: Api.SystemManage.OnlineUser) {
  try {
    await fetchKickAllSessions({ user_id: row.user_id });
    message.success($t('page.log.onlineUser.kickAllSuccess'));
    getData();
  } catch (error) {
    message.error($t('common.updateFailed'));
  }
}
</script>

<template>
  <div class="min-h-500px flex-col-stretch gap-16px overflow-hidden lt-sm:overflow-auto">
    <OnlineUserSearch v-model:model="searchParams" @search="getDataByPage" />
    <NCard :title="$t('page.log.onlineUser.title')" :bordered="false" size="small" class="flex-1-hidden card-wrapper">
      <template #header-extra>
        <TableHeaderOperation
          v-model:columns="columnChecks"
          :loading="loading"
          :show-add="false"
          :show-delete="false"
          @refresh="getData"
        />
      </template>
      <NDataTable
        :columns="columns"
        :data="data"
        size="small"
        :flex-height="!appStore.isMobile"
        :scroll-x="900"
        :loading="loading"
        remote
        :row-key="row => row.session_id"
        :pagination="mobilePagination"
        class="sm:h-full"
      />
    </NCard>
  </div>
</template>
