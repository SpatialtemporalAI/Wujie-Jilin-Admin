<script setup lang="ts">
import { toRaw } from 'vue';
import dayjs from 'dayjs';
import { jsonClone } from '@sa/utils';
import { $t } from '@/locales';
import { NButton, NCard, NCollapse, NCollapseItem, NDatePicker, NForm, NFormItemGi, NGrid, NInput, NSpace } from 'naive-ui';

defineOptions({
  name: 'OperationLogSearch'
});

interface Emits {
  (e: 'search'): void;
}

const model = defineModel<Api.SystemManage.OperationLogSearchParams>('model', { required: true });

const emit = defineEmits<Emits>();

const defaultModel = jsonClone(toRaw(model.value));

function resetModel() {
  Object.assign(model.value, defaultModel);
  emit('search');
}

function search() {
  emit('search');
}
</script>

<template>
  <NCard :bordered="false" size="small" class="card-wrapper">
    <NCollapse :default-expanded-names="['operation-log-search']">
      <NCollapseItem :title="$t('common.search')" name="operation-log-search">
        <NForm :model="model" label-placement="left" :label-width="80">
          <NGrid responsive="screen" item-responsive>
            <NFormItemGi span="24 s:12 m:6" :label="$t('page.log.operationLog.username')" path="username" class="pr-24px">
              <NInput
                v-model:value="model.username"
                :placeholder="$t('page.log.operationLog.form.username')"
                clearable
              />
            </NFormItemGi>
            <NFormItemGi span="24 s:12 m:6" :label="$t('page.log.operationLog.module')" path="module" class="pr-24px">
              <NInput
                v-model:value="model.module"
                :placeholder="$t('page.log.operationLog.form.module')"
                clearable
              />
            </NFormItemGi>
            <NFormItemGi span="24 s:12 m:6" :label="$t('page.log.operationLog.action')" path="action" class="pr-24px">
              <NInput
                v-model:value="model.action"
                :placeholder="$t('page.log.operationLog.form.action')"
                clearable
              />
            </NFormItemGi>
            <NFormItemGi span="24 s:24 m:12" :label="$t('page.log.operationLog.form.timeRange')" class="pr-24px">
              <NSpace align="center" :size="8" :wrap="false" class="w-full">
                <NDatePicker
                  :value="null"
                  type="datetime"
                  :placeholder="$t('page.log.operationLog.form.startTime')"
                  clearable
                  class="flex-1"
                  @update:value="(val: number | null) => { model.start_time = val ? dayjs(val).format() : null }"
                />
                <span>~</span>
                <NDatePicker
                  :value="null"
                  type="datetime"
                  :placeholder="$t('page.log.operationLog.form.endTime')"
                  clearable
                  class="flex-1"
                  @update:value="(val: number | null) => { model.end_time = val ? dayjs(val).format() : null }"
                />
              </NSpace>
            </NFormItemGi>
            <NFormItemGi span="24 m:12" class="pr-24px">
              <NSpace class="w-full" justify="end">
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
            </NFormItemGi>
          </NGrid>
        </NForm>
      </NCollapseItem>
    </NCollapse>
  </NCard>
</template>
