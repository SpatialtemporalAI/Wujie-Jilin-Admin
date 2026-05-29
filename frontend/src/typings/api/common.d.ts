/**
 * Namespace Api
 *
 * All backend api type
 */
declare namespace Api {
  /** operate type */
  type OperateType = 'add' | 'edit' | 'delete' | 'view';

  namespace Common {
    /** common params of paginating */
    interface PaginatingCommonParams {
      /** current page number */
      page: number;
      /** page size */
      page_size: number;
      /** total count */
      total: number;
      /** total page count */
      total_pages: number;
    }

    /** common params of paginating query list data */
    interface PaginatingQueryRecord<T = any> extends PaginatingCommonParams {
      records: T[];
    }

    /** common search params of table */
    type CommonSearchParams = Pick<Common.PaginatingCommonParams, 'page' | 'page_size'>;

    /**
     * enable status
     *
     * - "1": enabled
     * - "2": disabled
     */
    type EnableStatus = '1' | '2';

    /** common record */
    type CommonRecord<T = any> = {
      /** record id */
      id: number;
      /** record creator */
      created_by: string;
      /** record create time */
      created_at: string;
      /** record updater */
      updated_by: string;
      /** record update time */
      updated_at: string;
      /** record status */
      status: EnableStatus | null;
    } & T;
  }
}
