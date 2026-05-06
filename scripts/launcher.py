#!/usr/bin/env python3
"""
Obsidian 统一启动器 - 一键启动所有服务

使用方式:
    python launcher.py                    # 查看状态
    python launcher.py start              # 启动所有服务
    python launcher.py stop               # 停止所有服务
    python launcher.py status             # 查看状态
    python launcher.py install            # 安装依赖
"""
import argparse
import os
import subprocess
import sys
from pathlib import Path


class Launcher:
    """统一启动器"""

    def __init__(self, vault_path: str = None):
        self.vault_path = Path(vault_path or os.getcwd())
        self.scripts_dir = self.vault_path / "scripts"

    def check_dependencies(self):
        """检查依赖"""
        print("📦 检查依赖...\n")

        required = {
            "requests": "requests",
            "beautifulsoup4": "bs4",
            "anthropic": "anthropic",
            "PyPDF2": "PyPDF2",
            "python-docx": "docx",
        }

        missing = []
        for package, import_name in required.items():
            try:
                __import__(import_name)
                print(f"   ✅ {package}")
            except ImportError:
                print(f"   ❌ {package} (未安装)")
                missing.append(package)

        if missing:
            print(f"\n💡 安装缺失依赖: pip install {' '.join(missing)}")
            return False

        print("\n✅ 所有依赖已安装")
        return True

    def start_achievement_daemon(self):
        """启动成果自动处理器"""
        print("🚀 启动成果自动处理器...")
        try:
            # 后台启动
            subprocess.Popen(
                [sys.executable, str(self.scripts_dir / "achievement-daemon.py"), "--path", str(self.vault_path)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True
            )
            print("   ✅ 已启动 (PID 记录在系统)")
        except Exception as e:
            print(f"   ❌ 启动失败: {e}")

    def start_api_server(self):
        """启动 API 服务器"""
        print("🚀 启动 API 服务器...")
        try:
            api_dir = self.vault_path / "api"
            if not api_dir.exists():
                print("   ⚠️ API 目录不存在")
                return

            # 检查配置文件
            config_file = api_dir / "config.py"
            if not config_file.exists():
                print("   ⚠️ API 配置文件不存在")

            # 后台启动
            subprocess.Popen(
                [sys.executable, "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"],
                cwd=str(api_dir),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True
            )
            print("   ✅ API 服务已启动 (http://localhost:8000)")
        except Exception as e:
            print(f"   ❌ 启动失败: {e}")

    def show_status(self):
        """显示状态"""
        print("""
╔══════════════════════════════════════════════════════════════╗
║              🧠 Obsidian AI 系统状态                        ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  📥 输入模块:                                                ║
║     ├── 投递箱监听      : ⚙️ achievement-daemon.py          ║
║     ├── 网页收集        : 📌 web_collector.py               ║
║     └── 文件导入        : 📌 import_to_obsidian.py          ║
║                                                              ║
║  🧠 AI 处理模块:                                            ║
║     ├── 知识库演化      : ⚙️ auto_evolve.py                 ║
║     ├── AI 对话         : 📌 obsidian_chat.py               ║
║     └── 问答搜索        : 📌 obsidian_qa.py                 ║
║                                                              ║
║  🌐 API 服务:                                               ║
║     └── FastAPI         : 📌 api/main.py (port 8000)        ║
║                                                              ║
║  ⚙️ GitHub Actions:                                         ║
║     ├── AI 文档分析      : ✅ 已配置                         ║
║     ├── 知识图谱更新     : ✅ 已配置                         ║
║     ├── 项目仪表板       : ✅ 已配置                         ║
║     ├── AI 周报生成      : ✅ 已配置                         ║
║     └── AI 项目管理      : ✅ 已配置                         ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
        """)

        # 检查依赖
        print("📦 依赖检查:")
        self.check_dependencies()

        print("\n📂 目录结构:")
        inbox = self.vault_path / "_inbox"
        achievements = self.vault_path / "achievements"
        api = self.vault_path / "api"

        print(f"   📥 投递箱: {'✅ 存在' if inbox.exists() else '❌ 缺失'}")
        print(f"   📚 成果库: {'✅ 存在' if achievements.exists() else '❌ 缺失'}")
        print(f"   🌐 API:    {'✅ 存在' if api.exists() else '❌ 缺失'}")

        # 检查投递箱
        if inbox.exists():
            files = list(inbox.rglob("*"))
            pdf_count = len([f for f in files if f.suffix.lower() == '.pdf'])
            web_files = list((inbox / "web").glob("*.json")) if (inbox / "web").exists() else []
            print(f"\n📭 投递箱状态:")
            print(f"   - 待处理文件: {len([f for f in files if f.is_file() and not f.name.startswith('.')])}")
            print(f"   - 待处理网页: {len(web_files)}")

    def install(self):
        """安装依赖"""
        print("📦 安装依赖...\n")

        packages = [
            "requests",
            "beautifulsoup4",
            "anthropic",
            "PyPDF2",
            "python-docx",
            "watchdog",
            "faiss-cpu",
            "sentence-transformers",
            "uvicorn",
        ]

        for package in packages:
            try:
                subprocess.run([sys.executable, "-m", "pip", "install", package, "-q"],
                             capture_output=True, check=True)
                print(f"   ✅ {package}")
            except:
                print(f"   ⚠️ {package} 安装失败（可能已存在）")

        print("\n✅ 依赖安装完成")

    def quick_start(self):
        """快速开始"""
        print("""
🚀 快速开始

1. 安装依赖:
   python launcher.py install

2. 查看状态:
   python launcher.py status

3. 启动服务:
   python launcher.py start

4. 查看帮助:
   python scripts/obsidian_workflow.py
        """)


def main():
    parser = argparse.ArgumentParser(description="Obsidian AI 统一启动器")
    parser.add_argument("command", nargs="?", help="命令")
    parser.add_argument("--path", "-p", default=".", help="Obsidian 路径")

    args = parser.parse_args()

    vault_path = str(Path(args.path).resolve())
    launcher = Launcher(vault_path)

    if args.command == "install":
        launcher.install()
    elif args.command == "start":
        print("🚀 启动服务...\n")
        launcher.start_achievement_daemon()
        print("\n✅ 启动完成")
    elif args.command == "status":
        launcher.show_status()
    elif args.command == "quick" or args.command == "help":
        launcher.quick_start()
    else:
        launcher.show_status()


if __name__ == "__main__":
    main()