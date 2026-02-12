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
