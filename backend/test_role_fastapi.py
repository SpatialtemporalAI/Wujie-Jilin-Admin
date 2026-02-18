#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

# 测试创建角色接口
def test_create_role():
    url = "/admin/sys/role/add"
    data = {
        "name": "测试角色",
        "code": "test_role",
        "description": "测试角色描述",
        "status": True,
        "sort": 0,
        "menu_ids": []
    }
    
    response = client.post(url, json=data)
    print("Status Code:", response.status_code)
    print("Response:", response.json())

if __name__ == "__main__":
    test_create_role()
