import { request } from '../request';

/** 人脸库列表 */
export function fetchGetFaceDbList() {
  return request<Api.Face.FaceDbList>({
    url: '/face/db/list',
    method: 'get'
  });
}

/** 创建人脸库 */
export function fetchCreateFaceDb(dbName: string) {
  return request<{ db_name: string }>({
    url: '/face/db',
    method: 'post',
    data: { db_name: dbName }
  });
}

/** 实体分页列表 */
export function fetchGetFaceEntityList(params: Api.Face.FaceEntitySearchParams) {
  return request<Api.Face.FaceEntityList>({
    url: '/face/entity/list',
    method: 'get',
    params
  });
}

/** 实体详情（含人脸图片） */
export function fetchGetFaceEntityDetail(dbName: string, entityId: string) {
  return request<Api.Face.FaceEntityDetail>({
    url: '/face/entity/detail',
    method: 'get',
    params: { db_name: dbName, entity_id: entityId }
  });
}

/** 新增实体 */
export function fetchAddFaceEntity(dbName: string, entityId: string) {
  return request<void>({
    url: '/face/entity',
    method: 'post',
    data: { db_name: dbName, entity_id: entityId }
  });
}

/** 删除实体 */
export function fetchDeleteFaceEntity(dbName: string, entityId: string) {
  return request<void>({
    url: '/face/entity',
    method: 'delete',
    params: { db_name: dbName, entity_id: entityId }
  });
}

/** 添加人脸图片（上传文件入库，返回 face_id） */
export function fetchAddFaceImage(dbName: string, entityId: string, file: File) {
  const formData = new FormData();
  formData.append('db_name', dbName);
  formData.append('entity_id', entityId);
  formData.append('file', file);
  return request<Api.Face.FaceImageAddResult>({
    url: '/face/image',
    method: 'post',
    data: formData,
    headers: { 'Content-Type': 'multipart/form-data' }
  });
}

/** 删除人脸图片 */
export function fetchDeleteFaceImage(dbName: string, faceId: string) {
  return request<void>({
    url: '/face/image',
    method: 'delete',
    params: { db_name: dbName, face_id: faceId }
  });
}

/** 人脸搜索（上传图片，返回匹配实体） */
export function fetchSearchFace(data: Api.Face.FaceSearchParams) {
  const formData = new FormData();
  formData.append('db_name', data.db_name);
  formData.append('limit', String(data.limit));
  formData.append('file', data.file);
  return request<Api.Face.FaceSearchResult>({
    url: '/face/search',
    method: 'post',
    data: formData,
    headers: { 'Content-Type': 'multipart/form-data' }
  });
}

/** 人脸检测（上传图片，返回人脸框） */
export function fetchDetectFace(data: Api.Face.FaceDetectParams) {
  const formData = new FormData();
  formData.append('max_face_num', String(data.max_face_num));
  formData.append('file', data.file);
  return request<Api.Face.FaceDetectResult>({
    url: '/face/detect',
    method: 'post',
    data: formData,
    headers: { 'Content-Type': 'multipart/form-data' }
  });
}
