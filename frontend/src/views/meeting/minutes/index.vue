<script setup lang="tsx">
import { computed, onMounted, reactive, ref } from 'vue';
import { NButton, NCard, NDataTable, NDrawer, NDrawerContent, NPopconfirm, NTag, useMessage } from 'naive-ui';
import type { FlatResponseData } from '@sa/axios';
import {
  fetchClearMinuteTrash,
  fetchDeleteMinute,
  fetchExportMinute,
  fetchGetMinuteDetail,
  fetchGetMinuteList,
  fetchGetMinuteTrash,
  fetchGetVoiceprintRobots,
  fetchPurgeMinute,
  fetchRestoreMinute,
  fetchUpdateSegmentSpeaker
} from '@/service/api';
import { useAppStore } from '@/store/modules/app';
import { defaultTransform, useNaivePaginatedTable } from '@/hooks/common/table';
import { useAuth } from '@/hooks/business/auth';
import { $t } from '@/locales';

defineOptions({
  name: 'MeetingMinutes'
});

const message = useMessage();
const appStore = useAppStore();
const { hasAuth } = useAuth();

const TIME_RANGE_OPTIONS = [
  { label: '全部时间', value: 'all' },
  { label: '今天', value: 'today' },
  { label: '最近 7 天', value: '7' },
  { label: '最近 30 天', value: '30' }
];

const SORT_OPTIONS = [
  { label: '由近到远', value: 'desc' },
  { label: '由远到近', value: 'asc' }
];

function formatDuration(seconds: number) {
  const value = Number(seconds) || 0;
  const minutes = Math.floor(value / 60);
  const rest = value % 60;
  return minutes > 0 ? `${minutes} 分 ${rest} 秒` : `${rest} 秒`;
}

/** ==================== 机器人筛选项 ==================== */

const robots = ref<Api.Meeting.VoiceprintRobot[]>([]);
const robotOptions = computed(() => robots.value.map(item => ({ label: item.name, value: item.id })));

async function loadRobots() {
  const { data, error } = await fetchGetVoiceprintRobots();
  if (!error) robots.value = data || [];
}

/** ==================== 列表 ==================== */

const trashMode = ref(false);

const searchParams: Api.Meeting.MinuteSearchParams = reactive({
  page: 1,
  page_size: 10,
  keyword: null,
  robot_id: null,
  time_range: 'all',
  sort: 'desc'
});

