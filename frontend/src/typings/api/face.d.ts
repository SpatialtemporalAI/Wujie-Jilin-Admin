declare namespace Api {
  /**
   * namespace Face
   *
   * 阿里云人脸库管理（facebody）
   */
  namespace Face {
    /** 人脸库名称列表 */
    type FaceDbList = string[];

    /** 人脸实体（列表项） */
    type FaceEntity = {
      /** 实体标识 */
      entity_id: string;
      /** 所属人脸库名称 */
      db_name: string;
      /** 人脸图片数量 */
      face_count: number;
      /** 标签 */
      labels?: string | null;
      /** 创建时间 */
      created_at?: string | null;
      /** 更新时间 */
      updated_at?: string | null;
    };

    /** 实体分页查询参数 */
    type FaceEntitySearchParams = Common.CommonSearchParams & {
      db_name: string;
    };

    /** 实体分页列表 */
    type FaceEntityList = Common.PaginatingQueryRecord<FaceEntity>;

    /** 实体下的人脸图片 */
    type FaceEntityFace = {
      face_id: string;
    };

    /** 实体详情（含人脸图片列表） */
    type FaceEntityDetail = {
      db_name: string;
      entity_id: string;
      labels?: string | null;
      faces: FaceEntityFace[];
    };

    /** 人脸图片入库结果 */
    type FaceImageAddResult = {
      db_name: string;
      entity_id: string;
      face_id: string;
    };

    /** 搜索匹配项 */
    type FaceSearchItem = {
      entity_id: string;
      confidence: number;
    };

    /** 搜索结果 */
    type FaceSearchResult = {
      results: FaceSearchItem[];
    };

    /** 搜索参数（库 + 文件 + 数量上限） */
    type FaceSearchParams = {
      db_name: string;
      file: File;
      limit: number;
    };

    /** 检测项 */
    type FaceDetectItem = {
      /** 人脸框 [x, y, width, height] */
      face_rect: number[];
      /** 人脸概率 */
      face_probability: number;
    };

    /** 检测结果 */
    type FaceDetectResult = {
      results: FaceDetectItem[];
    };

    /** 检测参数（文件 + 最大人脸数） */
    type FaceDetectParams = {
      file: File;
      max_face_num: number;
    };
  }
}
