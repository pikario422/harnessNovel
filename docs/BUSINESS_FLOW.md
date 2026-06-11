# harnessNovel 业务流程分析

## 一、整体架构

```
用户输入（参考小说.txt + 创作方向）
           ↓
    ┌──────────────┐
    │  拆书阶段    │  → 提取结构化知识
    └──────────────┘
           ↓
    ┌──────────────┐
    │  仿写阶段    │  → 生成新小说
    └──────────────┘
           ↓
    输出（新小说正文）
```

---

## 二、拆书阶段详细流程

**执行命令**：`novel init <workspace> --txt <参考小说.txt>`

**入口函数**：`novel_cli.cmd_init()` → `training/outline_builder.run_outline_build()`

### 阶段 1：章节切分与识别

```
参考小说.txt
    ↓
split_chapters()
    ├─ _find_volumes()      → 识别卷标题（正则匹配）
    ├─ _find_chapters()     → 识别章节标题（正则匹配）
    └─ _assign_volumes()    → 按位置分配章节到卷
    ↓
返回：volumes[], chapters[]
```

**关键算法**：
- 卷标题正则：`^第[一二三四五...]卷\s+\S+`
- 章节正则：`^第[一二三四五...]章\s+.+`
- 按位置分配：章节的 `pos` 属于哪个卷的起始范围

### 阶段 2：批次摘要提取

```
每卷章节
    ↓
按 batch_size (默认20章) 分批
    ↓
每批调用 LLM (DATA_BUILDER)
    ├─ Prompt: batch_extract
    ├─ 输入：20章原文
    └─ 输出：batch_XXX_YYY.md (摘要)
    ↓
存储到：reference/outlines/vol_XX_<卷名>/
```

**断点续传**：检测文件存在则跳过

### 阶段 3：卷纲合并

```
本卷所有批次摘要
    ↓
情况1：单批次 → 直接作为卷纲
情况2：多批次 → 调用 LLM (DATA_BUILDER)
    ├─ Prompt: volume_merge
    ├─ 输入：所有批次摘要
    └─ 输出：volume_outline.md
    ↓
存储到：reference/outlines/vol_XX_<卷名>/volume_outline.md
```

### 阶段 4：虚拟分卷（可选）

**触发条件**：仅有一个"全书"伪卷

```
所有批次摘要
    ↓
调用 LLM (DATA_BUILDER)
    ├─ Prompt: virtual_volume_segment
    ├─ 分析：识别剧情卷边界
    └─ 输出：卷1：标题 | 第X-Y章
    ↓
边界对齐到故事片段端点
    ↓
创建虚拟卷目录
    ├─ 复制对应批次文件
    ├─ 写入 meta.json (start_ch, end_ch)
    └─ 生成虚拟卷卷纲
```

**智能合并**：卷章节数 < 60 时自动合并到相邻卷

### 阶段 5：全书大纲汇总

```
所有卷纲
    ↓
调用 LLM (DATA_BUILDER)
    ├─ Prompt: novel_extract
    ├─ 输入：所有卷纲
    └─ 输出：novel_outline.md
    ↓
存储到：reference/outlines/novel_outline.md
```

### 阶段 6：世界观提取

```
每卷卷纲 + 批次摘要
    ↓
调用 LLM (ADAPTIVE_BUILDER_LITE)
    ├─ Prompt: worldview_extract
    └─ 输出：vol_XX_worldview.md
    ↓
所有卷世界观
    ↓
情况1：单卷 → 直接作为全书世界观
情况2：多卷 → 调用 LLM (ADAPTIVE_BUILDER_LITE)
    ├─ Prompt: worldview_merge
    └─ 输出：reference_worldview.md
```

**世界观结构**：
- 势力与人物
- 修炼体系
- 特殊物品
- 地理场景
- 种族与族群
- 核心规则与禁忌
- 主角金手指进展

---

## 三、仿写阶段详细流程

### Step 1: 生成新小说大纲

**执行命令**：`novel novel-outline <workspace> --direction "创作方向"`

**入口函数**：`training/adaptive_builder.gen_novel_outline()`

