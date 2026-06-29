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
  }
}
