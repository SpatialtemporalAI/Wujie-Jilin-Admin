import { request } from '../request';

/**
 * Login
 *
 * @param userName User name
 * @param password Password
 */
export function fetchLogin(username: string, password: string, captchaToken?: string) {
  return request<Api.Auth.LoginToken>({
    url: '/admin/auth/login',
    method: 'post',
    data: {
      username,
      password,
      ...(captchaToken ? { captcha_token: captchaToken } : {})
    }
  });
}

/** Get user info */
export function fetchGetUserInfo() {
  return request<Api.Auth.UserInfo>({ url: '/admin/auth/users/me' });
}

/**
 * Refresh token
 *
 * @param refreshToken Refresh token
 */
export function fetchRefreshToken(refreshToken: string) {
  return request<Api.Auth.LoginToken>({
    url: '/admin/auth/refreshToken',
    method: 'post',
    data: {
      refreshToken
    }
  });
}

/**
 * return custom backend error
 *
 * @param code error code
 * @param msg error message
 */
export function fetchCustomBackendError(code: string, msg: string) {
  return request({ url: '/admin/auth/error', params: { code, msg } });
}

/** Get slider captcha image */
export function fetchGetCaptcha() {
  return request<Api.Auth.CaptchaImageData>({
    url: '/admin/auth/captcha',
    method: 'get'
  });
}

/** Verify slider captcha position */
export function fetchVerifyCaptcha(captchaId: string, slideX: number) {
  return request<Api.Auth.CaptchaVerifyResponse>({
    url: '/admin/auth/captcha/verify',
    method: 'post',
    data: { captcha_id: captchaId, slide_x: slideX }
  });
}

/** Check if captcha is required */
export function fetchCheckCaptcha() {
  return request<Api.Auth.CaptchaCheckResponse>({ url: '/admin/auth/captcha/check' });
}
