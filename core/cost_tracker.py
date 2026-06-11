# Token 成本追踪与可视化

# 主流模型定价（美元 / 1M tokens）
MODEL_PRICING = {
    # DeepSeek
    "deepseek-chat": {"input": 0.14, "output": 0.28},
    "deepseek-reasoner": {"input": 0.55, "output": 2.19},
    "deepseek-v4-flash": {"input": 0.07, "output": 0.14},
    "deepseek-v4-pro": {"input": 0.55, "output": 2.19},

    # OpenAI
    "gpt-4o": {"input": 2.5, "output": 10.0},
    "gpt-4o-mini": {"input": 0.15, "output": 0.6},
    "gpt-4-turbo": {"input": 10.0, "output": 30.0},
    "gpt-3.5-turbo": {"input": 0.5, "output": 1.5},

    # Claude (Anthropic)
    "claude-3-5-sonnet-20241022": {"input": 3.0, "output": 15.0},
    "claude-3-5-haiku-20241022": {"input": 0.8, "output": 4.0},
    "claude-3-opus-20240229": {"input": 15.0, "output": 75.0},

    # 智谱 GLM
    "glm-4-plus": {"input": 0.7, "output": 0.7},
    "glm-4-flash": {"input": 0.014, "output": 0.014},

    # Qwen
    "qwen-plus": {"input": 0.28, "output": 0.56},
    "qwen-turbo": {"input": 0.21, "output": 0.42},
}


class CostTracker:
    def __init__(self):
        self.sessions = []  # [{model, input_tokens, output_tokens, cost}]

    def add(self, model, input_tokens, output_tokens):
        """记录一次调用"""
        cost = self._calculate_cost(model, input_tokens, output_tokens)
        self.sessions.append({
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost": cost
        })
        return cost

    def _calculate_cost(self, model, input_tokens, output_tokens):
        """计算成本（美元）"""
        pricing = MODEL_PRICING.get(model)
        if not pricing:
            # 未知模型，使用默认估算
            pricing = {"input": 0.5, "output": 1.5}

        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        output_cost = (output_tokens / 1_000_000) * pricing["output"]
        return input_cost + output_cost

    def get_summary(self):
        """获取总计"""
        if not self.sessions:
            return None

        total_input = sum(s["input_tokens"] for s in self.sessions)
        total_output = sum(s["output_tokens"] for s in self.sessions)
        total_cost = sum(s["cost"] for s in self.sessions)

        return {
            "calls": len(self.sessions),
            "input_tokens": total_input,
            "output_tokens": total_output,
            "total_tokens": total_input + total_output,
            "cost_usd": total_cost,
            "cost_cny": total_cost * 7.2  # 汇率估算
        }

    def print_summary(self):
        """打印统计信息"""
        summary = self.get_summary()
        if not summary:
            return

        print("\n" + "=" * 50)
        print("📊 Token 使用统计")
        print("=" * 50)
        print(f"  调用次数：{summary['calls']}")
        print(f"  输入 Token：{summary['input_tokens']:,}")
        print(f"  输出 Token：{summary['output_tokens']:,}")
        print(f"  总计 Token：{summary['total_tokens']:,}")
        print(f"  💰 成本：${summary['cost_usd']:.4f} (约 ¥{summary['cost_cny']:.2f})")
        print("=" * 50)


# 全局实例
_global_tracker = CostTracker()


def get_tracker():
    """获取全局追踪器"""
    return _global_tracker


def reset_tracker():
    """重置追踪器"""
    global _global_tracker
    _global_tracker = CostTracker()
