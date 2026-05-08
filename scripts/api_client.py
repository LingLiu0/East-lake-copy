#!/usr/bin/env python3
"""
自定义 API 客户端 - 支持任意兼容 OpenAI 格式的大模型 API
"""
import os
import requests
from typing import Optional

# 配置（可被环境变量覆盖）
API_BASE = os.getenv("API_BASE", "https://zhenze-huhehaote.cmecloud.cn")
API_KEY = os.getenv("API_KEY", "7R0_5N8p7twgq2xd6Z15Uu0gy4u8cvLViOOX-rbNKQE")
MODEL = os.getenv("MODEL", "Minimax-M2.5")  # 默认用 Minimax-M2.5
API_PATH = "/api/coding/v1/chat/completions"  # API 路径


def chat(
    prompt: str,
    model: str = None,
    system_prompt: str = None,
    temperature: float = 0.7,
    max_tokens: int = 2000
) -> Optional[str]:
    """
    调用自定义大模型 API

    Args:
        prompt: 用户提示
        model: 模型名称（默认从环境变量或配置获取）
        system_prompt: 系统提示
        temperature: 温度参数
        max_tokens: 最大 token 数

    Returns:
        AI 回复文本，失败返回 None
    """
    model = model or MODEL

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens
    }

    try:
        resp = requests.post(
            f"{API_BASE}{API_PATH}",
            headers=headers,
            json=payload,
            timeout=120
        )
        resp.raise_for_status()
        result = resp.json()

        # 兼容 OpenAI 格式
        if "choices" in result:
            return result["choices"][0]["message"]["content"]
        # 兼容 DashScope 格式
        elif "output" in result and "text" in result["output"]:
            return result["output"]["text"]
        else:
            print(f"⚠️ 未知响应格式: {result}")
            return None
    except requests.exceptions.Timeout:
        print("❌ 请求超时")
        return None
    except requests.exceptions.HTTPError as e:
        print(f"❌ HTTP 错误: {e}")
        try:
            print(f"   响应: {e.response.text}")
        except:
            pass
        return None
    except Exception as e:
        print(f"❌ 调用失败: {e}")
        return None


def test_connection() -> bool:
    """测试 API 连接"""
    print(f"🔧 测试 API 连接...")
    print(f"   端点: {API_BASE}")
    print(f"   模型: {MODEL}")

    result = chat("你好，请回复'测试成功'", model=MODEL)

    if result:
        print(f"   ✅ 连接成功！")
        print(f"   回复: {result[:100]}")
        return True
    else:
        print(f"   ❌ 连接失败")
        return False


if __name__ == "__main__":
    test_connection()