<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue';
import type { UploadCustomRequestOptions } from 'naive-ui';
import { fetchDeletePerformanceMusic, fetchGetPerformanceMusic, fetchUploadPerformanceMusic } from '@/service/api';
import { getFilePreviewUrl } from '@/service/api/file';

defineOptions({ name: 'PerformanceMusicSelect' });

interface Props {
  value: string | null;
}

const props = defineProps<Props>();

const emit = defineEmits<{
  (e: 'update:value', value: string | null): void;
}>();

/** 用户上传音乐的标识前缀（与后端 UPLOAD_MUSIC_PREFIX 一致）：upload:<sys_file_id> */
const UPLOAD_MUSIC_PREFIX = 'upload:';
/** 上传音频大小上限（与后端一致，20MB） */
const UPLOAD_MUSIC_MAX_SIZE = 20 * 1024 * 1024;

const showModal = ref(false);
const loading = ref(false);
const uploading = ref(false);
const options = ref<Api.Task.PerformanceMusicOption[]>([]);

const presetOptions = computed(() => options.value.filter(o => !isUploadMusic(o.value)));
const uploadOptions = computed(() => options.value.filter(o => isUploadMusic(o.value)));
const selectedOption = computed(() => options.value.find(o => o.value === props.value));
const displayLabel = computed(() => selectedOption.value?.label ?? props.value ?? '点击选择背景音乐');

function isUploadMusic(value: string): boolean {
  return value.startsWith(UPLOAD_MUSIC_PREFIX);
}

function parseFileId(value: string): number {
  return Number(value.slice(UPLOAD_MUSIC_PREFIX.length));
}

function formatDuration(seconds?: number | null): string {
  if (seconds === null || seconds === undefined) return '--:--';
  const m = Math.floor(seconds / 60);
  const s = Math.round(seconds % 60);
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
}

async function loadOptions() {
  loading.value = true;
  try {
    const { data, error } = await fetchGetPerformanceMusic();
    if (!error && data) {
      options.value = data;
    }
  } finally {
    loading.value = false;
  }
}

// ---------- 试听（file_id 非空即可试听：用户上传为自身文件，预设为映射的服务端文件） ----------

const playingValue = ref<string | null>(null);
let audio: HTMLAudioElement | null = null;

function stopPlay() {
  audio?.pause();
  audio = null;
  playingValue.value = null;
}

function togglePlay(item: Api.Task.PerformanceMusicOption) {
  if (!item.file_id) return;
  if (playingValue.value === item.value) {
    stopPlay();
    return;
  }
  stopPlay();
  audio = new Audio(getFilePreviewUrl(item.file_id));
  audio.onended = () => {
    playingValue.value = null;
  };
  audio.onerror = () => {
    playingValue.value = null;
    window.$message?.error('音频加载失败');
  };
  audio.play();
  playingValue.value = item.value;
}

// ---------- 选择 / 上传 / 删除 ----------

function handleSelect(item: Api.Task.PerformanceMusicOption) {
  stopPlay();
  emit('update:value', item.value);
  showModal.value = false;
}

async function handleUpload({ file, onFinish, onError }: UploadCustomRequestOptions) {
  // 无论成功失败都必须调用 onFinish/onError 收尾，否则文件会留在 NUpload 内部队列被重复提交
  if (!file.file) {
    onError();
    return;
  }
  if (!/\.(mp3|wav)$/i.test(file.name)) {
    window.$message?.warning('仅支持 mp3/wav 格式的音频文件');
    onError();
    return;
  }
  if (file.file.size > UPLOAD_MUSIC_MAX_SIZE) {
    window.$message?.warning('音频文件不能超过 20MB');
    onError();
    return;
  }
  uploading.value = true;
  try {
    const { data, error } = await fetchUploadPerformanceMusic(file.file);
    if (error || !data) {
      onError();
      return;
    }
    await loadOptions();
    // 上传仅加入列表，不自动切换当前已选音乐（用户可能已选好其他曲目）
    if (data.truncated) {
      window.$message?.warning('上传成功：音频超过 5 分钟，已自动截取前 5 分钟');
    } else {
      window.$message?.success('上传成功，可在列表中试听并选择');
    }
    onFinish();
  } finally {
    uploading.value = false;
  }
}

async function handleDelete(item: Api.Task.PerformanceMusicOption) {
  const { error } = await fetchDeletePerformanceMusic(parseFileId(item.value));
  if (error) return;
  if (playingValue.value === item.value) stopPlay();
  options.value = options.value.filter(o => o.value !== item.value);
  if (props.value === item.value) {
    emit('update:value', null);
  }
  window.$message?.success('删除成功');
}

/** 删除当前已选中的上传音乐（字段上的删除按钮入口） */
async function handleDeleteSelected() {
  if (selectedOption.value && isUploadMusic(selectedOption.value.value)) {
    await handleDelete(selectedOption.value);
  }
}

onMounted(loadOptions);
watch(showModal, visible => {
  if (visible) {
    loadOptions();
  } else {
    stopPlay();
  }
});
onBeforeUnmount(stopPlay);
</script>

