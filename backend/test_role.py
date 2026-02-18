#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json

# 测试创建角色接口
def test_create_role():
    url = "http://localhost:8000/admin/sys/role/add"
    data = {
        "name": "测试角色",
        "code": "test_role",
        "description": "测试角色描述",
        "status": True,
        "sort": 0,
        "menu_ids": []
    }
    
    response = requests.post(url, json=data)
    print("Status Code:", response.status_code)
    print("Response:", json.dumps(response.json(), ensure_ascii=False, indent=2))

if __name__ == "__main__":
    test_create_role()
