<script setup lang="tsx">
import { nextTick, onMounted, reactive, ref } from 'vue';
import {
  NButton,
  NCard,
  NDataTable,
  NForm,
  NFormItem,
  NInput,
  NModal,
  NPopconfirm,
  NSpace,
  NUpload,
  type UploadFileInfo,
  useMessage
} from 'naive-ui';
import {
  fetchCreateFaceRecognition,
  fetchDeleteFaceRecognition,
  fetchGetFaceRecognitionList,
  fetchUpdateFaceRecognition,
  fetchUploadFacePhoto,
  getPersistentFilePreviewPath,
  resolveFilePreviewUrl
} from '@/service/api';
import { useAppStore } from '@/store/modules/app';
import { useNaiveForm } from '@/hooks/common/form';
import { useAuth } from '@/hooks/business/auth';
import SvgIcon from '@/components/custom/svg-icon.vue';

defineOptions({ name: 'FaceRecognitionTab' });

/** 人像上传限制（对齐阿里云 facebody 要求；人脸占比 64×64 由 facebody 校验） */
const ALLOWED_FACE_PHOTO_EXTS = ['jpg', 'jpeg', 'png'];
const MAX_FACE_PHOTO_SIZE = 5 * 1024 * 1024; // 5MB
const MIN_FACE_PHOTO_DIM = 32; // 分辨率下限（>32）
const MAX_FACE_PHOTO_DIM = 4096; // 分辨率上限（<4096）

const { hasAuth } = useAuth();
const message = useMessage();
const appStore = useAppStore();
const { formRef, validate, restoreValidation } = useNaiveForm();

const loading = ref(false);
const tableLoading = ref(false);
const editingId = ref<number | null>(null);
const isFormExpanded = ref(true);
const formAnchorRef = ref<HTMLElement | null>(null);

const model = reactive<Api.RobotConfig.FaceRecognitionCreate>({
  person_name: '',
  photo_url: '',
  broadcast_text: ''
});

const fileList = ref<UploadFileInfo[]>([]);

const faceList = ref<Api.RobotConfig.FaceRecognition[]>([]);

const previewVisible = ref(false);
const previewUrl = ref('');

function openPreview(url: string) {
  previewUrl.value = url;
  previewVisible.value = true;
}

const rules = {
  person_name: [{ required: true, message: '请输入人员名称', trigger: 'blur' }],
  photo_url: [{ required: true, message: '请上传人像', trigger: 'change' }],
  broadcast_text: [{ required: true, message: '请输入语音播报内容', trigger: 'blur' }]
};

async function loadData() {
  tableLoading.value = true;
  try {
    const { data, error } = await fetchGetFaceRecognitionList({ page: 1, page_size: 100 });
    if (!error && data) {
      faceList.value = data.records || [];
    }
  } catch (err) {
    console.error('加载人脸识别TTS列表失败:', err);
  } finally {
    tableLoading.value = false;
  }
}

/** 读取图片宽高，失败返回 null */
function getImageSize(file: File): Promise<{ width: number; height: number } | null> {
  return new Promise(resolve => {
    const url = URL.createObjectURL(file);
    const img = new Image();
    img.onload = () => {
      const result = { width: img.width, height: img.height };
      URL.revokeObjectURL(url);
      resolve(result);
    };
    img.onerror = () => {
      URL.revokeObjectURL(url);
      resolve(null);
    };
    img.src = url;
  });
}

async function handleUpload({ file }: { file: UploadFileInfo }) {
  if (!file.file) return;
  const raw = file.file;
  const ext = raw.name.split('.').pop()?.toLowerCase() || '';
  if (!ALLOWED_FACE_PHOTO_EXTS.includes(ext)) {
    message.error('图像格式仅支持 JPG、JPEG、PNG');
    fileList.value = [];
    return;
  }
  if (raw.size > MAX_FACE_PHOTO_SIZE) {
    message.error('图像大小不能超过 5MB');
    fileList.value = [];
    return;
  }
  const dim = await getImageSize(raw);
  if (!dim) {
    message.error('无法读取图片，请确认文件未损坏');
    fileList.value = [];
    return;
  }
  if (dim.width <= MIN_FACE_PHOTO_DIM || dim.height <= MIN_FACE_PHOTO_DIM) {
    message.error(`图像分辨率需大于 32×32 像素，当前 ${dim.width}×${dim.height}`);
    fileList.value = [];
    return;
  }
  if (dim.width >= MAX_FACE_PHOTO_DIM || dim.height >= MAX_FACE_PHOTO_DIM) {
    message.error(`图像分辨率需小于 4096×4096 像素，当前 ${dim.width}×${dim.height}`);
    fileList.value = [];
    return;
  }
  try {
    const { data, error } = await fetchUploadFacePhoto(raw);
    if (!error && data) {
      model.photo_url = getPersistentFilePreviewPath(data.id);
      message.success('上传成功');
    }
  } catch (err) {
    message.error('上传失败');
    console.error('上传人像失败:', err);
  }
}

