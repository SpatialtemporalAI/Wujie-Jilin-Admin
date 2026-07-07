import { useRouter } from 'vue-router';
import type { RouteLocationRaw } from 'vue-router';
import type { RouteKey } from '@elegant-router/types';
import { router as globalRouter } from '@/router';
import { useRouteStore } from '@/store/modules/route';
import { getFirstMenuRouteKey } from '@/store/modules/route/shared';

/**
 * Router push
 *
 * Jump to the specified route, it can replace function router.push
 *
 * @param inSetup Whether is in vue script setup
 */
export function useRouterPush(inSetup = true) {
  const router = inSetup ? useRouter() : globalRouter;
  const route = globalRouter.currentRoute;

  const routerPush = router.push;

  const routerBack = router.back;

  async function routerPushByKey(key: RouteKey, options?: App.Global.RouterPushOptions) {
    const { query, params } = options || {};

    const routeLocation: RouteLocationRaw = {
      name: key
    };

    if (Object.keys(query || {}).length) {
      routeLocation.query = query;
    }

    if (Object.keys(params || {}).length) {
      routeLocation.params = params;
    }

    return routerPush(routeLocation);
  }

  function routerPushByKeyWithMetaQuery(key: RouteKey) {
    const allRoutes = router.getRoutes();
    const meta = allRoutes.find(item => item.name === key)?.meta || null;

    const query: Record<string, string> = {};

    meta?.query?.forEach(item => {
      query[item.key] = item.value;
    });

    return routerPushByKey(key, { query });
  }

  async function toHome() {
    return routerPushByKey('root');
  }

  /**
   * Navigate to login page
   *
   * @param loginModule The login module
   */
  async function toLogin(loginModule?: UnionKey.LoginModule) {
    const module = loginModule || 'pwd-login';

    const options: App.Global.RouterPushOptions = {
      params: {
        module
      }
    };

    return routerPushByKey('login', options);
  }

  /**
   * Toggle login module
   *
   * @param module
   */
  async function toggleLoginModule(module: UnionKey.LoginModule) {
    const query = route.value.query as Record<string, string>;

    return routerPushByKey('login', { query, params: { module } });
  }

  /**
   * Redirect from login
   *
   * Navigate **by route name** to the first accessible menu in the user's
   * permission list (skipping the `home` dashboard). Name-based navigation
   * resolves directly to the registered route, so it never falls through to
   * `/home` (which 404s for accounts without home permission). Falls back to
   * `toHome()` only when there are no menus.
   *
   * @param [needRedirect=true] Whether to redirect after login. Default is `true`
   */
  async function redirectFromLogin(needRedirect = true) {
    // [temporarily disabled] redirect back to the originally requested route
    // (the `redirect` query param is ignored).
    void needRedirect;

    // menus are not loaded yet at this point; ensure auth routes are initialized
    // so we can pick the first accessible menu as the landing page.
    const routeStore = useRouteStore();
    await routeStore.initAuthRoute();

    const firstMenuRouteKey = getFirstMenuRouteKey(routeStore.menus);

    if (firstMenuRouteKey) {
      await routerPushByKey(firstMenuRouteKey);
      return;
    }

    await toHome();
  }

  return {
    routerPush,
    routerBack,
    routerPushByKey,
    routerPushByKeyWithMetaQuery,
    toLogin,
    toggleLoginModule,
    redirectFromLogin
  };
}
