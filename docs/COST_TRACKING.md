# Token 成本可视化功能

## 功能说明

每次执行命令后，自动显示本次操作的 Token 消耗和成本统计。

## 使用示例

```bash
$ novel init my-novel --txt reference.txt

>>> 参考小说大纲梳理启动 <<<
[LLMProvider] 调用模型 deepseek-v4-flash（预估输入：12,450 tokens）...
[LLMProvider] 完成（输入：12,450 | 输出：3,200 | 成本：$0.0032）

...（中间过程省略）...

==================================================
📊 Token 使用统计
==================================================
  调用次数：45
  输入 Token：562,340
  输出 Token：128,760
  总计 Token：691,100
  💰 成本：$0.4528 (约 ¥3.26)
==================================================
```

## 支持的模型

### DeepSeek
- `deepseek-chat`: $0.14/$0.28 per 1M tokens (input/output)
- `deepseek-v4-flash`: $0.07/$0.14 per 1M tokens
- `deepseek-v4-pro`: $0.55/$2.19 per 1M tokens
- `deepseek-reasoner`: $0.55/$2.19 per 1M tokens

### OpenAI
- `gpt-4o`: $2.5/$10.0 per 1M tokens
- `gpt-4o-mini`: $0.15/$0.6 per 1M tokens
- `gpt-4-turbo`: $10.0/$30.0 per 1M tokens
- `gpt-3.5-turbo`: $0.5/$1.5 per 1M tokens

### Claude (Anthropic)
- `claude-3-5-sonnet-20241022`: $3.0/$15.0 per 1M tokens
- `claude-3-5-haiku-20241022`: $0.8/$4.0 per 1M tokens
- `claude-3-opus-20240229`: $15.0/$75.0 per 1M tokens

### 智谱 GLM
- `glm-4-plus`: $0.7/$0.7 per 1M tokens
- `glm-4-flash`: $0.014/$0.014 per 1M tokens

### Qwen
- `qwen-plus`: $0.28/$0.56 per 1M tokens
- `qwen-turbo`: $0.21/$0.42 per 1M tokens

## 实现细节

1. **Token 估算**：使用 `tiktoken` 库（GPT-4 tokenizer）估算输入 token 数
2. **实际统计**：优先使用 API 返回的 `usage` 字段，如无则使用估算值
3. **成本计算**：基于模型定价表自动计算，显示美元和人民币（汇率 7.2）
4. **未知模型**：使用默认定价（$0.5/$1.5 per 1M tokens）

## 注意事项

- Token 计数是估算值，与实际 API 消耗可能有 ±5% 误差
- 汇率为固定值 7.2，仅供参考
- 成本统计在每个命令开始时重置，只显示本次操作的消耗
- 如果 API 不返回 `usage` 字段，统计精度会降低