function handleRemovePhoto() {
  model.photo_url = '';
  return true;
}

async function handleSave() {
  try {
    await validate();
    loading.value = true;
    if (editingId.value) {
      const { error } = await fetchUpdateFaceRecognition(editingId.value, { ...model });
      if (!error) {
        message.success('更新成功');
        resetForm();
        await loadData();
      }
    } else {
      const { error } = await fetchCreateFaceRecognition({ ...model });
      if (!error) {
        message.success('保存成功');
        resetForm();
        await loadData();
      }
    }
  } catch (err) {
    console.error('保存人脸识别配置失败:', err);
  } finally {
    loading.value = false;
  }
}

function handleEdit(row: Api.RobotConfig.FaceRecognition) {
  editingId.value = row.id;
  model.person_name = row.person_name;
  model.photo_url = row.photo_url;
  model.broadcast_text = row.broadcast_text;
  fileList.value = [];
  isFormExpanded.value = true;
  restoreValidation();
  // 编辑表单位于列表上方，点击后滚动到表单，避免「点了没反应」的错觉
  nextTick(() => {
    formAnchorRef.value?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  });
}

async function handleDelete(id: number) {
  try {
    const { error } = await fetchDeleteFaceRecognition(id);
    if (!error) {
      message.success('删除成功');
      await loadData();
    }
  } catch (err) {
    console.error('删除人脸识别配置失败:', err);
  }
}

function resetForm() {
  editingId.value = null;
  model.person_name = '';
  model.photo_url = '';
  model.broadcast_text = '';
  fileList.value = [];
  formRef.value?.restoreValidation();
}

const columns = [
  { key: 'index', title: '序号', align: 'center' as const, width: 64, render: (_: any, index: number) => index + 1 },
  { key: 'person_name', title: '人员名称', align: 'center' as const, width: 300 },
  {
    key: 'photo_url',
    title: '人像',
    align: 'center' as const,
    width: 100,
    render: (row: Api.RobotConfig.FaceRecognition) => {
      const url = resolveFilePreviewUrl(row.photo_url);
      return (
        <img
          src={url}
          class="h-48px w-48px cursor-pointer rounded object-cover"
          alt="人像"
          onClick={() => openPreview(url)}
        />
      );
    }
  },
  { key: 'broadcast_text', title: '播报内容', align: 'center' as const, minWidth: 200, ellipsis: { tooltip: true } },
  {
    key: 'entity_id',
    title: '实体ID',
    align: 'center' as const,
    width: 120,
    ellipsis: { tooltip: true },
    render: (row: Api.RobotConfig.FaceRecognition) => row.entity_id || '-'
  },
  {
    key: 'operate',
    title: '操作',
    align: 'center' as const,
    width: 160,
    render: (row: Api.RobotConfig.FaceRecognition) => (
      <div class="flex-center gap-8px">
        {hasAuth('robot:config:edit') && (
          <NButton type="primary" ghost size="small" onClick={() => handleEdit(row)}>
            编辑
          </NButton>
        )}
        {hasAuth('robot:config:edit') && (
          <NPopconfirm onPositiveClick={() => handleDelete(row.id)}>
            {{
              default: () => '确认删除吗？',
              trigger: () => (
                <NButton type="error" ghost size="small">
                  删除
                </NButton>
              )
            }}
          </NPopconfirm>
        )}
      </div>
    )
  }
];

onMounted(() => {
  loadData();
});
</script>

