<script setup lang="ts">
import { toRaw } from 'vue';
import { jsonClone } from '@sa/utils';
import { $t } from '@/locales';

defineOptions({
  name: 'IpBlacklistSearch'
});

interface Emits {
  (e: 'search'): void;
  (e: 'reset'): void;
}

const emit = defineEmits<Emits>();

const model = defineModel<Api.SystemManage.IpBlacklistSearchParams>('model', { required: true });

const defaultModel = jsonClone(toRaw(model.value));

const typeOptions = [
  { label: $t('page.manage.ipBlacklist.typePermanent'), value: 'permanent' },
  { label: $t('page.manage.ipBlacklist.typeTemporary'), value: 'temporary' }
];

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
        <NFormItemGi span="24 s:12 m:6" :label="$t('page.manage.ipBlacklist.ip')" path="ip" class="pr-24px">
          <NInput v-model:value="model.ip" :placeholder="$t('page.manage.ipBlacklist.form.ip')" clearable />
        </NFormItemGi>
        <NFormItemGi span="24 s:12 m:6" :label="$t('page.manage.ipBlacklist.type')" path="type" class="pr-24px">
          <NSelect
            v-model:value="model.type"
            :options="typeOptions"
            :placeholder="$t('page.manage.ipBlacklist.form.type')"
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
