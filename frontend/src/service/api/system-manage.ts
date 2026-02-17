import { request } from '../request';

/** get role list */
export function fetchGetRoleList(params?: Api.SystemManage.RoleSearchParams) {
  return request<Api.SystemManage.RoleList>({
    url: '/sys/role/list',
    method: 'get',
    params
  });
}

/**
 * get all roles
 *
 * these roles are all enabled
 */
export function fetchGetAllRoles() {
  return request<Api.SystemManage.AllRole[]>({
    url: '/sys/role/all',
    method: 'get'
  });
}

/** get user list */
export function fetchGetUserList(params?: Api.SystemManage.UserSearchParams) {
  return request<Api.SystemManage.UserList>({
    url: '/sys/user/list',
    method: 'get',
    params
  });
}

/** get menu list */
export function fetchGetMenuList() {
  return request<Api.SystemManage.MenuList>({
    url: '/sys/menu/list',
    method: 'get'
  });
}

/** get all pages */
export function fetchGetAllPages() {
  return request<string[]>({
    url: '/sys/menu/pages',
    method: 'get'
  });
}

/** get menu tree */
export function fetchGetMenuTree() {
  return request<Api.SystemManage.MenuTree[]>({
    url: '/sys/menu/tree',
    method: 'get'
  });
}

/** change user password */
export function fetchChangeUserPassword(userId: number, newPassword: string) {
  return request<void>({
    url: `/sys/user/${userId}/password`,
    method: 'put',
    data: {
      new_password: newPassword
    }
  });
}

/** create user */
export function fetchCreateUser(user: Api.SystemManage.UserCreate) {
  return request<Api.SystemManage.User>({
    url: '/sys/user/add',
    method: 'post',
    data: user
  });
}

/** update user */
export function fetchUpdateUser(userId: number, user: Api.SystemManage.UserUpdate) {
  return request<Api.SystemManage.User>({
    url: `/sys/user/${userId}`,
    method: 'put',
    data: user
  });
}

/** delete user */
export function fetchDeleteUser(userId: number) {
  return request<void>({
    url: `/sys/user/${userId}`,
    method: 'delete'
  });
}

/** ==================== 字典管理 API ==================== */

/** get dict list */
export function fetchGetDictList(params?: Api.SystemManage.DictSearchParams) {
  return request<Api.SystemManage.DictList>({
    url: '/sys/dict/list',
    method: 'get',
    params
  });
}

/** get all dicts */
export function fetchGetAllDicts(status?: boolean) {
  return request<Api.SystemManage.Dict[]>({
    url: '/sys/dict/all',
    method: 'get',
    params: { status }
  });
}

/** get dict by code */
export function fetchGetDictByCode(code: string) {
  return request<Api.SystemManage.DictWithItems>({
    url: `/sys/dict/code/${code}`,
    method: 'get'
  });
}

/** get dict by id */
export function fetchGetDict(dictId: number) {
  return request<Api.SystemManage.Dict>({
    url: `/sys/dict/${dictId}`,
    method: 'get'
  });
}

/** get dict with items */
export function fetchGetDictWithItems(dictId: number) {
  return request<Api.SystemManage.DictWithItems>({
    url: `/sys/dict/${dictId}/with-items`,
    method: 'get'
  });
}

/** create dict */
export function fetchCreateDict(dict: Api.SystemManage.DictCreate) {
  return request<Api.SystemManage.Dict>({
    url: '/sys/dict',
    method: 'post',
    data: dict
  });
}

/** update dict */
export function fetchUpdateDict(dictId: number, dict: Api.SystemManage.DictUpdate) {
  return request<Api.SystemManage.Dict>({
    url: `/sys/dict/${dictId}`,
    method: 'put',
    data: dict
  });
}

/** batch update dict status */
export function fetchBatchUpdateDictStatus(data: Api.SystemManage.DictBatchUpdateStatus) {
  return request<void>({
    url: '/sys/dict/batch/status',
    method: 'put',
    data
  });
}

/** delete dict */
export function fetchDeleteDict(dictId: number) {
  return request<void>({
    url: `/sys/dict/${dictId}`,
    method: 'delete'
  });
}

/** ==================== 字典项管理 API ==================== */

