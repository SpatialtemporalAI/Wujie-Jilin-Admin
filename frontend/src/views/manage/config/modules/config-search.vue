<script setup lang="tsx">
import { useVModel } from '@vueuse/core';
import { NButton, NForm, NFormItem, NGrid, NGridItem, NInput, NSelect } from 'naive-ui';
import { yesOrNoOptions } from '@/constants/business';
import { $t } from '@/locales';

interface Props {
  model: Api.SystemManage.ConfigSearchParams;
}

const props = defineProps<Props>();
const emit = defineEmits<{
  search: [];
  reset: [];
}>();

const model = useVModel(props, 'model');

/** 配置类型选项 */
const configTypeOptions = [
  { label: $t('page.manage.config.type.string'), value: 'string' },
  { label: $t('page.manage.config.type.number'), value: 'number' },
  { label: $t('page.manage.config.type.boolean'), value: 'boolean' },
  { label: $t('page.manage.config.type.json'), value: 'json' },
  { label: $t('page.manage.config.type.array'), value: 'array' }
];

/** 配置分组选项 */
const configGroupOptions = [
  { label: $t('page.manage.config.group.system'), value: 'system' },
  { label: $t('page.manage.config.group.security'), value: 'security' },
  { label: $t('page.manage.config.group.log'), value: 'log' },
  { label: $t('page.manage.config.group.network'), value: 'network' },
  { label: $t('page.manage.config.group.storage'), value: 'storage' },
  { label: $t('page.manage.config.group.custom'), value: 'custom' }
];

function handleSearch() {
  emit('search');
}

function handleReset() {
  model.value = {
    page: 1,
    page_size: 10,
    key: null,
    description: null,
    type: null,
    group: null,
    editable: null,
    is_system: null
  };
  emit('reset');
}
</script>

<template>
  <NCard :bordered="false" size="small" class="card-wrapper">
    <NForm :model="model" label-placement="left" label-width="auto" size="small">
      <NGrid :x-gap="16" :cols="24">
        <NGridItem :xs="24" :sm="12" :md="8" :lg="6" :xl="4">
          <NFormItem :label="$t('page.manage.config.configKey')">
            <NInput v-model:value="model.key" :placeholder="$t('common.keywordSearch')" clearable />
          </NFormItem>
        </NGridItem>
        <NGridItem :xs="24" :sm="12" :md="8" :lg="6" :xl="4">
          <NFormItem :label="$t('page.manage.config.configDesc')">
            <NInput v-model:value="model.description" :placeholder="$t('common.keywordSearch')" clearable />
          </NFormItem>
        </NGridItem>
        <NGridItem :xs="24" :sm="12" :md="8" :lg="6" :xl="4">
          <NFormItem :label="$t('page.manage.config.configType')">
            <NSelect v-model:value="model.type" :options="configTypeOptions" :placeholder="$t('common.keywordSearch')" clearable />
          </NFormItem>
        </NGridItem>
        <NGridItem :xs="24" :sm="12" :md="8" :lg="6" :xl="4">
          <NFormItem :label="$t('page.manage.config.configGroup')">
            <NSelect v-model:value="model.group" :options="configGroupOptions" :placeholder="$t('common.keywordSearch')" clearable />
          </NFormItem>
        </NGridItem>
        <NGridItem :xs="24" :sm="12" :md="8" :lg="6" :xl="4">
          <NFormItem :label="$t('page.manage.config.editable')">
            <NSelect v-model:value="model.editable" :options="yesOrNoOptions" :placeholder="$t('common.keywordSearch')" clearable />
          </NFormItem>
        </NGridItem>
        <NGridItem :xs="24" :sm="12" :md="8" :lg="6" :xl="4">
          <NFormItem :label="$t('page.manage.config.isSystem')">
            <NSelect v-model:value="model.is_system" :options="yesOrNoOptions" :placeholder="$t('common.keywordSearch')" clearable />
          </NFormItem>
        </NGridItem>
        <NGridItem :xs="24" :sm="12" :md="8" :lg="6" :xl="4">
          <NFormItem>
            <div class="flex-center gap-8px">
              <NButton type="primary" size="small" @click="handleSearch">
                {{ $t('common.search') }}
              </NButton>
              <NButton size="small" @click="handleReset">
                {{ $t('common.reset') }}
              </NButton>
            </div>
          </NFormItem>
        </NGridItem>
      </NGrid>
    </NForm>
  </NCard>
</template>

<style scoped></style>
