<script setup lang="ts">
import { computed } from 'vue';
import { NTag } from 'naive-ui';
import { useDict } from '@/hooks/business/dict';

defineOptions({ name: 'DictTag' });

const props = withDefaults(
  defineProps<{
    dictCode: string;
    value?: string | null;
    type?: 'default' | 'primary' | 'info' | 'success' | 'warning' | 'error';
  }>(),
  { value: null, type: 'default' }
);

const { getLabelByValue } = useDict(() => props.dictCode);

const label = computed(() => getLabelByValue(props.value));
</script>

<template>
  <NTag v-if="label" :type="type">
    {{ label }}
  </NTag>
</template>
