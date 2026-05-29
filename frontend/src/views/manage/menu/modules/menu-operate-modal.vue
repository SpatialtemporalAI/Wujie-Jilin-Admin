<script setup lang="tsx">
import { computed, ref, watch } from 'vue';
import type { SelectOption } from 'naive-ui';
import { enableStatusOptions, menuIconTypeOptions, menuTypeOptions } from '@/constants/business';
import { fetchCreateMenu, fetchGetAllRoles, fetchGetMenuTree, fetchUpdateMenu } from '@/service/api';
import { useFormRules, useNaiveForm } from '@/hooks/common/form';
import { getLocalIcons } from '@/utils/icon';
import { $t } from '@/locales';
import SvgIcon from '@/components/custom/svg-icon.vue';
import {
  getLayoutAndPage,
  getPathParamFromRoutePath,
  getRoutePathByRouteName,
  getRoutePathWithParam,
  transformLayoutAndPageToComponent
} from './shared';

defineOptions({
  name: 'MenuOperateModal'
});

export type OperateType = NaiveUI.TableOperateType | 'addChild';

interface Props {
  /** the type of operation */
  operateType: OperateType;
  /** the edit menu data or the parent menu data when adding a child menu */
  rowData?: Api.SystemManage.Menu | null;
  /** all pages */
  allPages: string[];
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
const { defaultRequiredRule } = useFormRules();

const title = computed(() => {
  const titles: Record<OperateType, string> = {
    add: $t('page.manage.menu.addMenu'),
    addChild: $t('page.manage.menu.addChildMenu'),
    edit: $t('page.manage.menu.editMenu')
  };
  return titles[props.operateType];
});

type Model = Pick<
  Api.SystemManage.Menu,
  | 'menuType'
  | 'menuName'
  | 'routeName'
  | 'routePath'
  | 'component'
  | 'order'
  | 'i18nKey'
  | 'icon'
  | 'iconType'
  | 'status'
  | 'parentId'
  | 'keepAlive'
  | 'constant'
  | 'href'
  | 'hideInMenu'
  | 'activeMenu'
  | 'multiTab'
  | 'fixedIndexInTab'
  | 'is_system'
> & {
  query: NonNullable<Api.SystemManage.Menu['query']>;
  buttons: NonNullable<Api.SystemManage.Menu['buttons']>;
  permission: string;
  layout: string;
  page: string;
  pathParam: string;
};

const model = ref(createDefaultModel());

const menuTreeRaw = ref<Api.SystemManage.MenuTree[]>([]);

async function getMenuTree() {
  const { data } = await fetchGetMenuTree();
  menuTreeRaw.value = data || [];
}

function collectDescendantIds(trees: Api.SystemManage.MenuTree[], excludeId: number): Set<number> {
  const ids = new Set<number>();
  function walk(nodes: Api.SystemManage.MenuTree[]) {
    for (const node of nodes) {
      if (node.id === excludeId) {
        ids.add(node.id);
        if (node.children) walk(node.children);
        continue;
      }
      if (node.children) walk(node.children);
    }
  }
  walk(trees);
  return ids;
}

function filterTree(
  trees: Api.SystemManage.MenuTree[],
  excludeIds: Set<number>
): Api.SystemManage.MenuTree[] {
  return trees
    .filter(t => !excludeIds.has(t.id))
    .map(t => ({
      ...t,
      children: t.children ? filterTree(t.children, excludeIds) : undefined
    }));
}

function filterTreeByType(
  trees: Api.SystemManage.MenuTree[],
  allowedParentType: Api.SystemManage.MenuType
): Api.SystemManage.MenuTree[] {
  return trees
    .filter(t => t.menuType === allowedParentType)
    .map(t => ({
      ...t,
      children: t.children ? filterTreeByType(t.children, allowedParentType) : undefined
    }));
}

const parentMenuOptions = computed(() => {
  let trees = menuTreeRaw.value;
  if (props.operateType === 'edit' && props.rowData) {
    const excludeIds = collectDescendantIds(trees, props.rowData.id);
    excludeIds.add(props.rowData.id);
    trees = filterTree(trees, excludeIds);
  }
  if (model.value.menuType === '2') {
    trees = filterTreeByType(trees, '1');
  } else if (model.value.menuType === '3') {
    trees = filterTreeByType(trees, '2');
  }
  return trees;
});

function createDefaultModel(): Model {
  return {
    menuType: '1',
    menuName: '',
    routeName: '',
    routePath: '',
    pathParam: '',
    component: '',
    layout: 'base',
    page: '',
    i18nKey: null,
    icon: '',
    iconType: '1',
    parentId: 0,
    status: '1',
    keepAlive: false,
    constant: false,
    order: 0,
    href: null,
    hideInMenu: false,
    activeMenu: null,
    multiTab: false,
    fixedIndexInTab: null,
    query: [],
    buttons: [],
    permission: '',
    is_system: '2'
  };
}

type RuleKey = Extract<keyof Model, 'menuName' | 'status' | 'routeName' | 'routePath' | 'permission'>;

const rules = computed<Record<RuleKey, App.Global.FormRule>>(() => {
  const base: Record<RuleKey, App.Global.FormRule> = {
    menuName: defaultRequiredRule,
    status: defaultRequiredRule,
    routeName: defaultRequiredRule,
    routePath: defaultRequiredRule,
    permission: defaultRequiredRule
  };
  if (model.value.menuType === '3') {
    return {
      ...base,
      routeName: { required: false },
      routePath: { required: false }
    } as Record<RuleKey, App.Global.FormRule>;
  }
  return {
    ...base,
    permission: { required: false }
  } as Record<RuleKey, App.Global.FormRule>;
});

const disabledMenuType = computed(() => props.operateType === 'edit');

const localIcons = getLocalIcons();
const localIconOptions = localIcons.map<SelectOption>(item => ({
  label: () => (
    <div class="flex-y-center gap-16px">
      <SvgIcon localIcon={item} class="text-icon" />
      <span>{item}</span>
    </div>
  ),
  value: item
}));

const showLayout = computed(() => !model.value.parentId);

const showPage = computed(() => model.value.menuType === '2');

const isButton = computed(() => model.value.menuType === '3');

const pageOptions = computed(() => {
  const allPages = [...props.allPages];

  if (model.value.routeName && !allPages.includes(model.value.routeName)) {
    allPages.unshift(model.value.routeName);
  }

  const opts: CommonType.Option[] = allPages.map(page => ({
    label: page,
    value: page
  }));

  return opts;
});

const layoutOptions = computed<CommonType.Option[]>(() => [
  {
    label: $t('page.manage.menu.layoutBase'),
    value: 'base'
  },
  {
    label: $t('page.manage.menu.layoutBlank'),
    value: 'blank'
  }
]);

/** the enabled role options */
const roleOptions = ref<CommonType.Option<string>[]>([]);

async function getRoleOptions() {
  const { error, data } = await fetchGetAllRoles();

  if (!error) {
    const options = data.map(item => ({
      label: item.name,
      value: item.code
    }));

    roleOptions.value = [...options];
  }
}

function handleInitModel() {
  model.value = createDefaultModel();

  if (!props.rowData) return;

  if (props.operateType === 'addChild') {
    const { id } = props.rowData;

    Object.assign(model.value, { parentId: id });
  }

  if (props.operateType === 'edit') {
    const { component, ...rest } = props.rowData;

    const { layout, page } = getLayoutAndPage(component);
    const { path, param } = getPathParamFromRoutePath(rest.routePath);

    Object.assign(model.value, rest, { layout, page, routePath: path, pathParam: param });
    model.value.permission = props.rowData.permission || '';
  }

  if (!model.value.query) {
    model.value.query = [];
  }
  if (!model.value.buttons) {
    model.value.buttons = [];
  }
}

function closeDrawer() {
  visible.value = false;
}

function handleUpdateRoutePathByRouteName() {
  if (model.value.routeName) {
    model.value.routePath = getRoutePathByRouteName(model.value.routeName);
  } else {
    model.value.routePath = '';
  }
}

function handleUpdateI18nKeyByRouteName() {
  if (model.value.routeName) {
    model.value.i18nKey = `route.${model.value.routeName}` as App.I18n.I18nKey;
  } else {
    model.value.i18nKey = null;
  }
}

function handleCreateButton() {
  const buttonItem: Api.SystemManage.MenuButton = {
    code: '',
    desc: ''
  };

  return buttonItem;
}

function getSubmitParams() {
  const { layout, page, pathParam, ...params } = model.value;

  if (model.value.menuType === '3') {
    params.routeName = '';
    params.routePath = '';
    params.component = '';
    params.icon = '';
    params.buttons = [];
    params.query = [];
    return params;
  }

  // Child menus inherit layout from parent, so only include layout for top-level menus
  const effectiveLayout = model.value.parentId ? '' : layout;
  const component = transformLayoutAndPageToComponent(effectiveLayout, page);
  const routePath = getRoutePathWithParam(model.value.routePath, pathParam);

  params.component = component;
  params.routePath = routePath;

  return params;
}

async function handleSubmit() {
  await validate();

  const params = getSubmitParams();

  let error: any = null;

  if (props.operateType === 'edit') {
    const result = await fetchUpdateMenu(props.rowData!.id, params);
    error = result.error;
  } else {
    const result = await fetchCreateMenu(params);
    error = result.error;
  }

  if (!error) {
    window.$message?.success(props.operateType === 'edit' ? $t('common.updateSuccess') : $t('common.addSuccess'));
    closeDrawer();
    emit('submitted');
  }
}

watch(visible, () => {
  if (visible.value) {
    handleInitModel();
    restoreValidation();
    getRoleOptions();
    getMenuTree();
  }
});

watch(
  () => model.value.routeName,
  () => {
    handleUpdateRoutePathByRouteName();
    handleUpdateI18nKeyByRouteName();
  }
);
</script>

<template>
  <NModal v-model:show="visible" :title="title" preset="card" class="w-800px">
    <NScrollbar class="h-480px pr-20px">
      <NForm ref="formRef" :model="model" :rules="rules" label-placement="left" :label-width="100">
        <NGrid responsive="screen" item-responsive>
          <NFormItemGi span="24 m:12" :label="$t('page.manage.menu.parentMenu')" path="parentId">
            <NTreeSelect
              v-model:value="model.parentId"
              :options="parentMenuOptions"
              key-field="id"
              label-field="label"
              children-field="children"
              :placeholder="$t('page.manage.menu.form.parentMenu')"
              clearable
              default-expand-all
            />
          </NFormItemGi>
          <NFormItemGi span="24 m:12" :label="$t('page.manage.menu.menuType')" path="menuType">
            <NRadioGroup v-model:value="model.menuType" :disabled="disabledMenuType">
              <NRadio v-for="item in menuTypeOptions" :key="item.value" :value="item.value" :label="item.label" />
            </NRadioGroup>
          </NFormItemGi>
          <NFormItemGi span="24 m:12" :label="$t('page.manage.menu.menuName')" path="menuName">
            <NInput v-model:value="model.menuName" :placeholder="$t('page.manage.menu.form.menuName')" />
          </NFormItemGi>
          <NFormItemGi
            v-if="isButton"
            span="24 m:12"
            :label="$t('page.manage.menu.permission')"
            path="permission"
          >
            <NInput v-model:value="model.permission" :placeholder="$t('page.manage.menu.form.permission')" />
          </NFormItemGi>
          <NFormItemGi v-if="!isButton" span="24 m:12" :label="$t('page.manage.menu.routeName')" path="routeName">
            <NInput v-model:value="model.routeName" :placeholder="$t('page.manage.menu.form.routeName')" />
          </NFormItemGi>
          <NFormItemGi v-if="!isButton" span="24 m:12" :label="$t('page.manage.menu.routePath')" path="routePath">
            <NInput v-model:value="model.routePath" disabled :placeholder="$t('page.manage.menu.form.routePath')" />
          </NFormItemGi>
          <NFormItemGi v-if="!isButton" span="24 m:12" :label="$t('page.manage.menu.pathParam')" path="pathParam">
            <NInput v-model:value="model.pathParam" :placeholder="$t('page.manage.menu.form.pathParam')" />
          </NFormItemGi>
          <NFormItemGi v-if="!isButton && showLayout" span="24 m:12" :label="$t('page.manage.menu.layout')" path="layout">
            <NSelect
              v-model:value="model.layout"
              :options="layoutOptions"
              :placeholder="$t('page.manage.menu.form.layout')"
            />
          </NFormItemGi>
          <NFormItemGi v-if="!isButton && showPage" span="24 m:12" :label="$t('page.manage.menu.page')" path="page">
            <NSelect
              v-model:value="model.page"
              :options="pageOptions"
              :placeholder="$t('page.manage.menu.form.page')"
            />
          </NFormItemGi>
          <NFormItemGi v-if="!isButton" span="24 m:12" :label="$t('page.manage.menu.i18nKey')" path="i18nKey">
            <NInput v-model:value="model.i18nKey" :placeholder="$t('page.manage.menu.form.i18nKey')" />
          </NFormItemGi>
          <NFormItemGi span="24 m:12" :label="$t('page.manage.menu.order')" path="order">
            <NInputNumber v-model:value="model.order" class="w-full" :placeholder="$t('page.manage.menu.form.order')" />
          </NFormItemGi>
          <NFormItemGi v-if="!isButton" span="24 m:12" :label="$t('page.manage.menu.iconTypeTitle')" path="iconType">
            <NRadioGroup v-model:value="model.iconType">
              <NRadio v-for="item in menuIconTypeOptions" :key="item.value" :value="item.value" :label="item.label" />
            </NRadioGroup>
          </NFormItemGi>
          <NFormItemGi v-if="!isButton" span="24 m:12" :label="$t('page.manage.menu.icon')" path="icon">
            <template v-if="model.iconType === '1'">
              <div class="flex-y-center gap-8px w-full">
                <NInput v-model:value="model.icon" :placeholder="$t('page.manage.menu.form.icon')" class="flex-1">
                  <template #suffix>
                    <SvgIcon v-if="model.icon" :icon="model.icon" class="text-icon" />
                  </template>
                </NInput>
                <NButton @click="window.open('https://icon-sets.iconify.design/', '_blank')">
                  <icon-ic:round-launch class="text-icon" />
                </NButton>
              </div>
            </template>
            <template v-if="model.iconType === '2'">
              <NSelect
                v-model:value="model.icon"
                :placeholder="$t('page.manage.menu.form.localIcon')"
                :options="localIconOptions"
              />
            </template>
          </NFormItemGi>
          <NFormItemGi span="24 m:12" :label="$t('page.manage.menu.menuStatus')" path="status">
            <NRadioGroup v-model:value="model.status">
              <NRadio v-for="item in enableStatusOptions" :key="item.value" :value="item.value" :label="item.label" />
            </NRadioGroup>
          </NFormItemGi>
          <NFormItemGi span="24 m:12" :label="$t('page.manage.menu.isSystem')" path="is_system">
            <NRadioGroup v-model:value="model.is_system">
              <NRadio v-for="item in enableStatusOptions" :key="item.value" :value="item.value" :label="item.label" />
            </NRadioGroup>
          </NFormItemGi>
          <NFormItemGi v-if="!isButton" span="24 m:12" :label="$t('page.manage.menu.keepAlive')" path="keepAlive">
            <NRadioGroup v-model:value="model.keepAlive">
              <NRadio :value="true" :label="$t('common.yesOrNo.yes')" />
              <NRadio :value="false" :label="$t('common.yesOrNo.no')" />
            </NRadioGroup>
          </NFormItemGi>
          <NFormItemGi v-if="!isButton" span="24 m:12" :label="$t('page.manage.menu.constant')" path="constant">
            <NRadioGroup v-model:value="model.constant">
              <NRadio :value="true" :label="$t('common.yesOrNo.yes')" />
              <NRadio :value="false" :label="$t('common.yesOrNo.no')" />
            </NRadioGroup>
          </NFormItemGi>
          <NFormItemGi v-if="!isButton" span="24 m:12" :label="$t('page.manage.menu.href')" path="href">
            <NInput v-model:value="model.href" :placeholder="$t('page.manage.menu.form.href')" />
          </NFormItemGi>
          <NFormItemGi v-if="!isButton" span="24 m:12" :label="$t('page.manage.menu.hideInMenu')" path="hideInMenu">
            <NRadioGroup v-model:value="model.hideInMenu">
              <NRadio :value="true" :label="$t('common.yesOrNo.yes')" />
              <NRadio :value="false" :label="$t('common.yesOrNo.no')" />
            </NRadioGroup>
          </NFormItemGi>
          <NFormItemGi
            v-if="!isButton && model.hideInMenu"
            span="24 m:12"
            :label="$t('page.manage.menu.activeMenu')"
            path="activeMenu"
          >
            <NSelect
              v-model:value="model.activeMenu"
              :options="pageOptions"
              clearable
              :placeholder="$t('page.manage.menu.form.activeMenu')"
            />
          </NFormItemGi>
          <NFormItemGi v-if="!isButton" span="24 m:12" :label="$t('page.manage.menu.multiTab')" path="multiTab">
            <NRadioGroup v-model:value="model.multiTab">
              <NRadio :value="true" :label="$t('common.yesOrNo.yes')" />
              <NRadio :value="false" :label="$t('common.yesOrNo.no')" />
            </NRadioGroup>
          </NFormItemGi>
          <NFormItemGi v-if="!isButton" span="24 m:12" :label="$t('page.manage.menu.fixedIndexInTab')" path="fixedIndexInTab">
            <NInputNumber
              v-model:value="model.fixedIndexInTab"
              class="w-full"
              clearable
              :placeholder="$t('page.manage.menu.form.fixedIndexInTab')"
            />
          </NFormItemGi>
          <NFormItemGi v-if="!isButton" span="24" :label="$t('page.manage.menu.query')">
            <NDynamicInput
              v-model:value="model.query"
              preset="pair"
              :key-placeholder="$t('page.manage.menu.form.queryKey')"
              :value-placeholder="$t('page.manage.menu.form.queryValue')"
            >
              <template #action="{ index, create, remove }">
                <NSpace class="ml-12px">
                  <NButton size="medium" @click="() => create(index)">
                    <icon-ic:round-plus class="text-icon" />
                  </NButton>
                  <NButton size="medium" @click="() => remove(index)">
                    <icon-ic-round-remove class="text-icon" />
                  </NButton>
                </NSpace>
              </template>
            </NDynamicInput>
          </NFormItemGi>
          <NFormItemGi v-if="!isButton" span="24" :label="$t('page.manage.menu.button')">
            <NDynamicInput v-model:value="model.buttons" :on-create="handleCreateButton">
              <template #default="{ value }">
                <div class="flex-y-center flex-1 gap-12px">
                  <NInput
                    v-model:value="value.code"
                    :placeholder="$t('page.manage.menu.form.buttonCode')"
                    class="flex-1"
                  />
                  <NInput
                    v-model:value="value.desc"
                    :placeholder="$t('page.manage.menu.form.buttonDesc')"
                    class="flex-1"
                  />
                </div>
              </template>
              <template #action="{ index, create, remove }">
                <NSpace class="ml-12px">
                  <NButton size="medium" @click="() => create(index)">
                    <icon-ic:round-plus class="text-icon" />
                  </NButton>
                  <NButton size="medium" @click="() => remove(index)">
                    <icon-ic-round-remove class="text-icon" />
                  </NButton>
                </NSpace>
              </template>
            </NDynamicInput>
          </NFormItemGi>
        </NGrid>
      </NForm>
    </NScrollbar>
    <template #footer>
      <NSpace justify="end" :size="16">
        <NButton @click="closeDrawer">{{ $t('common.cancel') }}</NButton>
        <NButton type="primary" @click="handleSubmit">{{ $t('common.confirm') }}</NButton>
      </NSpace>
    </template>
  </NModal>
</template>

<style scoped></style>
