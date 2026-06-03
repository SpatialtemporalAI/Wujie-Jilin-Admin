<script setup lang="ts">
import { computed } from 'vue';
import { useDict } from '@/hooks/business/dict';

defineOptions({ name: 'DictText' });

const props = defineProps<{
  dictCode: string;
  value?: string | null;
}>();

const { getLabelByValue } = useDict(() => props.dictCode);

const label = computed(() => getLabelByValue(props.value));
</script>

<template>
  <span>{{ label }}</span>
</template>
