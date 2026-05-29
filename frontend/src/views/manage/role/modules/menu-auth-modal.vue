<script setup lang="ts">
import { computed, h, shallowRef, watch } from 'vue';
import { NTag } from 'naive-ui';
import { fetchAssignMenuToRole, fetchGetAllPages, fetchGetMenuTree, fetchGetRole } from '@/service/api';
import { menuTypeRecord } from '@/constants/business';
import { $t } from '@/locales';

defineOptions({
  name: 'MenuAuthModal'
});

interface Props {
  /** the roleId */
  roleId: number;
}

const props = defineProps<Props>();

const visible = defineModel<boolean>('visible', {
  default: false
});

function closeModal() {
  visible.value = false;
}

const title = computed(() => $t('common.edit') + $t('page.manage.role.menuAuth'));

const tagTypeMap: Record<string, NaiveUI.ThemeColor> = {
  '1': 'default',
  '2': 'primary',
  '3': 'warning'
};

const home = shallowRef('');

async function getHome() {
  home.value = 'home';
}

async function updateHome(val: string) {
  home.value = val;
}

const pages = shallowRef<string[]>([]);

async function getPages() {
  const { error, data } = await fetchGetAllPages();

  if (!error) {
    pages.value = data;
  }
}

const pageSelectOptions = computed(() => {
  const opts: CommonType.Option[] = pages.value.map(page => ({
    label: page,
    value: page
  }));

  return opts;
});

const tree = shallowRef<Api.SystemManage.MenuTree[]>([]);

async function getTree() {
  const { error, data } = await fetchGetMenuTree();

  if (!error) {
    tree.value = data;
  }
}

const checks = shallowRef<number[]>([]);

async function getChecks() {
  const { error, data } = await fetchGetRole(props.roleId);

  if (!error && data) {
    checks.value = data.menu_ids || [];
  }
}

const expandedKeys = shallowRef<number[]>([]);

function getAncestorKeys(treeData: Api.SystemManage.MenuTree[], targetIds: number[]): number[] {
  const ancestorSet = new Set<number>();

  function findAncestors(nodes: Api.SystemManage.MenuTree[], targetId: number, currentPath: number[]): boolean {
    for (const node of nodes) {
      if (node.id === targetId) {
        for (const ancestorId of currentPath) {
          ancestorSet.add(ancestorId);
        }
        return true;
      }
      if (node.children && node.children.length > 0) {
        if (findAncestors(node.children, targetId, [...currentPath, node.id])) {
          return true;
        }
      }
    }
    return false;
  }

  for (const targetId of targetIds) {
    findAncestors(treeData, targetId, []);
  }

  return Array.from(ancestorSet);
}

async function handleSubmit() {
  const { error } = await fetchAssignMenuToRole(props.roleId, checks.value);

  if (!error) {
    window.$message?.success?.($t('common.modifySuccess'));
    closeModal();
  }
}

function renderLabel({ option }: { option: Record<string, unknown> }) {
  const node = option as unknown as Api.SystemManage.MenuTree;
  const tagType = tagTypeMap[node.menuType];

  if (node.menuType === '3') {
    return h(
      'span',
      { class: 'flex items-center gap-8px' },
      {
        default: () => [
          h(NTag, { type: tagType, size: 'small', bordered: false }, { default: () => $t(menuTypeRecord[node.menuType]) }),
          node.label
        ]
      }
    );
  }

  return node.label;
}

async function init() {
  getHome();
  getPages();
  await Promise.all([getTree(), getChecks()]);
  expandedKeys.value = getAncestorKeys(tree.value, checks.value);
}

watch(visible, val => {
  if (val) {
    init();
  }
});
</script>

<template>
  <NModal v-model:show="visible" :title="title" preset="card" class="w-480px">
    <div class="flex-y-center gap-16px pb-12px">
      <div>{{ $t('page.manage.menu.home') }}</div>
      <NSelect :value="home" :options="pageSelectOptions" size="small" class="w-160px" @update:value="updateHome" />
    </div>
    <NTree
      v-model:checked-keys="checks"
      v-model:expanded-keys="expandedKeys"
      :data="tree"
      key-field="id"
      checkable
      cascade
      expand-on-click
      virtual-scroll
      block-line
      :render-label="renderLabel"
      class="h-280px"
    />
    <template #footer>
      <NSpace justify="end">
        <NButton size="small" class="mt-16px" @click="closeModal">
          {{ $t('common.cancel') }}
        </NButton>
        <NButton type="primary" size="small" class="mt-16px" @click="handleSubmit">
          {{ $t('common.confirm') }}
        </NButton>
      </NSpace>
    </template>
  </NModal>
</template>

<style scoped></style>
