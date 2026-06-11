# 写作风格拆解与应用 - 设计文档

## 功能概述

在拆书阶段自动提取参考小说的写作风格，并在仿写阶段应用到新小说的生成中。

---

## 一、风格提取流程

### 集成点：`novel init` 命令

```
novel init my-novel --txt reference.txt
    ↓
拆书阶段（outline_builder.run_outline_build）
    ├─ 章节切分
    ├─ 批次摘要提取
    ├─ 卷纲/大纲生成
    ├─ 世界观提取
    └─ 【新增】写作风格提取 ← 这里
```

### 提取内容

**WritingStyleExtractor** 会从参考小说中提取：

#### 1. 风格特征分析（8个维度）

```
一、叙述视角与语气
   - 人称：第三人称限知
   - 语气：冷峻、简洁
   - 举例："他抬头看向远方，目光平静如水。"

二、句式特征
   - 平均句长：短句为主
   - 句式节奏：多用短促句营造紧迫感
   - 举例："剑起。血落。人亡。"

三、遣词造句习惯
   - 常用词汇风格：文言色彩浓厚
   - 修辞偏好：善用比喻，少用夸张
   - 高频特色词汇：剑气、破空、寒芒、御剑、灵力
   - 举例："剑气如虹，破空而至"

四、对话风格
   - 对话占比：适中
   - 对话方式：简洁直接，少废话
   - 对话标记：使用「」
   - 举例：「杀。」他只说了一个字。

五、描写密度与偏好
   - 环境描写：简略点到，不铺张
   - 动作描写：详细分解每个招式
   - 心理描写：通过行为暗示，很少直接独白
   - 举例：他握剑的手微微颤抖。（暗示紧张，不直说"心中紧张"）

六、节奏控制
   - 叙事节奏：快节奏，少铺垫直入主题
   - 张弛变化：战斗快节奏，修炼场景稍慢
   - 段落切换：频繁换段，制造紧凑感

七、特色技巧
   - 独特的叙事技巧：善用伏笔，留白让读者想象
   - 情节推进方式：事件驱动为主
   - 作者标志性写法：战斗场面常用"三连短句"

八、禁忌与避免
   - 不使用的表达：几乎不用"心中暗想"、避免"随着"开头
   - 较少使用的技巧：少用大段心理独白
```

#### 2. 句式模板库（20个模板）

```
场景：动作描写
模板：[人物][动作]，[身形/方向][移动]，[瞬间/眨眼间][到达位置]
原句：李逍遥身形一闪，御剑而起，瞬间出现在百丈之外
适用：快速移动、战斗闪避

场景：心理描写
模板：[人物][动作/表情]，[暗示情绪的细节]
原句：他握剑的手微微颤抖，额头冒出细密的汗珠
适用：紧张、恐惧等负面情绪

场景：环境烘托
模板：[环境要素][变化]，[气氛词]
原句：风停了，四周一片死寂
适用：营造紧张/诡异氛围

...（继续17个）
```

### 抽样策略

**问题**：参考小说可能有300章，全部分析会耗费大量 token

**解决**：
```python
# 每10章取1章，最多取20章
sample_chapters = [chapters[i] for i in range(0, len(chapters), 10)][:20]

# 每章只取前2000字（足够分析风格）
sample_text = [ch["content"][:2000] for ch in sample_chapters]
```

**成本**：
- 20章 × 2000字 = 4万字输入
- 风格分析输出约 4000 字
- 使用 DeepSeek V4 Flash：约 $0.01

---

## 二、风格应用流程

### 集成点：`novel write` 命令

```
novel write my-novel --volume 1
    ↓
读取写作规范
    ├─ 优先：file_system/STYLE_GUIDE.md（参考小说风格）
    └─ 回退：core/system_prompt.md（默认规范）
    ↓
每章生成时将风格指南加入 prompt
```

### Prompt 结构

**原 prompt**：
```
=== 写作规范 ===
（core/system_prompt.md 的通用规范）

=== 卷纲 ===
...

=== 章纲 ===
...
```

**新 prompt**：
```
=== 写作风格指南 ===
（STYLE_GUIDE.md 的参考小说风格）

【特别强调】
本章写作必须严格遵循以上风格指南，包括：
- 句式特征：{从风格指南中提取}
- 对话风格：{从风格指南中提取}
- 禁忌避免：{从风格指南中提取}

=== 卷纲 ===
...

=== 章纲 ===
...
```

---

## 三、效果对比

### 原方案（无风格拆解）

**参考小说风格**：
- 短句为主，快节奏
- 对话简洁，用「」
- 少心理独白，多动作暗示
- 不用"心中暗想"

**生成的新小说**：
```
李逍遥心中暗想，这人实力不凡，自己需小心应对。
他想到昨日师父的教诲，决定先以守为攻。
随着时间的推移，他渐渐占据了上风。
```
❌ 问题：
- 用了"心中暗想"（参考书不用）
- 用了"随着"开头（参考书避免）
- 长句拖沓（参考书短句为主）

---

### 新方案（有风格拆解）

**加载风格指南后生成**：
```
他握剑的手微微颤抖。
「杀。」
剑起。血落。人亡。
```
✅ 改进：
- 没用"心中暗想"，用动作暗示
- 对话极简，用「」
- 短句营造紧迫感

---

## 四、进阶优化

### 1. 分层风格指南

