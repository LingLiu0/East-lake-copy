#!/usr/bin/env python3
"""
Obsidian 系统诊断工具
检查所有组件状态，生成诊断报告
"""
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path


class Diagnoser:
    """系统诊断器"""

    def __init__(self, vault_path: str = None):
        self.vault_path = Path(vault_path or os.getcwd())
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "vault_path": str(self.vault_path),
            "issues": [],
            "warnings": [],
            "info": [],
        }

    def check_all(self):
        """检查所有组件"""
        print("🔍 开始系统诊断...\n")

        self.check_directories()
        self.check_scripts()
        self.check_workflows()
        self.check_dependencies()
        self.check_configuration()

        self.generate_report()

        return self.results

    def check_directories(self):
        """检查目录结构"""
        print("📂 检查目录...")

        required_dirs = {
            "_inbox": "投递箱",
            "_inbox/web": "网页收集箱",
            "achievements": "成果库",
            "scripts": "脚本目录",
            "api": "API服务",
            ".obsidian": "Obsidian配置",
            ".github/workflows": "GitHub Actions",
        }

        for dir_name, desc in required_dirs.items():
            path = self.vault_path / dir_name
            if path.exists():
                file_count = len(list(path.rglob("*")))
                print(f"   ✅ {dir_name}: {file_count} 个文件")
            else:
                print(f"   ❌ {dir_name}: 不存在")
                self.results["issues"].append(f"目录 {dir_name} 不存在")

    def check_scripts(self):
        """检查脚本"""
        print("\n📜 检查脚本...")

        scripts = [
            "obsidian_workflow.py",
            "obsidian_chat.py",
            "obsidian_qa.py",
            "achievement_manager.py",
            "achievement-daemon.py",
            "web_collector.py",
            "import_to_obsidian.py",
            "auto_evolve.py",
            "embeddings.py",
        ]

        for script in scripts:
            path = self.vault_path / "scripts" / script
            if path.exists():
                size = path.stat().st_size
                print(f"   ✅ {script} ({size/1024:.1f} KB)")
            else:
                print(f"   ⚠️ {script}: 不存在")
                self.results["warnings"].append(f"脚本 {script} 不存在")

    def check_workflows(self):
        """检查 GitHub Actions"""
        print("\n⚙️ 检查 Workflows...")

        workflows_dir = self.vault_path / ".github" / "workflows"
        if not workflows_dir.exists():
            print("   ⚠️ Workflows 目录不存在")
            return

        workflows = list(workflows_dir.glob("*.yml")) + list(workflows_dir.glob("*.yaml"))
        print(f"   找到 {len(workflows)} 个 Workflows:")

        for wf in workflows:
            print(f"   ✅ {wf.name}")

    def check_dependencies(self):
        """检查依赖"""
        print("\n📦 检查 Python 依赖...")

        required = {
            "requests": "requests",
            "beautifulsoup4": "bs4",
            "anthropic": "anthropic",
            "PyPDF2": "PyPDF2",
        }

        for package, import_name in required.items():
            try:
                __import__(import_name)
                print(f"   ✅ {package}")
            except ImportError:
                print(f"   ❌ {package} (未安装)")
                self.results["issues"].append(f"缺少依赖: {package}")

    def check_configuration(self):
        """检查配置文件"""
        print("\n⚙️ 检查配置...")

        config_files = [
            ".obsidian/ai-config.json",
            ".obsidian/achievement-config.json",
            "api/config.py",
        ]

        for config in config_files:
            path = self.vault_path / config
            if path.exists():
                print(f"   ✅ {config}")
            else:
                print(f"   ⚠️ {config}: 不存在（可选）")

    def generate_report(self):
        """生成报告"""
        print("\n" + "=" * 50)
        print("📊 诊断报告")
        print("=" * 50)

        if self.results["issues"]:
            print(f"\n❌ 发现 {len(self.results['issues'])} 个问题:")
            for issue in self.results["issues"]:
                print(f"   - {issue}")

        if self.results["warnings"]:
            print(f"\n⚠️  发现 {len(self.results['warnings'])} 个警告:")
            for warning in self.results["warnings"]:
                print(f"   - {warning}")

        if not self.results["issues"] and not self.results["warnings"]:
            print("\n✅ 系统状态良好！")

        print(f"\n📅 诊断时间: {self.results['timestamp']}")

        # 建议
        print("\n💡 建议操作:")
        if not self.results["issues"]:
            print("   - 运行 'python scripts/launcher.py start' 启动服务")
            print("   - 运行 'python scripts/achievement_manager.py --process' 处理投递箱")
        else:
            print("   - 安装依赖: pip install requests beautifulsoup4 anthropic PyPDF2")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Obsidian 系统诊断")
    parser.add_argument("--path", "-p", default=".", help="Obsidian 路径")
    args = parser.parse_args()

    vault_path = str(Path(args.path).resolve())
    diagnoser = Diagnoser(vault_path)
    diagnoser.check_all()


if __name__ == "__main__":
    main()