<template>
  <div class="flex-col gap-16px">
    <!-- 配置表单 -->
    <div ref="formAnchorRef">
      <NCard :title="editingId ? '编辑人脸识别TTS' : '配置人脸识别TTS'" size="small">
        <NForm ref="formRef" :model="model" :rules="rules" label-placement="left" :label-width="100">
          <NGrid responsive="screen" :cols="1">
            <template v-if="isFormExpanded">
              <NFormItemGi label="人员名称" path="person_name">
                <NInput v-model:value="model.person_name" placeholder="请输入人员名称" clearable />
              </NFormItemGi>
              <!-- 编辑模式：人像只读不可修改，仅可改名称与播报文字 -->
              <NFormItemGi v-if="editingId" label="人像">
                <div class="flex items-center gap-8px">
                  <img
                    :src="resolveFilePreviewUrl(model.photo_url)"
                    class="h-48px w-48px rounded object-cover"
                    alt="人像"
                  />
                  <span class="text-12px text-gray">编辑时不支持修改人像</span>
                </div>
              </NFormItemGi>
              <!-- 新建模式：上传人像 -->
              <NFormItemGi v-else label="人像" path="photo_url">
                <div class="face-upload-wrap">
                  <div class="face-upload-left">
                    <NUpload
                      v-if="hasAuth('robot:config:edit')"
                      v-model:file-list="fileList"
                      :max="1"
                      accept=".jpg,.jpeg,.png,image/jpeg,image/png"
                      :custom-request="handleUpload"
                      :on-remove="handleRemovePhoto"
                      list-type="image-card"
                    />
                    <span v-if="model.photo_url && !fileList.length" class="text-12px text-gray">
                      已上传: {{ model.photo_url }}
                    </span>
                  </div>
                  <div class="face-upload-tips">
                    <div>图像格式：JPG、JPEG、PNG</div>
                    <div>图像大小：不超过 5 MB</div>
                    <div>图像分辨率：大于 32×32 像素，小于 4096×4096 像素</div>
                    <div>人脸占比：不低于 64×64 像素</div>
                    <div>图片中若包含多个人脸，会取最大的人脸进行添加</div>
                  </div>
                </div>
              </NFormItemGi>
              <NFormItemGi label="播报内容" path="broadcast_text">
                <NInput
                  v-model:value="model.broadcast_text"
                  type="textarea"
                  placeholder="请输入语音播报内容"
                  :rows="3"
                  clearable
                />
              </NFormItemGi>
            </template>
            <NFormItemGi>
              <div class="w-full flex-center justify-between">
                <NSpace>
                  <NButton
                    v-if="hasAuth('robot:config:edit')"
                    type="primary"
                    :loading="loading"
                    :disabled="!isFormExpanded"
                    @click="handleSave"
                  >
                    {{ editingId ? '更新配置' : '保存配置' }}
                  </NButton>
                  <NButton v-if="editingId" @click="resetForm">取消</NButton>
                </NSpace>
                <NButton text @click="isFormExpanded = !isFormExpanded">
                  <template #icon>
                    <SvgIcon :icon="isFormExpanded ? 'mdi:chevron-up' : 'mdi:chevron-down'" />
                  </template>
                  <span class="ml-4px">{{ isFormExpanded ? '收起' : '展开' }}</span>
                </NButton>
              </div>
            </NFormItemGi>
          </NGrid>
        </NForm>
      </NCard>
    </div>

    <!-- 已配置列表 -->
    <NCard title="已配置人员列表" size="small">
      <NDataTable
        :columns="columns"
        :data="faceList"
        size="small"
        :loading="tableLoading"
        :row-key="row => row.id"
        :scroll-x="720"
        class="sm:h-full"
      />
    </NCard>

    <NModal v-model:show="previewVisible" preset="card" title="人像预览" class="max-w-700px">
      <img :src="previewUrl" class="max-h-70vh w-full object-contain" alt="人像预览" />
    </NModal>
  </div>
</template>

<style scoped>
.face-upload-wrap {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  width: 100%;
}
.face-upload-left {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}
.face-upload-tips {
  font-size: 12px;
  color: #999;
  line-height: 1.8;
}
@media (max-width: 768px) {
  .face-upload-wrap {
    flex-direction: column;
  }
}
.h-48px {
  height: 48px;
}
.w-48px {
  width: 48px;
}
.rounded {
  border-radius: 4px;
}
.object-cover {
  object-fit: cover;
}
.text-12px {
  font-size: 12px;
}
.text-gray {
  color: #999;
}
.flex-center {
  display: flex;
  align-items: center;
}
.justify-between {
  justify-content: space-between;
}
.w-full {
  width: 100%;
}
.ml-4px {
  margin-left: 4px;
}
</style>
