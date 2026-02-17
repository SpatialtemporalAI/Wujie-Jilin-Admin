<script setup lang="tsx">
import { useVModel } from '@vueuse/core';
import { NButton, NForm, NFormItem, NGrid, NGridItem, NInput, NSelect } from 'naive-ui';
import { enableStatusOptions, yesOrNoOptions } from '@/constants/business';
import { $t } from '@/locales';

interface Props {
  model: Api.SystemManage.DictSearchParams;
}

const props = defineProps<Props>();
const emit = defineEmits<{
  search: [];
  reset: [];
}>();

const model = useVModel(props, 'model');

function handleSearch() {
  emit('search');
}

function handleReset() {
  model.value = {
    page: 1,
    page_size: 10,
    name: null,
    code: null,
    status: null,
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
          <NFormItem :label="$t('page.manage.dict.dictName')">
            <NInput v-model:value="model.name" :placeholder="$t('common.keywordSearch')" clearable />
          </NFormItem>
        </NGridItem>
        <NGridItem :xs="24" :sm="12" :md="8" :lg="6" :xl="4">
          <NFormItem :label="$t('page.manage.dict.dictCode')">
            <NInput v-model:value="model.code" :placeholder="$t('common.keywordSearch')" clearable />
          </NFormItem>
        </NGridItem>
        <NGridItem :xs="24" :sm="12" :md="8" :lg="6" :xl="4">
          <NFormItem :label="$t('page.manage.dict.dictStatus')">
            <NRadioGroup v-model:value="model.status">
              <NRadio v-for="item in enableStatusOptions" :key="item.value" :value="item.value"
                :label="$t(item.label)" />
            </NRadioGroup>
          </NFormItem>
        </NGridItem>
        <NGridItem :xs="24" :sm="12" :md="8" :lg="6" :xl="4">
          <NFormItem :label="$t('page.manage.dict.isSystem')">
            <NSelect v-model:value="model.is_system" :options="yesOrNoOptions" :placeholder="$t('common.keywordSearch')"
              clearable />
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
