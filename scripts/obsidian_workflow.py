#!/usr/bin/env python3
"""
Obsidian 一键 AI 工作流 - 整合问答、导入、收集的入口脚本
"""
import argparse
import os
import subprocess
import sys
from pathlib import Path


def get_script_dir():
    return Path(__file__).parent


def run_script(script_name: str, args: list = None):
    script_path = get_script_dir() / script_name
    cmd = [sys.executable, str(script_path)]
    if args:
        cmd.extend(args)
    return subprocess.run(cmd, capture_output=False).returncode


def main():
    parser = argparse.ArgumentParser(
        description="Obsidian AI 工作流 - 一站式知识管理",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
可用命令:

  📥 收集功能:
    collect add <URL>      添加网页到收集箱
    collect inbox          查看收集箱
    collect process        处理收集箱中的网页

  📥 成果管理:
    achieve in        查看投递箱
    achieve process   处理投递箱文件
    achieve watch     监听模式（自动处理）

  🧠 知识管理:
    ask <问题>       向知识库提问
    chat             交互式对话
    import <文件>    导入文件
    evolve           知识库自动演化
    dashboard        查看知识库统计

示例:

  # 收集网页
  python obsidian_workflow.py collect add "https://example.com/article"
  python obsidian_workflow.py collect process

  # 团队成果
  python obsidian_workflow.py achieve process

  # 知识管理
  python obsidian_workflow.py ask "什么是 RAG?"
        """
    )

    parser.add_argument("command", nargs="?", help="命令")
    parser.add_argument("subcommand", nargs="?", help="子命令")
    parser.add_argument("argument", nargs="?", help="命令参数")
    parser.add_argument("--path", "-p", default=".", help="Obsidian 路径")
    parser.add_argument("--tags", "-t", help="标签")
    parser.add_argument("--title", help="标题")

    args = parser.parse_args()
    os.chdir(args.path)

    # ==================== 网页收集 ====================
    if args.command == "collect" or args.command == "web":
        if args.subcommand == "add":
            if not args.argument:
                print("错误: 请提供 URL")
                sys.exit(1)
            cmd_args = [args.argument]
            if args.tags:
                cmd_args.extend(["--tags", args.tags])
            if args.title:
                cmd_args.extend(["--title", args.title])
            sys.exit(run_script("web_collector.py", cmd_args))
        elif args.subcommand == "inbox":
            sys.exit(run_script("web_collector.py", ["inbox"]))
        elif args.subcommand == "process":
            sys.exit(run_script("web_collector.py", ["process"]))
        else:
            print("collect add <URL>    - 添加网页")
            print("collect inbox        - 查看收集箱")
            print("collect process      - 处理收集箱")

    # ==================== 成果管理 ====================
    elif args.command == "achieve" or args.command == "achievement":
        if args.subcommand == "in" or args.subcommand == "inbox":
            sys.exit(run_script("achievement_manager.py", ["--inbox"]))
        elif args.subcommand == "process" or args.subcommand == "run":
            sys.exit(run_script("achievement_manager.py", ["--process"]))
        elif args.subcommand == "watch":
            sys.exit(run_script("achievement_manager.py", ["--watch"]))
        elif args.subcommand == "status":
            sys.exit(run_script("achievement_manager.py", ["--status"]))
        else:
            sys.exit(run_script("achievement_manager.py", []))

    # ==================== 知识管理 ====================
    elif args.command == "ask":
        if not args.argument:
            print("错误: 请提供问题")
            sys.exit(1)
        sys.exit(run_script("obsidian_chat.py", [args.argument]))

    elif args.command == "chat":
        sys.exit(run_script("obsidian_chat.py", ["--interactive"]))

    elif args.command == "import":
        if not args.argument:
            print("错误: 请提供文件")
            sys.exit(1)
        sys.exit(run_script("import_to_obsidian.py", [args.argument]))

    elif args.command == "evolve":
        sys.exit(run_script("auto_evolve.py", ["--once"]))

    elif args.command == "dashboard":
        sys.exit(run_script("obsidian_qa.py", ["--summary"]))

    else:
        print("""
╔══════════════════════════════════════════════════════════════╗
║           🧠 Obsidian AI 工作流 v2.1                        ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  🌐 网页收集:                                                ║
║    collect add <URL>      添加网页                           ║
║    collect inbox          查看收集箱                         ║
║    collect process        处理收集箱                         ║
║                                                              ║
║  📥 成果管理（团队）:                                        ║
║    achieve process       处理投递箱                          ║
║    achieve watch         自动监听                            ║
║                                                              ║
║  🧠 知识管理:                                                ║
║    ask <问题>           向知识库提问                         ║
║    chat                  交互式对话                           ║
║    evolve                知识库演化                          ║
║                                                              ╚══════════════════════════════════════════════════════╝
        """)
        parser.print_help()


if __name__ == "__main__":
    main()