```
输入材料：
├─ 参考小说大纲 (novel_outline.md)
├─ 参考小说世界观 (reference_worldview.md)
├─ 创作方向 (CLI 参数 / creative_direction.md)
└─ 大纲设计规则 (OUTLINE_RULES.md, 可选)
    ↓
调用 LLM (ADAPTIVE_BUILDER)
    ├─ Prompt: adaptive_novel_outline
    └─ 要求：换皮映射，保留结构，注入创作方向
    ↓
输出：file_system/novel_outline.md
    ↓
自动触发：生成新小说全书世界观
    ├─ 输入：新大纲 + 参考世界观
    ├─ 换皮映射：名称替换，体系重设计
    └─ 输出：file_system/new_novel_worldview.md
```

**关键逻辑**：
- 不是重新创作，是**换皮映射**
- 保留参考的节奏、结构、张力曲线
- 结合用户创作方向微调

### Step 2: 生成卷纲

**执行命令**：`novel volume-outline <workspace> [--volume N]`

**入口函数**：`training/adaptive_builder.gen_volume_outline()`

```
输入材料：
├─ 新小说大纲 (novel_outline.md)
├─ 新小说全书世界观 (new_novel_worldview.md)
├─ 上一卷卷纲 (vol_XX-1_outline.md, 保持连贯)
├─ 参考小说对应卷纲 (顺序映射：新卷N → 参考卷N)
└─ 创作方向
    ↓
调用 LLM (ADAPTIVE_BUILDER)
    ├─ Prompt: adaptive_volume_outline
    ├─ 判断：是否为终卷？
    │   ├─ 是 → 输出末尾加 [FINISHED]
    │   └─ 否 → 输出末尾加 [CONTINUE]
    └─ 输出：file_system/new_volume_outlines/vol_XX_outline.md
    ↓
自动触发：生成该卷世界观
    ├─ 输入：全书世界观 + 本卷卷纲 + 上卷世界观
    ├─ 细化：本卷涉及的势力、人物、地点
    └─ 输出：file_system/new_worldviews/vol_XX_worldview.md
```

**终卷判断**：
- LLM 根据大纲判断剧情是否收尾
- 检测到 `[FINISHED]` 停止生成
- 支持断点续传：从最后一卷继续

**逐卷生成模式**：
- 不指定 `--volume` → 从卷1开始，自动生成到终卷
- 指定 `--volume N` → 仅生成第N卷

### Step 3: 生成章纲

**执行命令**：`novel chapter-outlines <workspace> --volume N`

**入口函数**：`training/adaptive_builder.gen_serial_chapter_outlines()`

**两阶段设计**：

#### Phase 1: 生成批次摘要

```
输入材料：
├─ 本卷卷纲 (vol_XX_outline.md)
├─ 本卷世界观 (vol_XX_worldview.md)
├─ 上一批次摘要 (前20章的批次摘要)
└─ 参考小说对应批次摘要
    ↓
从卷纲推断总章数（正则提取"第X章"）
    ↓
按 BATCH_SIZE (20章) 切分
    ↓
每批调用 LLM (ADAPTIVE_BUILDER)
    ├─ Prompt: novel_batch_summary
    ├─ 要求：规划本批次的剧情节点
    └─ 输出：outlines/vol_XX/batch_XXX_YYY.md
```

#### Phase 2: 生成逐章章纲

```
每个批次摘要
    ↓
逐章生成章纲
    ├─ 输入：本批次摘要 + 前2章章纲
    ├─ 调用 LLM (ADAPTIVE_BUILDER)
    ├─ Prompt: serial_chapter_outline
    └─ 输出：chapter_outlines/vol_XX/chapter_XXX.md
```

**连贯性保障**：
- 批次摘要提供宏观节奏
- 前2章章纲提供局部衔接
- 逐章串行生成，避免割裂

### Step 4: 生成正文

**执行命令**：`novel write <workspace> --volume N [--start X] [--max Y]`

**入口函数**：`training/adaptive_builder.gen_serial_chapters()`

```
输入材料：
├─ 写作规范 (core/system_prompt.md + core/agents.md)
├─ 本卷卷纲 (vol_XX_outline.md)
├─ 本卷世界观 (vol_XX_worldview.md)
├─ 本章章纲 (chapter_XXX.md)
├─ 本批次摘要 (batch_XXX_YYY.md, 提供宏观节奏)
└─ 前2章正文末尾2000字 (保持文笔连贯)
    ↓
逐章串行生成
    ├─ 调用 LLM (ADAPTIVE_BUILDER)
    ├─ Prompt: adaptive_drafting
    └─ 输出：chapters/vol_XX/XXX_第X章.md
```

