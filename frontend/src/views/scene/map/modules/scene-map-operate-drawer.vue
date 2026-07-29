<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import type { FormRules, UploadCustomRequestOptions, UploadFileInfo } from 'naive-ui';
import { jsonClone } from '@sa/utils';
import { fetchCreateSceneMap, fetchUpdateSceneMap, fetchUploadSceneMapImage, getFilePreviewUrl } from '@/service/api';
import { useNaiveForm } from '@/hooks/common/form';

defineOptions({
  name: 'SceneMapOperateDrawer'
});

interface Props {
  operateType: NaiveUI.TableOperateType;
  rowData?: Api.Scene.SceneMap | null;
}

const props = defineProps<Props>();

interface Emits {
  (e: 'submitted'): void;
}

const emit = defineEmits<Emits>();

const visible = defineModel<boolean>('visible', {
  default: false
});

const { formRef, validate, restoreValidation } = useNaiveForm();

const title = computed(() => {
  const titles: Record<NaiveUI.TableOperateType, string> = {
    add: '新增场景地图',
    edit: '编辑场景地图'
  };
  return titles[props.operateType];
});

interface MapModel {
  name: string;
  image_id: number | null;
  width: number | null;
  height: number | null;
  resolution: number | null;
  start_point_x: number;
  start_point_y: number;
}

const model = ref<MapModel>(createDefaultModel());

function createDefaultModel(): MapModel {
  return {
    name: '',
    image_id: null,
    width: null,
    height: null,
    resolution: 1,
    start_point_x: 0,
    start_point_y: 0
  };
}

const rules: FormRules = {
  name: { required: true, message: '请输入地图名称', trigger: 'blur' },
  image_id: { required: true, type: 'number', message: '请上传地图图片', trigger: 'change' },
  width: { required: true, type: 'number', message: '请上传地图图片以获取宽度', trigger: 'change' },
  height: { required: true, type: 'number', message: '请上传地图图片以获取高度', trigger: 'change' },
  resolution: { required: true, type: 'number', message: '请输入映射比例', trigger: 'blur' },
  start_point_x: { required: true, type: 'number', message: '请输入扫图起始点X坐标', trigger: 'blur' },
  start_point_y: { required: true, type: 'number', message: '请输入扫图起始点Y坐标', trigger: 'blur' }
};

/** 图片上传 */
const uploading = ref(false);
const imageUrl = ref('');
const uploadFileList = ref<UploadFileInfo[]>([]);

async function handleUpload({ file }: UploadCustomRequestOptions) {
  if (!file.file) return;
  uploading.value = true;
  try {
    const { data, error } = await fetchUploadSceneMapImage(file.file, { includeImageInfo: true });
    if (!error && data) {
      model.value.image_id = data.id;
      imageUrl.value = getFilePreviewUrl(data.id);
      if (data.image_width != null && data.image_height != null) {
        model.value.width = data.image_width;
        model.value.height = data.image_height;
      }
      window.$message?.success('图片上传成功');
    }
  } finally {
    uploading.value = false;
    uploadFileList.value = [];
  }
}

function handleRemoveImage() {
  model.value.image_id = null;
  imageUrl.value = '';
}

const mapId = computed(() => props.rowData?.id || -1);
const isEdit = computed(() => props.operateType === 'edit');

function handleInitModel() {
  model.value = createDefaultModel();
  imageUrl.value = '';

  if (props.operateType === 'edit' && props.rowData) {
    const clonedData = jsonClone(props.rowData);
    model.value.name = clonedData.name || '';
    model.value.image_id = clonedData.image_id ?? null;
    model.value.width = clonedData.width ?? null;
    model.value.height = clonedData.height ?? null;
    model.value.resolution = clonedData.resolution ?? 1;
    model.value.start_point_x = clonedData.start_point_x ?? 0;
    model.value.start_point_y = clonedData.start_point_y ?? 0;
    if (clonedData.image_id) {
      imageUrl.value = getFilePreviewUrl(clonedData.image_id);
    }
  }
}

