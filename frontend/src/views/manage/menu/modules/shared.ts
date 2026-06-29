const LAYOUT_PREFIX = 'layout.';
const VIEW_PREFIX = 'view.';
const FIRST_LEVEL_ROUTE_COMPONENT_SPLIT = '$';

export function getLayoutAndPage(component?: string | null) {
  let layout = '';
  let page = '';

  const [layoutOrPage = '', pageItem = ''] = component?.split(FIRST_LEVEL_ROUTE_COMPONENT_SPLIT) || [];

  layout = getLayout(layoutOrPage);
  page = getPage(pageItem || layoutOrPage);

  return { layout, page };
}

function getLayout(layout: string) {
  return layout.startsWith(LAYOUT_PREFIX) ? layout.replace(LAYOUT_PREFIX, '') : '';
}

function getPage(page: string) {
  return page.startsWith(VIEW_PREFIX) ? page.replace(VIEW_PREFIX, '') : '';
}

export function transformLayoutAndPageToComponent(layout: string, page: string) {
  const hasLayout = Boolean(layout);
  const hasPage = Boolean(page);

  if (hasLayout && hasPage) {
    return `${LAYOUT_PREFIX}${layout}${FIRST_LEVEL_ROUTE_COMPONENT_SPLIT}${VIEW_PREFIX}${page}`;
  }

  if (hasLayout) {
    return `${LAYOUT_PREFIX}${layout}`;
  }

  if (hasPage) {
    return `${VIEW_PREFIX}${page}`;
  }

  return '';
}

/**
 * Get route name by route path
 *
 * @param routeName
 */
export function getRoutePathByRouteName(routeName: string) {
  return `/${routeName.replace(/_/g, '/')}`;
}

/**
 * 取路由名的末段（按 `_` 拆分），如 manage_ip-blacklist → ip-blacklist
 *
 * @param routeName 路由名
 */
export function getLastSegmentByName(routeName: string) {
  const segment = routeName.split('_').pop();
  return segment || routeName;
}

/**
 * 取完整路径的末段，如 /manage/face → face
 *
 * @param fullPath 完整路由路径
 */
export function getLastPathSegment(fullPath: string) {
  const segment = fullPath.split('/').filter(Boolean).pop();
  return segment || '';
}

/**
 * 由父级路径前缀与自身段拼接完整路径。
 * 如 ('/manage', 'face') → '/manage/face'；('', 'monitor') → '/monitor'
 *
 * @param prefix 父级目录的完整路径（无父级时传空串）
 * @param segment 当前菜单自身的路径段
 */
export function composePath(prefix: string, segment: string) {
  const cleanPrefix = (prefix || '').replace(/\/+$/, '');
  const cleanSegment = (segment || '').replace(/^\/+|\/+$/g, '');
  if (!cleanSegment) return cleanPrefix || '/';
  return cleanPrefix ? `${cleanPrefix}/${cleanSegment}` : `/${cleanSegment}`;
}