**断点续传**：
- 扫描已有正文文件，自动跳过
- `--start N` 指定起始章节
- `--max Y` 限制生成章节数（避免一次生成太多）

---

## 四、数据流转图

```
[参考小说.txt]
        ↓
    章节切分
        ↓
┌───────────────────────────────────┐
│  reference/outlines/              │
│  ├─ vol_01_<卷名>/                │
│  │   ├─ batch_001_020.md         │ ← 批次摘要
│  │   ├─ volume_outline.md        │ ← 卷纲
│  │   └─ meta.json (虚拟卷)       │
│  ├─ novel_outline.md             │ ← 全书大纲
│  └─ volume_outline.md            │ ← 汇总卷纲
└───────────────────────────────────┘
        ↓
    世界观提取
        ↓
┌───────────────────────────────────┐
│  file_system/                     │
│  ├─ worldviews/                   │
│  │   └─ vol_XX_worldview.md      │
│  └─ reference_worldview.md       │ ← 全书世界观
└───────────────────────────────────┘
        ↓
    仿写生成
        ↓
┌───────────────────────────────────┐
│  file_system/                     │
│  ├─ novel_outline.md             │ ← 新大纲
│  ├─ new_novel_worldview.md       │ ← 新全书世界观
│  ├─ new_volume_outlines/         │
│  │   └─ vol_XX_outline.md        │ ← 新卷纲
│  ├─ new_worldviews/               │
│  │   └─ vol_XX_worldview.md      │ ← 新卷世界观
│  ├─ outlines/vol_XX/             │
│  │   └─ batch_XXX_YYY.md         │ ← 新批次摘要
│  ├─ chapter_outlines/vol_XX/     │
│  │   └─ chapter_XXX.md           │ ← 章纲
│  └─ chapters/vol_XX/             │
│      └─ XXX_第X章.md             │ ← 正文
└───────────────────────────────────┘
```

---

## 五、关键设计模式

### 1. 渐进式细化（Progressive Refinement）

```
全书大纲 (宏观)
    ↓
卷纲 (中观)
    ↓
批次摘要 (局部宏观)
    ↓
章纲 (微观)
    ↓
正文 (细节)
```

**优势**：
- 避免 LLM 一次性生成长文的失控
- 每层都有上下文约束
- 支持任意阶段修改后重新生成下层

### 2. 上下文窗口管理

**问题**：长篇小说正文可能几百万字，无法全部放入 LLM 上下文

**解决方案**：
- **滑动窗口**：只保留前2章正文（末尾2000字）
- **批次摘要**：压缩20章为摘要，提供宏观节奏
- **分层世界观**：全书世界观 → 卷世界观，避免冗余

### 3. 换皮映射（Skin Mapping）

**核心思想**：不是重新创作，是有根基的创新

```
参考小说                  新小说
────────────────────────────────
第一卷：修仙入门    →     第一卷：异能觉醒
  ├─ 势力：天剑宗    →       势力：能力者协会
  ├─ 体系：炼气→筑基  →       体系：E级→D级
  ├─ 物品：聚灵丹    →       物品：基因药剂
  └─ 节奏：20章     →       节奏：20章 (保留)
```

**映射关系**：
- 名称替换（势力、人物、地点、物品）
- 体系重设计（修炼境界 → 异能等级）
- **节奏保留**（章节数、剧情张力曲线）

### 4. 断点续传机制

**实现方式**：
```python
if os.path.exists(output_file) and not force:
    print(f"已存在，跳过")
    return
```

**适用场景**：
- 生成中断（网络/API 失败）
- 分批生成（避免一次性费用过高）
- 人工审核后继续（修改大纲后只重新生成受影响部分）

### 5. 三层 LLM 配置

```
┌─────────────────────────────────────┐
│ DATA_BUILDER (Flash 模型)           │
│ ├─ 拆书批次摘要提取                 │
│ └─ 特点：速度快、成本低             │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│ ADAPTIVE_BUILDER_LITE (Flash 模型)  │
│ ├─ 世界观提取                       │
│ ├─ 灵感筛选                         │
│ └─ 特点：速度快、成本低             │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│ ADAPTIVE_BUILDER (Pro 模型)         │
│ ├─ 大纲、卷纲、章纲生成             │
│ ├─ 正文撰写                         │
│ └─ 特点：质量高、成本高             │
└─────────────────────────────────────┘
```

**设计目标**：平衡质量和成本

---

## 六、典型用户流程时间线