function closeDrawer() {
  visible.value = false;
}

async function handleSubmit() {
  await validate();

  const submitData: Api.Scene.SceneMapCreate = {
    name: model.value.name,
    image_id: model.value.image_id as number,
    width: model.value.width as number,
    height: model.value.height as number,
    resolution: model.value.resolution as number,
    start_point_x: model.value.start_point_x,
    start_point_y: model.value.start_point_y
  };

  let error: unknown = null;

  if (isEdit.value) {
    const updateData: Api.Scene.SceneMapUpdate = {
      name: submitData.name,
      image_id: submitData.image_id,
      width: submitData.width,
      height: submitData.height,
      resolution: submitData.resolution,
      start_point_x: submitData.start_point_x,
      start_point_y: submitData.start_point_y
    };
    const result = await fetchUpdateSceneMap(mapId.value, updateData);
    error = result.error;
  } else {
    const result = await fetchCreateSceneMap(submitData);
    error = result.error;
  }

  if (!error) {
    window.$message?.success(isEdit.value ? '修改成功' : '新增成功');
    closeDrawer();
    emit('submitted');
  }
}

watch(visible, () => {
  if (visible.value) {
    handleInitModel();
    restoreValidation();
  }
});
</script>

<template>
  <NDrawer v-model:show="visible" display-directive="show" :width="560">
    <NDrawerContent :title="title" :native-scrollbar="false" closable>
      <NForm ref="formRef" :model="model" :rules="rules">
        <NFormItem label="地图名称" path="name">
          <NInput v-model:value="model.name" placeholder="请输入地图名称" maxlength="200" show-count />
        </NFormItem>
        <NFormItem label="地图图片" path="image_id">
          <div class="w-full">
            <NUpload
              v-model:file-list="uploadFileList"
              :max="1"
              accept="image/*"
              :custom-request="handleUpload"
              :show-file-list="false"
            >
              <NButton :loading="uploading" ghost>
                <template #icon>
                  <icon-ic-round-upload class="text-icon" />
                </template>
                {{ uploading ? '上传中...' : '选择图片' }}
              </NButton>
            </NUpload>
            <div v-if="imageUrl" class="mt-8px flex items-center gap-8px">
              <NImage :src="imageUrl" width="120" object-fit="contain" />
              <NButton text type="error" @click="handleRemoveImage">移除</NButton>
            </div>
          </div>
        </NFormItem>
        <NFormItem v-show="false" label="宽度" path="width">
          <NInputNumber v-model:value="model.width" placeholder="请输入地图宽度" :min="0" class="w-full" />
        </NFormItem>
        <NFormItem v-show="false" label="高度" path="height">
          <NInputNumber v-model:value="model.height" placeholder="请输入地图高度" :min="0" class="w-full" />
        </NFormItem>
        <NFormItem label="映射比例" path="resolution">
          <NInputNumber
            v-model:value="model.resolution"
            placeholder="请输入映射比例"
            :min="0"
            :precision="6"
            clearable
            class="w-full"
          />
        </NFormItem>
        <NFormItem label="扫图起始点X" path="start_point_x">
          <NInputNumber
            v-model:value="model.start_point_x"
            placeholder="请输入扫图起始点X坐标"
            clearable
            class="w-full"
          />
        </NFormItem>
        <NFormItem label="扫图起始点Y" path="start_point_y">
          <NInputNumber
            v-model:value="model.start_point_y"
            placeholder="请输入扫图起始点Y坐标"
            clearable
            class="w-full"
          />
        </NFormItem>
      </NForm>
      <template #footer>
        <NSpace :size="16">
          <NButton @click="closeDrawer">取消</NButton>
          <NButton type="primary" @click="handleSubmit">确认</NButton>
        </NSpace>
      </template>
    </NDrawerContent>
  </NDrawer>
</template>

<style scoped></style>
