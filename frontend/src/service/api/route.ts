import { request } from '../request';

/** get user routes */
export function fetchGetUserRoutes() {
  return request<Api.Route.UserRoute>({ url: '/admin/sys/route/getUserRoutes' });
}

/**
 * whether the route is exist
 *
 * @param routeName route name
 */
export function fetchIsRouteExist(routeName: string) {
  return request<boolean>({ url: '/admin/sys/route/isRouteExist', params: { routeName } });
}
