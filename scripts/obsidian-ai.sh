#!/bin/bash
#
# Obsidian AI 工作流 - macOS/Linux 命令行工具
#
# 安装方法:
# 1. 将此文件复制到 /usr/local/bin/obsidian-ai
# 2. chmod +x /usr/local/bin/obsidian-ai
# 3. 或者直接在项目目录运行 ./obsidian-ai.sh
#
# 使用:
#   obsidian-ai achieve in        # 查看投递箱
#   obsidian-ai achieve process   # 处理文件
#   obsidian-ai ask "问题"
#   obsidian-ai chat

# 配置
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PYTHON="python3"

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到 python3"
    exit 1
fi

# 检查参数
if [ $# -lt 1 ]; then
    echo "Obsidian AI 工作流 v2.0"
    echo ""
    echo "📥 成果管理（团队使用）:"
    echo "  achieve in        查看投递箱"
    echo "  achieve process   处理投递箱"
    echo "  achieve watch     监听模式（自动处理）"
    echo "  achieve status    查看状态"
    echo ""
    echo "🧠 知识管理:"
    echo "  ask <问题>        向知识库提问"
    echo "  chat              交互式对话"
    echo "  import <文件>     导入文件"
    echo "  evolve            知识库自动演化"
    echo "  dashboard         统计信息"
    echo ""
    exit 0
fi

COMMAND=$1
shift

case $COMMAND in
    # ===== 成果管理 =====
    achieve|achievement|a)
        SUBCMD=$1
        shift

        case $SUBCMD in
            in|inbox|i)
                $PYTHON "$SCRIPT_DIR/achievement_manager.py" --inbox
                ;;
            process|run|p)
                $PYTHON "$SCRIPT_DIR/achievement_manager.py" --process
                ;;
            watch|daemon|w)
                $PYTHON "$SCRIPT_DIR/achievement_manager.py" --watch "$@"
                ;;
            status|stat|s)
                $PYTHON "$SCRIPT_DIR/achievement_manager.py" --status
                ;;
            revert|r)
                $PYTHON "$SCRIPT_DIR/achievement_manager.py" --revert "$1"
                ;;
            *)
                echo "📥 成果管理命令:"
                echo "  in        - 查看投递箱"
                echo "  process   - 处理文件"
                echo "  watch     - 监听模式"
                echo "  status    - 查看状态"
                echo "  revert    - 撤销处理"
                ;;
        esac
        ;;

    # ===== 知识管理 =====
    ask|q)
        $PYTHON "$SCRIPT_DIR/obsidian_chat.py" "$@"
        ;;
    chat|c)
        $PYTHON "$SCRIPT_DIR/obsidian_chat.py" --interactive
        ;;
    import|im)
        $PYTHON "$SCRIPT_DIR/import_to_obsidian.py" "$@"
        ;;
    batch|b)
        $PYTHON "$SCRIPT_DIR/import_to_obsidian.py" --batch "$@"
        ;;
    evolve|e)
        $PYTHON "$SCRIPT_DIR/auto_evolve.py" --once
        ;;
    gaps|g)
        $PYTHON "$SCRIPT_DIR/obsidian_qa.py" --gaps
        ;;
    dashboard|d|stats)
        $PYTHON "$SCRIPT_DIR/obsidian_qa.py" --summary
        ;;
    search|s)
        $PYTHON "$SCRIPT_DIR/obsidian_qa.py" "$@"
        ;;

    # ===== 帮助 =====
    help|--help|-h)
        echo "Obsidian AI 工作流"
        echo ""
        echo "📥 成果管理:"
        echo "  $(basename $0) achieve in        # 查看投递箱"
        echo "  $(basename $0) achieve process   # 处理文件"
        echo "  $(basename $0) achieve watch     # 自动处理"
        echo ""
        echo "🧠 知识管理:"
        echo "  $(basename $0) ask \"问题\"        # 提问"
        echo "  $(basename $0) chat              # 对话"
        echo "  $(basename $0) import <文件>     # 导入"
        echo "  $(basename $0) evolve            # 演化"
        echo "  $(basename $0) dashboard         # 统计"
        ;;

    *)
        echo "未知命令: $COMMAND"
        echo "运行 '$(basename $0) help' 查看帮助"
        exit 1
        ;;
esac