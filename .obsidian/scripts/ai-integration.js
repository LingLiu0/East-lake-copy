/**
 * Obsidian AI 集成 - QuickAdd/MetaEdit 脚本
 *
 * 安装方法:
 * 1. 将此文件复制到 .obsidian/scripts/ 目录
 * 2. 在 QuickAdd 中配置用户脚本
 * 3. 或者通过 Shell Commands 调用
 */

const { obsidian } = app;

// 配置
const CONFIG = {
    scriptsPath: ".obsidian/scripts/",
    pythonPath: "python", // 或 "python3"
};

// 预定义命令
const COMMANDS = {
    ask: async (query) => {
        if (!query) {
            query = await utils.input("请输入问题:");
        }
        return runPythonScript("obsidian_chat.py", [query]);
    },

    chat: async () => {
        return runPythonScript("obsidian_chat.py", ["--interactive"]);
    },

    import: async (filePath) => {
        if (!filePath) {
            filePath = await utils.input("请输入文件路径:");
        }
        return runPythonScript("import_to_obsidian.py", [filePath]);
    },

    evolve: async () => {
        return runPythonScript("auto_evolve.py", ["--once"]);
    },

    dashboard: async () => {
        return runPythonScript("obsidian_qa.py", ["--summary"]);
    },

    gaps: async () => {
        return runPythonScript("obsidian_qa.py", ["--gaps"]);
    },
};

/**
 * 运行 Python 脚本
 */
async function runPythonScript(scriptName, args = []) {
    const vaultPath = app.vault.adapter.getBasePath();
    const scriptPath = `${vaultPath}/scripts/${scriptName}`;

    const command = [CONFIG.pythonPath, scriptPath, ...args].join(" ");

    new Notice(`🚀 运行: ${scriptName}`);

    try {
        const { stdout, stderr } = await require('child_process').execSync(command, {
            encoding: 'utf-8',
            cwd: vaultPath,
            timeout: 60000
        });

        if (stdout) {
            console.log(stdout);
            return stdout;
        }

        if (stderr) {
            console.error(stderr);
            new Notice(`⚠️ ${stderr}`, 5000);
        }

    } catch (error) {
        console.error(error);
        new Notice(`❌ 错误: ${error.message}`, 5000);
    }
}

/**
 * 主入口 - 可被 QuickAdd 调用
 */
module.exports = async function(params, ...args) {
    const command = args[0] || "chat";

    if (COMMANDS[command]) {
        return COMMANDS[command](...args.slice(1));
    } else {
        new Notice(`未知命令: ${command}`, 5000);
    }
};

// 导出供其他脚本使用
window.ObsidianAI = {
    run: runPythonScript,
    commands: COMMANDS
};