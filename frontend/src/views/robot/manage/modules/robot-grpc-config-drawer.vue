<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import type { FormRules } from 'naive-ui';
import { useNaiveForm } from '@/hooks/common/form';
import { $t } from '@/locales';
import { fetchGetRobot, fetchUpdateRobotGrpcConfig } from '@/service/api';

defineOptions({
  name: 'RobotGrpcConfigDrawer'
});

interface Props {
  robotId: number | null;
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

interface ServiceFormModel {
  host: string;
  port: number | null;
  enabled: boolean;
}

interface FormModel {
  agent: ServiceFormModel;
  middleware: ServiceFormModel;
}

function createDefaultService(): ServiceFormModel {
  return { host: '', port: null, enabled: false };
}

function createDefaultModel(): FormModel {
  return {
    agent: createDefaultService(),
    middleware: createDefaultService()
  };
}

const model = ref<FormModel>(createDefaultModel());
const loading = ref(false);

const title = computed(() => 'gRPC 配置');

const rules: FormRules = {
  'agent.host': [{ required: true, message: '请输入 agent 服务地址', trigger: 'blur' }],
  'agent.port': [{ required: true, type: 'number', message: '请输入 agent 服务端口', trigger: 'blur' }],
  'middleware.host': [{ required: true, message: '请输入 middleware 服务地址', trigger: 'blur' }],
  'middleware.port': [{ required: true, type: 'number', message: '请输入 middleware 服务端口', trigger: 'blur' }]
};

async function loadRobot(robotId: number) {
  loading.value = true;
  try {
    const { data, error } = await fetchGetRobot(robotId);
    if (error || !data) {
      model.value = createDefaultModel();
      return;
    }
    const cfg = data.grpc_config || {};
    const a = cfg.agent;
    const m = cfg.middleware;
    model.value = {
      agent: {
        host: a?.host ?? '',
        port: a?.port ?? null,
        enabled: a?.enabled ?? false
      },
      middleware: {
        host: m?.host ?? '',
        port: m?.port ?? null,
        enabled: m?.enabled ?? false
      }
    };
  } finally {
    loading.value = false;
  }
}

function closeDrawer() {
  visible.value = false;
}

async function handleSubmit() {
  await validate();

  if (props.robotId === null) {
    window.$message?.warning('机器人 ID 缺失');
    return;
  }

  const payload: Api.Robot.RobotGrpcConfig = {
    agent: {
      host: model.value.agent.host,
      port: Number(model.value.agent.port),
      enabled: model.value.agent.enabled
    },
    middleware: {
      host: model.value.middleware.host,
      port: Number(model.value.middleware.port),
      enabled: model.value.middleware.enabled
    }
  };

  const { error } = await fetchUpdateRobotGrpcConfig(props.robotId, payload);
  if (!error) {
    window.$message?.success($t('common.updateSuccess'));
    closeDrawer();
    emit('submitted');
  }
}

watch(visible, val => {
  if (val) {
    if (props.robotId !== null) {
      loadRobot(props.robotId);
    } else {
      model.value = createDefaultModel();
    }
    restoreValidation();
  }
});
</script>

<template>
  <NDrawer v-model:show="visible" display-directive="show" :width="520">
    <NDrawerContent :title="title" :native-scrollbar="false" closable>
      <NSpin :show="loading">
        <NForm ref="formRef" :model="model" :rules="rules" label-placement="top">
          <NDivider title-placement="left">Agent</NDivider>
          <NFormItem label="服务地址" path="agent.host">
            <NInput v-model:value="model.agent.host" placeholder="例如 127.0.0.1" />
          </NFormItem>
          <NFormItem label="服务端口" path="agent.port">
            <NInputNumber
              v-model:value="model.agent.port"
              placeholder="例如 50051"
              :min="1"
              :max="65535"
              class="w-full"
            />
          </NFormItem>
          <NFormItem label="启用">
            <NSwitch v-model:value="model.agent.enabled" />
          </NFormItem>

          <NDivider title-placement="left">Middleware</NDivider>
          <NFormItem label="服务地址" path="middleware.host">
            <NInput v-model:value="model.middleware.host" placeholder="例如 127.0.0.1" />
          </NFormItem>
          <NFormItem label="服务端口" path="middleware.port">
            <NInputNumber
              v-model:value="model.middleware.port"
              placeholder="例如 50052"
              :min="1"
              :max="65535"
              class="w-full"
            />
          </NFormItem>
          <NFormItem label="启用">
            <NSwitch v-model:value="model.middleware.enabled" />
          </NFormItem>
        </NForm>
      </NSpin>
      <template #footer>
        <NSpace :size="16">
          <NButton @click="closeDrawer">{{ $t('common.cancel') }}</NButton>
          <NButton type="primary" @click="handleSubmit">{{ $t('common.confirm') }}</NButton>
        </NSpace>
      </template>
    </NDrawerContent>
  </NDrawer>
</template>

<style scoped></style>
