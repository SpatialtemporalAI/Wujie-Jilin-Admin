<script setup lang="ts">
import { toRaw } from 'vue';
import {
  NButton,
  NForm,
  NFormItem,
  NFormItemGi,
  NGrid,
  NInput,
  NSelect,
  NSpace
} from 'naive-ui';
import { jsonClone } from '@sa/utils';
import { enableStatusOptions, yesOrNoOptions } from '@/constants/business';
import { $t } from '@/locales';

defineOptions({
  name: 'DictSearch'
});

interface Emits {
  (e: 'search'): void;
  (e: 'reset'): void;
}

const emit = defineEmits<Emits>();

const model = defineModel<Api.SystemManage.DictSearchParams>('model', { required: true });

const defaultModel = jsonClone(toRaw(model.value));

function resetModel() {
  Object.assign(model.value, defaultModel);
  emit('reset');
}

function search() {
  emit('search');
}
</script>

<template>
  <NCard :bordered="false" size="small" class="card-wrapper">
    <NForm :model="model" label-placement="left" :label-width="80">
      <NGrid responsive="screen" item-responsive>
        <NFormItemGi span="24 s:12 m:6" :label="$t('page.manage.dict.dictName')" path="name" class="pr-24px">
          <NInput v-model:value="model.name" :placeholder="$t('page.manage.dict.form.dictName')" clearable />
        </NFormItemGi>
        <NFormItemGi span="24 s:12 m:6" :label="$t('page.manage.dict.dictCode')" path="code" class="pr-24px">
          <NInput v-model:value="model.code" :placeholder="$t('page.manage.dict.form.dictCode')" clearable />
        </NFormItemGi>
        <NFormItemGi span="24 s:12 m:6" :label="$t('page.manage.dict.dictStatus')" path="status" class="pr-24px">
          <NSelect
            v-model:value="model.status"
            :options="enableStatusOptions"
            :placeholder="$t('page.manage.dict.form.dictStatus')"
            clearable
          />
        </NFormItemGi>
        <NFormItemGi span="24 s:12 m:6" :label="$t('page.manage.dict.isSystem')" path="is_system" class="pr-24px">
          <NSelect
            v-model:value="model.is_system"
            :options="yesOrNoOptions"
            :placeholder="$t('page.manage.dict.form.isSystem')"
            clearable
          />
        </NFormItemGi>
      </NGrid>
      <NSpace class="mt-16px w-full" justify="end">
        <NButton @click="resetModel">
          <template #icon>
            <icon-ic-round-refresh class="text-icon" />
          </template>
          {{ $t('common.reset') }}
        </NButton>
        <NButton type="primary" ghost @click="search">
          <template #icon>
            <icon-ic-round-search class="text-icon" />
          </template>
          {{ $t('common.search') }}
        </NButton>
      </NSpace>
    </NForm>
  </NCard>
</template>

<style scoped></style>
