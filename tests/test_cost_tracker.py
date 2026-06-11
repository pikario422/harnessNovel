#!/usr/bin/env python3
"""测试 Token 成本追踪功能"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.cost_tracker import CostTracker, MODEL_PRICING

def test_cost_calculation():
    """测试成本计算"""
    tracker = CostTracker()

    # 测试 DeepSeek V4 Flash
    cost1 = tracker.add("deepseek-v4-flash", 1000, 2000)
    print(f"DeepSeek V4 Flash (1k input + 2k output): ${cost1:.6f}")

    # 测试 DeepSeek V4 Pro
    cost2 = tracker.add("deepseek-v4-pro", 10000, 5000)
    print(f"DeepSeek V4 Pro (10k input + 5k output): ${cost2:.6f}")

    # 测试 GPT-4o
    cost3 = tracker.add("gpt-4o", 5000, 3000)
    print(f"GPT-4o (5k input + 3k output): ${cost3:.6f}")

    # 打印总结
    print("\n" + "="*50)
    tracker.print_summary()

    # 验证总计
    summary = tracker.get_summary()
    expected_total = cost1 + cost2 + cost3
    assert abs(summary['cost_usd'] - expected_total) < 0.0001, "成本计算错误"

    print("\n✅ 测试通过！")

def test_unknown_model():
    """测试未知模型的默认定价"""
    tracker = CostTracker()
    cost = tracker.add("unknown-model-xyz", 1000, 1000)
    print(f"\n未知模型默认定价 (1k input + 1k output): ${cost:.6f}")
    assert cost > 0, "未知模型应使用默认定价"
    print("✅ 未知模型测试通过！")

if __name__ == "__main__":
    print("开始测试 Token 成本追踪功能...\n")
    test_cost_calculation()
    test_unknown_model()
