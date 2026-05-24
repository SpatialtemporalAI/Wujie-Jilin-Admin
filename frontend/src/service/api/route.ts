import { request } from '../request';

/** get user permissions (routes + button permissions) */
export function fetchGetPermissions() {
  return request<Api.Route.UserRoute>({ url: '/admin/sys/route/getPermissions' });
}

/**
 * whether the route is exist
 *
 * @param routeName route name
 */
export function fetchIsRouteExist(routeName: string) {
  return request<boolean>({ url: '/admin/sys/route/isRouteExist', params: { routeName } });
}