/** get dict item list */
export function fetchGetDictItemList(params?: Api.SystemManage.DictItemSearchParams) {
  return request<Api.SystemManage.DictItemList>({
    url: '/sys/dict/item/list',
    method: 'get',
    params
  });
}

/** get dict items by dict code */
export function fetchGetDictItemsByDictCode(dictCode: string) {
  return request<Api.SystemManage.DictItem[]>({
    url: `/sys/dict/item/all/${dictCode}`,
    method: 'get'
  });
}

/** get dict item by id */
export function fetchGetDictItem(itemId: number) {
  return request<Api.SystemManage.DictItem>({
    url: `/sys/dict/item/${itemId}`,
    method: 'get'
  });
}

/** create dict item */
export function fetchCreateDictItem(item: Api.SystemManage.DictItemCreate) {
  return request<Api.SystemManage.DictItem>({
    url: '/sys/dict/item',
    method: 'post',
    data: item
  });
}

/** update dict item */
export function fetchUpdateDictItem(itemId: number, item: Api.SystemManage.DictItemUpdate) {
  return request<Api.SystemManage.DictItem>({
    url: `/sys/dict/item/${itemId}`,
    method: 'put',
    data: item
  });
}

/** batch update dict item status */
export function fetchBatchUpdateDictItemStatus(data: Api.SystemManage.DictItemBatchUpdateStatus) {
  return request<void>({
    url: '/sys/dict/item/batch/status',
    method: 'put',
    data
  });
}

/** delete dict item */
export function fetchDeleteDictItem(itemId: number) {
  return request<void>({
    url: `/sys/dict/item/${itemId}`,
    method: 'delete'
  });
}

/** ==================== 系统配置管理 API ==================== */

/** get config list */
export function fetchGetConfigList(params?: Api.SystemManage.ConfigSearchParams) {
  return request<Api.SystemManage.ConfigList>({
    url: '/sys/config/list',
    method: 'get',
    params
  });
}

/** get all configs */
export function fetchGetAllConfigs(group?: Api.SystemManage.ConfigGroup, editableOnly?: boolean) {
  return request<Api.SystemManage.Config[]>({
    url: '/sys/config/all',
    method: 'get',
    params: { group, editable_only: editableOnly }
  });
}

/** get configs by group */
export function fetchGetConfigsByGroup(group: Api.SystemManage.ConfigGroup, editableOnly?: boolean) {
  return request<Api.SystemManage.Config[]>({
    url: `/sys/config/group/${group}`,
    method: 'get',
    params: { editable_only: editableOnly }
  });
}

/** get config by id */
export function fetchGetConfigById(configId: number) {
  return request<Api.SystemManage.Config>({
    url: `/sys/config/id/${configId}`,
    method: 'get'
  });
}

/** get config by key */
export function fetchGetConfigByKey(configKey: string) {
  return request<Api.SystemManage.Config>({
    url: `/sys/config/key/${configKey}`,
    method: 'get'
  });
}

/** get config value */
export function fetchGetConfigValue(configKey: string, defaultValue?: string) {
  return request({
    url: `/sys/config/value/${configKey}`,
    method: 'get',
    params: { default: defaultValue }
  });
}

/** create config */
export function fetchCreateConfig(config: Api.SystemManage.ConfigCreate) {
  return request<Api.SystemManage.Config>({
    url: '/sys/config',
    method: 'post',
    data: config
  });
}

/** update config */
export function fetchUpdateConfig(configId: number, config: Api.SystemManage.ConfigUpdate) {
  return request<Api.SystemManage.Config>({
    url: `/sys/config/${configId}`,
    method: 'put',
    data: config
  });
}

/** batch update configs */
export function fetchBatchUpdateConfigs(data: Api.SystemManage.ConfigBatchUpdate) {
  return request<void>({
    url: '/sys/config/batch/update',
    method: 'put',
    data
  });
}

/** reset configs */
export function fetchResetConfigs(data: Api.SystemManage.ConfigReset) {
  return request<void>({
    url: '/sys/config/batch/reset',
    method: 'put',
    data
  });
}

/** delete config */
export function fetchDeleteConfig(configId: number) {
  return request<void>({
    url: `/sys/config/${configId}`,
    method: 'delete'
  });
}