<template>
  <div class="w-full">
    <div class="flex items-center gap-6px">
      <!-- 与两侧的 NSelect/NInputNumber 保持居左对齐 -->
      <NButton class="flex-1" style="justify-content: flex-start" @click="showModal = true">
        <template #icon>
          <icon-ic-round-music-note class="text-icon" />
        </template>
        <span class="flex-1 truncate text-left" :class="{ 'text-#999': !selectedOption }">{{ displayLabel }}</span>
      </NButton>
      <!-- 清除已选（背景音乐为非必填项） -->
      <NTooltip v-if="value">
        <template #trigger>
          <NButton quaternary circle size="small" @click="emit('update:value', null)">
            <template #icon>
              <icon-ic-round-close class="text-icon" />
            </template>
          </NButton>
        </template>
        清除背景音乐
      </NTooltip>
      <!-- 已选为自己上传的音乐时，提供删除入口 -->
      <NPopconfirm v-if="value && isUploadMusic(value)" @positive-click="handleDeleteSelected">
        <template #trigger>
          <NButton quaternary circle size="small" type="error">
            <template #icon>
              <icon-ic-round-delete-outline class="text-icon" />
            </template>
          </NButton>
        </template>
        删除该上传音乐？已被任务引用的音乐无法删除。
      </NPopconfirm>
    </div>

    <NModal v-model:show="showModal" preset="card" title="选择背景音乐" style="width: 560px">
      <div class="mb-12px text-12px text-#999 leading-18px">
        支持系统预设曲目或上传本地音频（mp3/wav，单个不超过 20MB）；超过 5 分钟的音频将自动截取前 5
        分钟，时长以列表显示为准。点击左侧播放按钮可试听。
      </div>

      <div class="mb-12px">
        <NUpload :show-file-list="false" accept=".mp3,.wav,audio/mpeg,audio/wav,audio/x-wav" :custom-request="handleUpload">
          <NButton type="primary" secondary size="small" :loading="uploading">
            <template #icon>
              <icon-ic-round-upload class="text-icon" />
            </template>
            上传本地音乐
          </NButton>
        </NUpload>
      </div>

      <NSpin :show="loading">
        <div class="max-h-360px overflow-y-auto">
          <div class="music-group-title">预设音乐</div>
          <div
            v-for="item in presetOptions"
            :key="item.value"
            class="music-row"
            :class="{ 'music-row-active': item.value === value }"
            @click="handleSelect(item)"
          >
            <NTooltip :disabled="!!item.file_id">
              <template #trigger>
                <NButton quaternary circle size="small" :disabled="!item.file_id" @click.stop="togglePlay(item)">
                  <template #icon>
                    <icon-ic-round-pause v-if="playingValue === item.value" class="text-icon text-primary" />
                    <icon-ic-round-play-arrow v-else class="text-icon" />
                  </template>
                </NButton>
              </template>
              该预设曲目服务端暂无音频文件，暂不支持试听
            </NTooltip>
            <span class="flex-1 truncate">{{ item.label }}</span>
            <span class="music-duration">{{ formatDuration(item.duration_seconds) }}</span>
            <icon-ic-round-check-circle v-if="item.value === value" class="text-18px text-primary" />
          </div>

          <div class="music-group-title mt-12px">我上传的音乐</div>
          <div v-if="!uploadOptions.length" class="py-12px text-center text-12px text-#999">暂无上传的音乐</div>
          <div
            v-for="item in uploadOptions"
            :key="item.value"
            class="music-row"
            :class="{ 'music-row-active': item.value === value }"
            @click="handleSelect(item)"
          >
            <NButton quaternary circle size="small" @click.stop="togglePlay(item)">
              <template #icon>
                <icon-ic-round-pause v-if="playingValue === item.value" class="text-icon text-primary" />
                <icon-ic-round-play-arrow v-else class="text-icon" />
              </template>
            </NButton>
            <span class="flex-1 truncate">{{ item.label }}</span>
            <span class="music-duration">{{ formatDuration(item.duration_seconds) }}</span>
            <NPopconfirm @positive-click="handleDelete(item)">
              <template #trigger>
                <NButton quaternary circle size="small" type="error" @click.stop>
                  <template #icon>
                    <icon-ic-round-delete-outline class="text-icon" />
                  </template>
                </NButton>
              </template>
              删除该上传音乐？已被任务引用的音乐无法删除。
            </NPopconfirm>
            <icon-ic-round-check-circle v-if="item.value === value" class="text-18px text-primary" />
          </div>
        </div>
      </NSpin>
    </NModal>
  </div>
</template>

<style scoped>
.music-group-title {
  font-size: 13px;
  font-weight: 600;
  color: #666;
  margin-bottom: 4px;
}

.music-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 8px;
  border-radius: 6px;
  cursor: pointer;
}

.music-row:hover {
  background-color: rgba(0, 0, 0, 0.04);
}

.music-row-active {
  background-color: rgba(24, 160, 88, 0.08);
}

.music-duration {
  font-size: 12px;
  color: #999;
  font-variant-numeric: tabular-nums;
}
</style>
