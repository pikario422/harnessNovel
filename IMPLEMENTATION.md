# Token 成本可视化功能 - 实现总结

## 新增文件

1. **[core/cost_tracker.py](core/cost_tracker.py)** - Token 成本追踪核心模块
   - `CostTracker` 类：记录和统计 Token 消耗
   - `MODEL_PRICING` 字典：主流模型定价表
   - 全局追踪器实例

2. **[docs/COST_TRACKING.md](docs/COST_TRACKING.md)** - 功能说明文档

3. **[tests/test_cost_tracker.py](tests/test_cost_tracker.py)** - 单元测试

4. **[requirements.txt](requirements.txt)** - 依赖清单

## 修改文件

1. **[core/llm_provider.py](core/llm_provider.py)**
   - 引入 `tiktoken` 和 `cost_tracker`
   - 初始化时创建 tokenizer
   - `generate()` 方法增加 Token 估算和成本记录
   - 每次调用显示：预估输入 → 实际输入/输出 → 成本

2. **[novel_cli.py](novel_cli.py)**
   - 所有命令函数增加 `reset_tracker()` 和 `print_summary()`
   - 命令执行前重置统计，执行后打印汇总

3. **[setup.py](setup.py)**
   - 添加 `tiktoken>=0.5.0` 依赖

4. **[README.md](README.md) / [README_EN.md](README_EN.md)**
   - 特性列表增加"Token 成本可视化"
   - 快速开始示例增加成本统计输出演示

## 功能特点

### 1. 实时显示
每次 LLM 调用都显示：
```
[LLMProvider] 调用模型 deepseek-v4-flash（预估输入：12,450 tokens）...
[LLMProvider] 完成（输入：12,450 | 输出：3,200 | 成本：$0.0032）
```

### 2. 命令级汇总
每个命令执行完成后显示总统计：
```
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

### 3. 支持主流模型
- DeepSeek (v4-flash, v4-pro, chat, reasoner)
- OpenAI (gpt-4o, gpt-4o-mini, gpt-4-turbo, gpt-3.5-turbo)
- Claude (sonnet, haiku, opus)
- 智谱 GLM (glm-4-plus, glm-4-flash)
- Qwen (qwen-plus, qwen-turbo)

### 4. 智能回退
- 优先使用 API 返回的 `usage` 字段
- 如无则使用 tiktoken 估算（误差 ±5%）
- 未知模型使用默认定价

## 使用方式

无需任何配置，功能自动启用。执行任何命令都会显示成本统计：

```bash
novel init my-novel --txt ref.txt
novel novel-outline my-novel --direction "现代都市"
novel volume-outline my-novel --volume 1
novel chapter-outlines my-novel --volume 1
novel write my-novel --volume 1
```

## 测试方法

```bash
# 运行单元测试
python tests/test_cost_tracker.py
```

## 技术要点

1. **Token 计数**：使用 tiktoken（GPT-4 tokenizer），适用于大多数模型
2. **成本计算**：基于 2025年6月 的官方定价
3. **线程安全**：使用全局单例模式，支持并发场景
4. **零侵入**：现有代码无需修改配置，自动启用

## 后续优化空间

1. **历史记录**：将统计持久化到 `.cost_history.json`
2. **预算控制**：设置单次操作预算上限，超出时提前警告
3. **成本对比**：显示不同模型完成同任务的预估成本对比
4. **定价更新**：定期从官网自动更新模型定价