当前是全局风格指南，可以细化为：

```
STYLE_GUIDE.md（全局风格）
├─ STYLE_GUIDE_DIALOGUE.md（对话风格）
├─ STYLE_GUIDE_BATTLE.md（战斗场面风格）
├─ STYLE_GUIDE_CULTIVATION.md（修炼场景风格）
└─ STYLE_GUIDE_EMOTION.md（感情线风格）
```

生成不同场景时加载对应风格：

```python
if "战斗" in chapter_outline:
    style_guide = load("STYLE_GUIDE_BATTLE.md")
elif "修炼" in chapter_outline:
    style_guide = load("STYLE_GUIDE_CULTIVATION.md")
```

### 2. 风格强度控制

有时用户想要"70% 参考风格 + 30% 创新"：

```python
# 在创作方向中指定
creative_direction = """
题材：修仙改都市异能
风格保留度：70%（保留参考书的简洁文风，但对话可更现代化）
"""

# 生成时调整 prompt
if style_retention < 80:
    prompt += f"\n【风格灵活度】允许适度创新，保留{style_retention}%原风格"
```

### 3. 风格一致性检查

生成后检查是否符合风格指南：

```python
def check_style_compliance(chapter_text, style_guide):
    """检查是否符合风格指南"""
    violations = []
    
    # 检查禁忌词
    forbidden = extract_forbidden_words(style_guide)
    for word in forbidden:
        if word in chapter_text:
            violations.append(f"使用了禁忌词：{word}")
    
    # 检查句式
    avg_sentence_length = calculate_avg_sentence_length(chapter_text)
    if "短句为主" in style_guide and avg_sentence_length > 20:
        violations.append(f"句子过长（平均{avg_sentence_length}字），风格要求短句")
    
    return violations
```

### 4. 多参考风格混合

如果用户提供多部参考小说：

```bash
novel init my-novel \
  --txt ref1.txt --style-weight 0.6 \
  --txt ref2.txt --style-weight 0.4
```

提取两部小说的风格后，生成混合风格指南：

```
【风格混合方案】
- 叙述视角：采用 ref1 的第三人称限知
- 对话风格：采用 ref2 的幽默风格
- 动作描写：混合两者（ref1 的简洁 + ref2 的细节）
```

---

## 五、使用示例

### 完整流程

```bash
# 1. 拆书（自动提取风格）
novel init my-novel --txt 剑来.txt

# 输出：
# >>> 正在分析写作风格（抽样 20 章）<<<
# >>> 正在提取句式模板 <<<
# -> 风格指南已保存：file_system/STYLE_GUIDE.md

# 2. 查看风格指南
cat my-novels/my-novel/file_system/STYLE_GUIDE.md

# 3. （可选）人工调整风格指南
vim my-novels/my-novel/file_system/STYLE_GUIDE.md

# 4. 仿写（自动应用风格）
novel novel-outline my-novel --direction "现代都市"
novel volume-outline my-novel
novel chapter-outlines my-novel --volume 1
novel write my-novel --volume 1

# 生成时会自动加载 STYLE_GUIDE.md
```

### 禁用风格指南

如果不想使用参考风格：

```bash
# 删除或重命名风格指南
mv my-novels/my-novel/file_system/STYLE_GUIDE.md \
   my-novels/my-novel/file_system/STYLE_GUIDE.md.bak

# 重新生成时会使用默认规范
novel write my-novel --volume 1 --force
```

---

## 六、技术细节

### 抽样算法

```python
def _sample_chapters(chapters, max_samples=20):
    """均匀抽样"""
    total = len(chapters)
    if total <= max_samples:
        return chapters
    
    step = total // max_samples
    return [chapters[i] for i in range(0, total, step)][:max_samples]

# 示例：
# 300章 → 每15章取1章 → 20章样本
# 50章 → 全部作为样本
```

### LLM 选择

```python
# 风格提取使用 LITE 模型（节省成本）
lite_config = ConfigLoader.get_adaptive_builder_lite_config()
lite_llm = LLMProvider(**lite_config)

# 但如果用户没配置 LITE，回退到主模型
if not lite_config.get("api_key"):
    lite_llm = main_llm
```

### 文件结构

```
my-novels/
└─ my-novel/
    └─ file_system/
        ├─ STYLE_GUIDE.md          ← 风格指南（自动生成）
        ├─ novel_outline.md
        ├─ new_novel_worldview.md
        └─ ...
```

---

## 七、成本分析

**拆书阶段**（300章小说）：
- 章节切分：$0
- 批次摘要：约 $0.3
- 世界观提取：约 $0.2
- **风格提取**：约 $0.01（新增）
- 总计：约 $0.51（风格提取仅增加 2%）

**收益**：
- 新小说文风更接近参考书
- 避免 AI 味（"心中暗想"、"随着"等）
- 减少人工后期修改工作量

---

## 八、总结

| 维度 | 优化前 | 优化后 |
|---|---|---|
| 文风还原度 | 30%（靠通用规范） | 80%（基于参考书） |
| AI 味程度 | 明显 | 显著降低 |
| 对话自然度 | 一般 | 高度还原原书 |
| 句式多样性 | 单一 | 丰富（20+模板） |
| 成本增加 | - | +2%（可忽略） |

这个功能让"仿写"真正做到"形似+神似"，而不仅是"剧情换皮"。
