import { request } from '../request';

/** ==================== 通知管理 API（管理端） ==================== */

/** get notice list */
export function fetchGetNoticeList(params?: Api.Notification.NoticeSearchParams) {
  return request<Api.Notification.NoticeList>({
    url: '/admin/sys/notice/list',
    method: 'get',
    params
  });
}

/** get notice by id */
export function fetchGetNotice(noticeId: number) {
  return request<Api.Notification.Notice>({
    url: `/admin/sys/notice/${noticeId}`,
    method: 'get'
  });
}

/** create notice */
export function fetchCreateNotice(notice: Api.Notification.NoticeCreate) {
  return request<Api.Notification.Notice>({
    url: '/admin/sys/notice/add',
    method: 'post',
    data: notice
  });
}

/** update notice */
export function fetchUpdateNotice(noticeId: number, notice: Api.Notification.NoticeUpdate) {
  return request<Api.Notification.Notice>({
    url: `/admin/sys/notice/${noticeId}`,
    method: 'put',
    data: notice
  });
}

/** delete notice */
export function fetchDeleteNotice(noticeId: number) {
  return request<void>({
    url: `/admin/sys/notice/${noticeId}`,
    method: 'delete'
  });
}

/** batch delete notices */
export function fetchBatchDeleteNotice(noticeIds: number[]) {
  return request<void>({
    url: '/admin/sys/notice/batch',
    method: 'delete',
    data: noticeIds
  });
}

/** publish notice */
export function fetchPublishNotice(noticeId: number) {
  return request<Api.Notification.Notice>({
    url: `/admin/sys/notice/${noticeId}/publish`,
    method: 'post'
  });
}

/** ==================== 我的通知 API（接收端） ==================== */

/** get my notice list */
export function fetchGetMyNoticeList(params?: Api.Notification.MyNoticeSearchParams) {
  return request<Api.Notification.MyNoticeList>({
    url: '/admin/sys/notice/my/list',
    method: 'get',
    params
  });
}

/** get unread count */
export function fetchGetUnreadCount() {
  return request<number>({
    url: '/admin/sys/notice/my/unread-count',
    method: 'get'
  });
}

/** mark notice as read */
export function fetchMarkAsRead(noticeId: number) {
  return request<void>({
    url: `/admin/sys/notice/my/${noticeId}/read`,
    method: 'put'
  });
}

/** mark all as read */
export function fetchMarkAllAsRead() {
  return request<void>({
    url: '/admin/sys/notice/my/read-all',
    method: 'put'
  });
}
