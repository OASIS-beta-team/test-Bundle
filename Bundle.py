#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import ast
import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
inlined = set()
ANNOTATE = True


def find_module_path(module_name):
    candidate = os.path.join(PROJECT_ROOT, module_name.replace('.', os.sep) + '.py')
    if os.path.isfile(candidate):
        return candidate
    return None


def inline_file(path):
    code = []
    with open(path, encoding='utf-8') as f:
        source = f.read()
    tree = ast.parse(source, filename=path)

    for node in tree.body:
        if isinstance(node, ast.Import):
            for alias in node.names:
                mod = alias.name
                mp = find_module_path(mod)
                if mp and mp not in inlined:
                    inlined.add(mp)
                    if ANNOTATE:
                        code.append(f"# --- begin inline import {mod} from {mp} ---\n")
                    code.append(inline_file(mp))
                    if ANNOTATE:
                        code.append(f"# --- end inline import {mod} ---\n")
                else:
                    code.append(ast.get_source_segment(source, node) + "\n")

        elif isinstance(node, ast.ImportFrom):
            if node.level == 0 and node.module:
                mod = node.module
                mp = find_module_path(mod)
                if mp and mp not in inlined:
                    inlined.add(mp)
                    names_list = ", ".join(alias.name for alias in node.names)
                    if ANNOTATE:
                        code.append(f"# --- begin inline from {mod} import {names_list} ---\n")
                    code.append(inline_file(mp))
                    if ANNOTATE:
                        code.append(f"# --- end inline from {mod} ---\n")
                else:
                    code.append(ast.get_source_segment(source, node) + "\n")
            else:
                code.append(ast.get_source_segment(source, node) + "\n")

        else:
            snippet = ast.get_source_segment(source, node)
            code.append(snippet + ("\n" if not snippet.endswith("\n") else ""))

    return "".join(code)


def bundle(main_path, output_path):
    abs_main = os.path.join(PROJECT_ROOT, main_path)
    if not os.path.isfile(abs_main):
        print(f"未找到入口文件：{abs_main}", file=sys.stderr)
        sys.exit(1)

    inlined.clear()

    bundled_code = []
    bundled_code.append("# -*- coding: utf-8 -*-\n")
    bundled_code.append(f"# Bundled by {os.path.basename(__file__)}\n\n")

    bundled_code.append(inline_file(abs_main))

    with open(os.path.join(PROJECT_ROOT, output_path), 'w', encoding='utf-8') as fw:
        fw.write("".join(bundled_code))
    print(f"✅ 成功生成合并文件：{output_path}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="将 Python 多文件项目打包为单个文件")
    parser.add_argument("main", nargs="?", default="main.py", help="主入口文件")
    parser.add_argument("output", nargs="?", default="output.py", help="输出文件名")
    parser.add_argument("--no-annotate", action="store_true", help="关闭内联注释")

    args = parser.parse_args()
    ANNOTATE = not args.no_annotate

    bundle(args.main, args.output)
