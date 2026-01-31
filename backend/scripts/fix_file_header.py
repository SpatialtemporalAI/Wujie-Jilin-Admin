#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件头修复脚本
用于为项目中所有Python文件添加标准文件头
"""
import os
import re
import argparse


def main():
    """
    主函数，遍历所有Python文件并添加标准文件头
    """
    # 定义项目根目录
    project_root = "d:/project/SmileX/SmileX-Fastapi-Cloud"

    # 排除的目录
    excluded_dirs = [".venv", "alembic"]

    # 标准文件头
    standard_header = "#!/usr/bin/env python3\n# -*- coding: utf-8 -*-\n"

    # 文件计数
    total_files = 0
    modified_files = 0

    # 遍历项目目录
    for root, dirs, files in os.walk(project_root):
        # 跳过排除的目录
        dirs[:] = [d for d in dirs if d not in excluded_dirs]

        # 处理每个Python文件
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                total_files += 1

                # 读取文件内容
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                except Exception as e:
                    print(f"读取文件 {file_path} 失败: {e}")
                    continue

                # 检查文件头
                has_shebang = content.startswith("#!/usr/bin/env python3")
                has_encoding = "# -*- coding: utf-8 -*-" in content[:100]

                # 如果缺少其中之一，需要添加
                if not has_shebang or not has_encoding:
                    # 构建新内容
                    new_content = standard_header

                    # 如果有shebang但没有编码，或者有编码但没有shebang，需要重新构建
                    if content.strip():
                        # 移除已有的shebang和编码行
                        lines = content.splitlines()
                        cleaned_lines = []
                        found_header = False

                        for line in lines:
                            if line.strip() in [
                                "#!/usr/bin/env python3",
                                "# -*- coding: utf-8 -*-",
                            ]:
                                if not found_header:
                                    found_header = True
                                continue
                            if found_header and not line.strip():
                                continue
                            cleaned_lines.append(line)
                            found_header = True

                        # 添加清理后的内容
                        if cleaned_lines:
                            new_content += "\n" + "\n".join(cleaned_lines)

                    # 写入新内容
                    try:
                        with open(file_path, "w", encoding="utf-8") as f:
                            f.write(new_content)
                        modified_files += 1
                        print(f"已为文件 {file_path} 添加标准文件头")
                    except Exception as e:
                        print(f"写入文件 {file_path} 失败: {e}")
                    continue

                # 如果文件头正确，跳过
                print(f"文件 {file_path} 已包含完整的标准文件头")

    # 输出统计信息
    print(f"\n处理完成!")
    print(f"总文件数: {total_files}")
    print(f"修改文件数: {modified_files}")


if __name__ == "__main__":
    main()