以 300 章小说为例（参考小说 + 新小说生成）：

```
Day 1:
  └─ novel init my-novel --txt ref.txt
     ├─ 章节切分: 2s
     ├─ 批次摘要提取: 15 批 × 30s = 7.5分钟
     ├─ 虚拟分卷: 2分钟
     ├─ 世界观提取: 3卷 × 1分钟 = 3分钟
     └─ 总计: 约 13 分钟

Day 2:
  └─ novel novel-outline my-novel --direction "..."
     ├─ 生成新大纲: 2分钟
     ├─ 生成全书世界观: 1分钟
     └─ 人工审核修改: 1小时

Day 3-5:
  └─ novel volume-outline my-novel
     ├─ 生成3卷卷纲: 3卷 × 2分钟 = 6分钟
     ├─ 生成3卷世界观: 3卷 × 1分钟 = 3分钟
     └─ 人工审核修改: 每卷30分钟

Day 6-8:
  └─ novel chapter-outlines my-novel --volume 1
     ├─ 生成批次摘要: 5批 × 1分钟 = 5分钟
     ├─ 生成章纲: 100章 × 20s = 33分钟
     └─ 重复3卷: 约 2小时

Day 9-30:
  └─ novel write my-novel --volume 1 --max 10
     ├─ 生成正文: 10章 × 2分钟 = 20分钟/天
     ├─ 人工审核修改: 10章 × 15分钟 = 2.5小时/天
     └─ 30天完成 300章
```

**成本估算（DeepSeek V4）**：
- 拆书: 约 $0.5
- 仿写大纲/卷纲/章纲: 约 $2
- 正文生成（300章，每章3000字）: 约 $20
- **总计**: 约 $22.5 (¥162)

---

## 七、核心优化策略

### 1. 为什么使用批次摘要？

**问题**：直接让 LLM 生成 300 章章纲，容易出现：
- 前后矛盾
- 遗忘前文设定
- 剧情节奏失控

**解决**：
```
卷纲 (100章宏观规划)
    ↓
批次摘要 (每20章中观规划)
    ↓
章纲 (逐章微观规划)
```

每20章形成一个节奏单元，保证连贯性。

### 2. 为什么逐章串行生成正文？

**并发问题**：
- 第5章和第6章并发生成，可能出现伏笔冲突
- 人物状态不同步

**串行优势**：
- 每章都读取前2章的末尾，保持文笔连贯
- 严格按剧情顺序推进

### 3. 为什么要虚拟分卷？

**问题**：参考小说可能是连载作品，无自然分卷

**解决**：
- LLM 分析批次摘要，识别剧情卷边界
- 对齐到故事片段端点（避免拆碎情节）
- 自动合并小于60章的卷（避免碎片化）

---

## 八、潜在瓶颈与优化方向

### 1. 当前瓶颈

| 阶段 | 瓶颈 | 影响 |
|---|---|---|
| 批次摘要提取 | 串行调用 LLM | 15批 × 30s = 7.5分钟 |
| 章纲生成 | 串行调用 LLM | 100章 × 20s = 33分钟 |
| 正文生成 | 串行调用 LLM | 300章 × 2分钟 = 10小时 |

### 2. 并发优化方案

```python
# 当前
for batch in batches:
    result = llm.generate(prompt)

# 优化
with ThreadPoolExecutor(max_workers=5) as executor:
    futures = [executor.submit(llm.generate, prompt) for prompt in prompts]
    results = [f.result() for f in futures]
```

**适用场景**：
- ✅ 批次摘要提取（独立任务）
- ✅ 章纲生成（基于批次摘要，批次间独立）
- ❌ 正文生成（需要读取前文，必须串行）

**预期收益**：
- 批次摘要：7.5分钟 → 2分钟 (5个并发)
- 章纲生成：33分钟 → 8分钟

---

## 九、总结

harnessNovel 的核心设计理念：

1. **结构化拆书** - 提取参考小说的精华，而非原文照搬
2. **换皮映射** - 有根基的创新，避免 AI 凭空创作的平庸化
3. **渐进式细化** - 从宏观到微观，层层约束，避免失控
4. **上下文管理** - 滑动窗口 + 批次摘要，解决长文生成难题
5. **断点续传** - 支持分批生成、人工审核、成本控制

这套流程让 AI 能够真正写出**结构完整、逻辑自洽、节奏合理**的长篇小说，而不是简单的文字拼接。
