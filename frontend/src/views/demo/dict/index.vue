<script setup lang="ts">
import { ref } from 'vue';

defineOptions({ name: 'DictDemoPage' });

const selectedGender = ref<string | null>(null);
const selectedGender2 = ref<string | null>('0');
</script>

<template>
  <NSpace vertical :size="16">
    <NCard :bordered="false" :title="$t('page.demo.dict.selectDemo')" class="card-wrapper">
      <NSpace vertical :size="12">
        <NText>{{ $t('page.demo.dict.selectLabel') }}</NText>
        <DictSelect dict-code="gender" v-model:value="selectedGender" />
        <NText depth="3">
          v-model value: {{ selectedGender ?? 'null' }}
        </NText>

        <NDivider />

        <NText>{{ $t('page.demo.dict.selectWithDefault') }}</NText>
        <DictSelect dict-code="gender" v-model:value="selectedGender2" />
        <NText depth="3">
          v-model value: {{ selectedGender2 ?? 'null' }}
        </NText>
      </NSpace>
    </NCard>

    <NCard :bordered="false" :title="$t('page.demo.dict.tagDemo')" class="card-wrapper">
      <NSpace vertical :size="12">
        <NText>{{ $t('page.demo.dict.tagLabel') }}</NText>
        <NSpace :size="8">
          <DictTag dict-code="gender" value="1" type="primary" />
          <DictTag dict-code="gender" value="2" type="error" />
          <DictTag dict-code="gender" value="0" type="warning" />
        </NSpace>
      </NSpace>
    </NCard>

    <NCard :bordered="false" :title="$t('page.demo.dict.textDemo')" class="card-wrapper">
      <NSpace vertical :size="12">
        <NText>{{ $t('page.demo.dict.textLabel') }}</NText>
        <NDescriptions bordered :column="3" label-placement="left">
          <NDescriptions-item label="value = 1">
            <DictText dict-code="gender" value="1" />
          </NDescriptions-item>
          <NDescriptions-item label="value = 2">
            <DictText dict-code="gender" value="2" />
          </NDescriptions-item>
          <NDescriptions-item label="value = 0">
            <DictText dict-code="gender" value="0" />
          </NDescriptions-item>
        </NDescriptions>
      </NSpace>
    </NCard>

    <NCard :bordered="false" :title="$t('page.demo.dict.tableDemo')" class="card-wrapper">
      <NSpace vertical :size="12">
        <NText>{{ $t('page.demo.dict.tableLabel') }}</NText>
        <NDataTable
          :bordered="false"
          :columns="[
            { key: 'name', title: 'Name' },
            { key: 'gender', title: 'Gender (DictText)' },
            { key: 'tag', title: 'Gender (DictTag)' }
          ]"
          :data="[
            { name: 'Alice', gender: '1', tag: '1' },
            { name: 'Bob', gender: '2', tag: '2' },
            { name: 'Unknown', gender: '0', tag: '0' }
          ]"
        >
          <template #gender="{ row }">
            <DictText dict-code="gender" :value="row.gender" />
          </template>
          <template #tag="{ row }">
            <DictTag dict-code="gender" :value="row.tag" />
          </template>
        </NDataTable>
      </NSpace>
    </NCard>
  </NSpace>
</template>
