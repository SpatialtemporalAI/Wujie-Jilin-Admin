declare namespace Api {
  /**
   * namespace Merchant
   *
   * 商户管理 + 商户开放 API
   */
  namespace Merchant {
    type CommonSearchParams = Pick<Common.PaginatingCommonParams, 'page' | 'page_size'>;

    /** merchant */
    type Merchant = Common.CommonRecord<{
      /** merchant name */
      name: string;
      /** merchant code */
      code: string;
      /** contact name */
      contact_name: string | null;
      /** contact phone */
      contact_phone: string | null;
      /** contact email */
      contact_email: string | null;
      /** api key (non-secret, used for routing) */
      api_key: string;
      /** remark */
      remark: string | null;
    }>;

    /** merchant search params */
    type MerchantSearchParams = CommonType.RecordNullable<
      Pick<Merchant, 'name' | 'code' | 'status'> & CommonSearchParams
    >;

    /** merchant list */
    type MerchantList = Common.PaginatingQueryRecord<Merchant>;

    /** merchant detail (with bound robot ids) */
    type MerchantDetail = Merchant & {
      /** bound robot ids */
      robot_ids: number[];
    };

    /** merchant create */
    type MerchantCreate = {
      name: string;
      code: string;
      contact_name?: string | null;
      contact_phone?: string | null;
      contact_email?: string | null;
      status: Common.EnableStatus;
      remark?: string | null;
      /** bound robot ids */
      robot_ids?: number[];
    };

    /** merchant update */
    type MerchantUpdate = Partial<MerchantCreate>;

    /** api credentials (api_secret plaintext, returned only on create/reset) */
    type ApiCredentials = {
      id: number;
      api_key: string;
      api_secret: string;
    };

    /** merchant openapi call log */
    type CallLog = {
      id: number;
      merchant_id: number | null;
      merchant_name: string | null;
      merchant_code: string | null;
      api_key_masked: string | null;
      method: string | null;
      path: string | null;
      action: string | null;
      ip: string | null;
      response_code: number | null;
      success: boolean | null;
      elapsed_ms: number | null;
      error_msg: string | null;
      created_at: string | null;
    };

    /** merchant call log detail (with sanitized params/result) */
    type CallLogDetail = CallLog & {
      request_params: string | null;
      response_result: string | null;
    };

    /** merchant call log search params */
    type CallLogSearchParams = CommonType.RecordNullable<
      {
        merchant_id?: number;
        action?: string;
        success?: boolean;
        api_key?: string;
        start_time?: string;
        end_time?: string;
      } & CommonSearchParams
    >;

    /** merchant call log list */
    type CallLogList = Common.PaginatingQueryRecord<CallLog>;
  }
}
