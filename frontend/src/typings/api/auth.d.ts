declare namespace Api {
  /**
   * namespace Auth
   *
   * backend api module: "auth"
   */
  namespace Auth {
    interface LoginToken {
      access_token: string;
      token_type: string;
      expires_in: number;
      refresh_token: string;
    }

    interface UserInfo {
      id: number;
      username: string;
      nickname: string;
      email: string | null;
      phone: string | null;
      avatar: string | null;
      is_superuser: boolean;
      status: boolean;
      last_login_at: string | null;
      last_login_ip: string | null;
      roles: string[];
      buttons: string[];
    }

    interface CaptchaImageData {
      captcha_id: string;
      background_image: string;
      puzzle_image: string;
      puzzle_y: number;
      slider_width: number;
    }

    interface CaptchaVerifyResponse {
      captcha_token: string;
    }

    interface CaptchaCheckResponse {
      required: boolean;
      fail_count: number;
    }
  }
}