const {
  columns: minuteColumns,
  columnChecks: minuteColumnChecks,
  data: minuteData,
  getData: getMinuteData,
  getDataByPage: getMinuteDataByPage,
  loading: minuteLoading,
  mobilePagination: minuteMobilePagination
} = useNaivePaginatedTable<FlatResponseData<any, Api.Meeting.MinuteList>, Api.Meeting.MinuteListItem>({
  api: () => (trashMode.value ? fetchGetMinuteTrash(searchParams) : fetchGetMinuteList(searchParams)),
  transform: defaultTransform,
  onPaginationParamsChange: params => {
    searchParams.page = params.page;
    searchParams.page_size = params.pageSize;
  },
  columns: () => [
    {
      key: 'title',
      title: '会议标题',
      align: 'left',
      minWidth: 200,
      ellipsis: { tooltip: true }
    },
    {
      key: 'meeting_no',
      title: '会议编号',
      align: 'center',
      width: 190,
      ellipsis: { tooltip: true }
    },
    {
      key: 'robot_name',
      title: '机器人',
      align: 'center',
      width: 140,
      ellipsis: { tooltip: true }
    },
    {
      key: 'started_at',
      title: '会议开始时间',
      align: 'center',
      width: 170
    },
    {
      key: 'duration_seconds',
      title: '时长',
      align: 'center',
      width: 110,
      render: row => formatDuration(row.duration_seconds)
    },
    {
      key: 'speaker_count',
      title: '发言人',
      align: 'center',
      width: 90
    },
    {
      key: 'segment_count',
      title: '逐字稿',
      align: 'center',
      width: 90
    },
    {
      key: 'created_at',
      title: '上报时间',
      align: 'center',
      width: 170
    },
    {
      key: 'operate',
      title: $t('common.operate'),
      align: 'center',
      width: 220,
      fixed: 'right',
      render: row => {
        if (trashMode.value) {
          return (
            <div class="flex-center gap-8px">
              {hasAuth('meeting:minutes:delete') && (
                <NPopconfirm onPositiveClick={() => handleRestore(row.id)}>
                  {{
                    default: () => '确认恢复到列表？',
                    trigger: () => (
                      <NButton type="primary" ghost size="small">
                        恢复
                      </NButton>
                    )
                  }}
                </NPopconfirm>
              )}
              {hasAuth('meeting:minutes:delete') && (
                <NPopconfirm onPositiveClick={() => handlePurge(row.id)}>
                  {{
                    default: () => '彻底删除后不可恢复，确认删除？',
                    trigger: () => (
                      <NButton type="error" ghost size="small">
                        彻底删除
                      </NButton>
                    )
                  }}
                </NPopconfirm>
              )}
            </div>
          );
        }

        return (
          <div class="flex-center gap-8px">
            <NButton type="primary" ghost size="small" onClick={() => openDetail(row.id)}>
              详情
            </NButton>
            {hasAuth('meeting:minutes:export') && (
              <NButton size="small" onClick={() => handleExport(row.id)}>
                导出
              </NButton>
            )}
            {hasAuth('meeting:minutes:delete') && (
              <NPopconfirm onPositiveClick={() => handleDelete(row.id)}>
                {{
                  default: () => '确认移入回收站？',
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

function handleToggleTrash() {
  trashMode.value = !trashMode.value;
  searchParams.page = 1;
  getMinuteDataByPage(1);
}

async function handleDelete(minuteId: number) {
  const { error } = await fetchDeleteMinute(minuteId);
  if (error) return;
  message.success('已移入回收站');
  getMinuteData();
}

async function handleRestore(minuteId: number) {
  const { error } = await fetchRestoreMinute(minuteId);
  if (error) return;
  message.success('恢复成功');
  getMinuteData();
}

async function handlePurge(minuteId: number) {
  const { error } = await fetchPurgeMinute(minuteId);
  if (error) return;
  message.success('彻底删除成功');
  getMinuteData();
}

async function handleClearTrash() {
  const { data, error } = await fetchClearMinuteTrash();
  if (error || !data) return;
  message.success(`已彻底删除 ${data.purged_count} 条会议纪要`);
  getMinuteDataByPage(1);
}

function downloadTextFile(filename: string, content: string, mimeType: string) {
  const blob = new Blob([content], { type: mimeType || 'text/plain;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

async function handleExport(minuteId: number) {
  const { data, error } = await fetchExportMinute(minuteId, 'md');
  if (error || !data) return;
  downloadTextFile(data.filename, data.content, data.mime_type);
}

/** ==================== 详情抽屉 ==================== */

const detailVisible = ref(false);
const detailLoading = ref(false);
const detail = ref<Api.Meeting.MinuteDetail | null>(null);

const speakerOptions = computed(() =>
  (detail.value?.speakers || []).map(item => ({ label: item.name, value: item.id }))
);

function getSpeakerName(segment: Api.Meeting.MinuteSegment) {
  const speaker = detail.value?.speakers.find(item => item.id === segment.speaker_id);
  return speaker?.name || '未识别';
}

function formatSegmentTime(segment: Api.Meeting.MinuteSegment) {
  if (segment.timecode) return segment.timecode;
  if (segment.start_seconds === null || segment.start_seconds === undefined) return '';
  return formatDuration(Math.floor(segment.start_seconds));
}

async function loadDetail(minuteId: number) {
  detailLoading.value = true;
  try {
    const { data, error } = await fetchGetMinuteDetail(minuteId);
    if (!error && data) detail.value = data;
  } finally {
    detailLoading.value = false;
  }
}

async function openDetail(minuteId: number) {
  detailVisible.value = true;
  detail.value = null;
  await loadDetail(minuteId);
}

async function handleReassign(segment: Api.Meeting.MinuteSegment, speakerId: number) {
  if (segment.speaker_id === speakerId) return;
  const { error } = await fetchUpdateSegmentSpeaker(segment.id, speakerId);
  if (error) return;
  message.success('发言人改派成功');
  if (detail.value) await loadDetail(detail.value.id);
}

onMounted(() => {
  loadRobots();
});
</script>

<template>
  <div class="min-h-500px flex-col-stretch gap-16px overflow-hidden lt-sm:overflow-auto">
    <div class="flex-y-center flex-wrap justify-between gap-12px">
      <div class="flex-y-center flex-wrap gap-12px">
        <NInput
          v-model:value="searchParams.keyword"
          placeholder="搜索标题 / 总结 / 发言人"
          clearable
          :style="{ width: '220px' }"
          @update:value="getMinuteDataByPage(1)"
        />
        <NSelect
          v-model:value="searchParams.robot_id"
          :options="robotOptions"
          placeholder="全部机器人"
          clearable
          :style="{ width: '160px' }"
          @update:value="getMinuteDataByPage(1)"
        />
        <NSelect
          v-model:value="searchParams.time_range"
          :options="TIME_RANGE_OPTIONS"
          :style="{ width: '140px' }"
          @update:value="getMinuteDataByPage(1)"
        />
        <NSelect
          v-model:value="searchParams.sort"
          :options="SORT_OPTIONS"
          :style="{ width: '130px' }"
          @update:value="getMinuteDataByPage(1)"
        />
        <NButton
          v-if="hasAuth('meeting:minutes:delete')"
          :type="trashMode ? 'primary' : 'default'"
          ghost
          @click="handleToggleTrash"
        >
          {{ trashMode ? '返回列表' : '回收站' }}
        </NButton>
        <NPopconfirm v-if="trashMode && hasAuth('meeting:minutes:delete')" @positive-click="handleClearTrash">
          <template #trigger>
            <NButton type="error" ghost>清空回收站</NButton>
          </template>
          确认彻底删除回收站中的全部会议纪要？该操作不可恢复。
        </NPopconfirm>
      </div>
      <TableHeaderOperation
        v-model:columns="minuteColumnChecks"
        :show-add="false"
        :show-delete="false"
        :loading="minuteLoading"
        @refresh="getMinuteData"
      />
    </div>

    <NCard :bordered="false" size="small" class="card-wrapper sm:flex-1-hidden">
      <NDataTable
        :columns="minuteColumns"
        :data="minuteData"
        size="small"
        :flex-height="!appStore.isMobile"
        :scroll-x="1460"
        :loading="minuteLoading"
        remote
        :row-key="row => row.id"
        :pagination="minuteMobilePagination"
        class="sm:h-full"
      />
    </NCard>

    <NDrawer v-model:show="detailVisible" :width="720" placement="right" resizable>
      <NDrawerContent :title="detail?.title || '会议纪要详情'" closable>
        <NSpin :show="detailLoading">
          <div v-if="detail" class="flex-col gap-16px">
            <NGrid :cols="24" :x-gap="12" :y-gap="12" item-responsive>
              <NGridItem span="24 m:12">
                <div class="text-12px text-gray-400">会议编号</div>
                <div class="text-14px">{{ detail.meeting_no }}</div>
              </NGridItem>
              <NGridItem span="24 m:12">
                <div class="text-12px text-gray-400">机器人</div>
                <div class="text-14px">{{ detail.robot_name || '-' }}</div>
              </NGridItem>
              <NGridItem span="24 m:12">
                <div class="text-12px text-gray-400">会议开始时间</div>
                <div class="text-14px">{{ detail.started_at }}</div>
              </NGridItem>
              <NGridItem span="24 m:12">
                <div class="text-12px text-gray-400">会议时长</div>
                <div class="text-14px">{{ formatDuration(detail.duration_seconds) }}</div>
              </NGridItem>
              <NGridItem span="24 m:12">
                <div class="text-12px text-gray-400">发言人数</div>
                <div class="text-14px">{{ detail.speaker_count }}</div>
              </NGridItem>
              <NGridItem span="24 m:12">
                <div class="text-12px text-gray-400">逐字稿片段</div>
                <div class="text-14px">{{ detail.segment_count }}</div>
              </NGridItem>
            </NGrid>

            <div v-if="detail.audio_url" class="flex-col gap-8px">
              <div class="text-14px font-medium">会议录音</div>
              <audio :src="detail.audio_url" controls class="w-full" />
            </div>

            <div v-if="detail.overview" class="rounded-8px bg-#f7f9fc p-16px dark:bg-#1f1f1f">
              <div class="mb-8px text-14px font-medium">会议总结</div>
              <div class="text-13px text-gray-600 leading-6 dark:text-gray-300">{{ detail.overview }}</div>
            </div>

            <div v-if="detail.conclusions?.length" class="flex-col gap-8px">
              <div class="text-14px font-medium">会议结论</div>
              <ul class="m-0 flex-col gap-6px pl-18px text-13px text-gray-600 leading-6 dark:text-gray-300">
                <li v-for="(item, index) in detail.conclusions" :key="index">{{ item }}</li>
              </ul>
            </div>

            <div v-if="detail.risks?.length" class="flex-col gap-8px">
              <div class="text-14px font-medium">风险与待办</div>
              <ul class="m-0 flex-col gap-6px pl-18px text-13px text-gray-600 leading-6 dark:text-gray-300">
                <li v-for="(item, index) in detail.risks" :key="index">{{ item }}</li>
              </ul>
            </div>

            <div class="flex-col gap-8px">
              <div class="text-14px font-medium">参会发言人</div>
              <div class="flex-y-center flex-wrap gap-8px">
                <NTag v-for="speaker in detail.speakers" :key="speaker.id" size="small" round>
                  {{ speaker.name }}
                  <span v-if="speaker.role" class="ml-4px text-gray-400">· {{ speaker.role }}</span>
                </NTag>
                <span v-if="!detail.speakers.length" class="text-13px text-gray-400">无</span>
              </div>
            </div>

            <div class="flex-col gap-8px">
              <div class="text-14px font-medium">逐字稿</div>
              <div class="max-h-420px overflow-auto border border-gray-200 rounded-8px p-12px dark:border-gray-700">
                <div
                  v-for="segment in detail.segments"
                  :key="segment.id"
                  class="flex-col gap-4px border-b border-gray-100 py-10px last:border-b-0 dark:border-gray-800"
                >
                  <div class="flex-y-center justify-between gap-8px">
                    <div class="flex-y-center flex-wrap gap-8px">
                      <span class="text-12px text-gray-400">{{ formatSegmentTime(segment) }}</span>
                      <NTag :type="segment.need_confirm ? 'warning' : 'default'" size="small">
                        {{ getSpeakerName(segment) }}
                      </NTag>
                      <span v-if="segment.confidence !== null" class="text-12px text-gray-400">
                        置信度 {{ segment.confidence }}%
                      </span>
                    </div>
                    <NSelect
                      v-if="hasAuth('meeting:minutes:edit')"
                      :value="segment.speaker_id"
                      :options="speakerOptions"
                      size="tiny"
                      placeholder="改派"
                      :style="{ width: '120px' }"
                      @update:value="value => handleReassign(segment, value as number)"
                    />
                  </div>
                  <div class="text-14px leading-6">{{ segment.text }}</div>
                </div>
                <div v-if="!detail.segments.length" class="py-20px text-center text-13px text-gray-400">暂无逐字稿</div>
              </div>
            </div>
          </div>
          <NEmpty v-else-if="!detailLoading" description="暂无数据" class="py-60px" />
        </NSpin>
      </NDrawerContent>
    </NDrawer>
  </div>
</template>

<style scoped></style>
