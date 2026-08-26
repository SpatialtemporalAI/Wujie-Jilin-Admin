<script setup lang="tsx">
import { onMounted, reactive, ref } from 'vue';
import { NButton, NCard, NDataTable, NTag } from 'naive-ui';
import dayjs from 'dayjs';
import { fetchGetVoiceConsultationSessionList, fetchGetVoiceConsultationStats } from '@/service/api';
import { defaultTransform, useNaivePaginatedTable } from '@/hooks/common/table';
import { useAuth } from '@/hooks/business/auth';
import { useExportSubmit } from '@/hooks/business/export-task';
import { $t } from '@/locales';
import StatCards from './modules/stat-cards.vue';
import IntentBarChart from './modules/intent-bar-chart.vue';
import TriggerPieChart from './modules/trigger-pie-chart.vue';
import SessionSearch from './modules/session-search.vue';
import SessionDetailDrawer from './modules/session-detail-drawer.vue';

defineOptions({ name: 'VoiceConsultation' });

const { hasAuth } = useAuth();
const { submitting, submitExport } = useExportSubmit();

const searchParams: Api.VoiceConsultation.SessionSearchParams = reactive({
  page: 1,
  page_size: 10,
  robot_id: null,
  trigger_method: null,
  status: null,
  intent_type: null,
  keyword: null,
  start_time: undefined,
  end_time: undefined
});

const stats = ref<Api.VoiceConsultation.Stats | null>(null);
const statsLoading = ref(false);

async function loadStats() {
  statsLoading.value = true;
  try {
    const { data, error } = await fetchGetVoiceConsultationStats(searchParams);
    if (!error) {
      stats.value = data;
    }
  } catch (error) {
    console.error('获取语音问诊统计失败:', error);
  } finally {
    statsLoading.value = false;
  }
}

const statusTagMap: Record<string, NaiveUI.ThemeColor> = {
  completed: 'success',
  in_progress: 'info',
  interrupted: 'warning'
};

const triggerTagMap: Record<string, NaiveUI.ThemeColor> = {
  wake_word: 'info'
};

function formatDuration(seconds: number | null): string {
  if (seconds == null) return '-';
  if (seconds < 60) return `${seconds} 秒`;
  const minutes = Math.floor(seconds / 60);
  const rest = seconds % 60;
  return rest > 0 ? `${minutes} 分 ${rest} 秒` : `${minutes} 分`;
}

function formatTime(time: string | null): string {
  return time ? dayjs(time).format('YYYY-MM-DD HH:mm:ss') : '-';
}

const { columns, columnChecks, data, getData, getDataByPage, loading, mobilePagination, pagination } =
  useNaivePaginatedTable({
    api: () => fetchGetVoiceConsultationSessionList(searchParams),
    transform: response => {
      return defaultTransform(response);
    },
    onPaginationParamsChange: params => {
      searchParams.page = params.page;
      searchParams.page_size = params.pageSize;
    },
    columns: () => [
      {
        key: 'occurred_at',
        title: $t('page.manage.voiceConsultation.time'),
        align: 'center',
        width: 170,
        render: row => formatTime(row.occurred_at)
      },
      {
        key: 'trigger_method',
        title: $t('page.manage.voiceConsultation.trigger'),
        align: 'center',
        width: 100,
        render: row => {
          const isFace = row.trigger_method === 'face_recognition';
          return (
            <NTag
              type={isFace ? undefined : (triggerTagMap[row.trigger_method] || 'default')}
              style={isFace ? { backgroundColor: '#b37feb1A', color: '#b37feb', borderColor: '#b37feb80', borderWidth: '1px' } : undefined}
              bordered={!isFace}
              size="small"
            >
              {$t(`page.manage.voiceConsultation.triggerMethod.${row.trigger_method}`)}
            </NTag>
          );
        }
      },
      {
        key: 'robot_name',
        title: $t('page.manage.voiceConsultation.robot'),
        align: 'center',
        width: 110,
        render: row => row.robot_name || '-'
      },
      {
        key: 'turn_count',
        title: $t('page.manage.voiceConsultation.turns'),
        align: 'center',
        width: 70
      },
      {
        key: 'question_summary',
        title: $t('page.manage.voiceConsultation.questionSummary'),
        align: 'center',
        minWidth: 220,
        ellipsis: { tooltip: true },
        render: row => row.question_summary || '-'
      },
      {
        key: 'duration_seconds',
        title: $t('page.manage.voiceConsultation.duration'),
        align: 'center',
        width: 100,
        render: row => formatDuration(row.duration_seconds)
      },
      {
        key: 'status',
        title: $t('page.manage.voiceConsultation.status'),
        align: 'center',
        width: 90,
        render: row => (
          <NTag type={statusTagMap[row.status] || 'default'} size="small">
            {$t(`page.manage.voiceConsultation.statusLabel.${row.status}`)}
          </NTag>
        )
      },
      {
        key: 'operate',
        title: $t('common.operate'),
        align: 'center',
        width: 80,
        render: row => {
          return (
            <NButton type="primary" text size="small" onClick={() => handleViewDetail(row.id)}>
              {$t('page.manage.voiceConsultation.viewDetail')}
            </NButton>
          );
        }
      }
    ]
  });

const detailDrawerVisible = ref(false);
const detailSessionId = ref<number | null>(null);

function handleViewDetail(id: number) {
  detailSessionId.value = id;
  detailDrawerVisible.value = true;
}

function handleSearch() {
  getDataByPage();
  loadStats();
}

onMounted(() => {
  loadStats();
});
</script>

<template>
  <div class="flex-col-stretch gap-12px overflow-y-auto pb-12px">
    <StatCards :stats="stats" :loading="statsLoading" />

    <NGrid cols="s:1 m:1 l:2" responsive="screen" :x-gap="12" :y-gap="12">
      <NGi>
        <IntentBarChart :data="stats?.intent_distribution ?? []" />
      </NGi>
      <NGi>
        <TriggerPieChart :data="stats?.trigger_distribution ?? []" />
      </NGi>
    </NGrid>

    <NCard :bordered="false" size="small" class="card-wrapper">
      <template #header>
        <div class="flex-y-center justify-between gap-12px">
          <div class="flex-y-center gap-8px">
            <span>{{ $t('page.manage.voiceConsultation.records') }}</span>
            <NTag size="small" :bordered="false" type="primary" round>
              {{ pagination.itemCount }}
            </NTag>
          </div>
          <div class="flex-y-center gap-12px">
            <TableHeaderOperation v-model:columns="columnChecks" :loading="loading" :show-add="false"
              :show-delete="false" @refresh="getData">
              <template #prefix>
                <NButton v-if="hasAuth('voice:consultation:export')" type="primary" ghost size="small"
                  :loading="submitting" :disabled="loading" @click="submitExport('voice_consultation', searchParams)">
                  {{ $t('common.export') }}
                </NButton>
              </template>
            </TableHeaderOperation>
          </div>
        </div>
      </template>
      <div class="flex-y-center flex-wrap gap-12px pb-12px">
        <SessionSearch v-model:model="searchParams" @search="handleSearch" />
      </div>
      <NDataTable :columns="columns" :data="data" size="small" :scroll-x="1100" :loading="loading" remote
        :row-key="row => row.id" :pagination="mobilePagination" />
    </NCard>

    <SessionDetailDrawer v-model:visible="detailDrawerVisible" :session-id="detailSessionId" />
  </div>
</template>
