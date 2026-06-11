# 章节同质化与衔接问题 - 解决方案总结

## 问题分析

### 问题 1：章节描写同质化

**表现**：
- 所有章节都是"主角醒来"开头
- 所有章节都是"主角总结当前情况"结尾
- 场景类型单一（连续10章都是打斗）
- 节奏平缓（没有起伏）

**根本原因**：
- LLM 生成时没有"记忆"前几章的模式
- 每章 prompt 相互独立，缺少多样性约束
- 批次摘要只规划剧情，不控制叙事技巧

### 问题 2：章节割裂感

**表现**：
- 上章：主角在房间准备出门 → 本章：主角已经在山顶战斗
- 上章：夜晚紧张氛围 → 本章：清晨轻松对话（无过渡）
- 上章：提到"明天找李二"→ 本章：忘了这茬

**根本原因**：
- 正文生成时只看前2章末尾 2000 字（丢失了上章结尾的状态信息）
- 没有显式的"衔接要求"传递给 LLM
- LLM 不知道下章内容，无法为下章铺垫

---

## 解决方案

### 方案 1: 章节多样性追踪器 (ChapterDiversityTracker)

**核心思路**：记录每章的"开头类型、结尾类型、场景类型"，生成下一章时主动避免重复。

#### 追踪内容

```python
{
    "opening_type": "醒来",      # 开头分类（醒来/对话/动作/环境/回忆/独白）
    "ending_type": "总结",        # 结尾分类（总结/悬念/对话/动作/环境）
    "scene_type": "战斗",         # 场景分类（战斗/修炼/对话/探索/日常）
    "has_dialogue": True,         # 是否有对话
    "has_action": True,           # 是否有动作场面
    "has_introspection": False,   # 是否有内心戏
}
```

#### 生成多样性要求

```python
# 最近3章的开头：醒来、醒来、对话
# 生成要求：
"""
⚠️ 避免使用「醒来」类型的开头（最近已用2次）
建议使用：动作开头（直接进入场景）/ 环境描写开头
"""
```

#### 节奏调节

```python
# 每3章插入高潮场景
if chapter_num % 3 == 0:
    "✓ 建议：本章安排高潮场景（战斗/冲突/突破）"

# 每5章插入角色互动
if chapter_num % 5 == 0:
    "✓ 建议：本章安排角色互动（对话/感情线）"
```

---

### 方案 2: 章节衔接管理器 (ChapterTransitionManager)

**核心思路**：分析上章结尾状态（地点、时间、人物、氛围），生成"衔接桥接"指导下章开头。

#### 提取上章结尾状态

```python
{
    "location": "房间",
    "characters_present": ["主角", "李二"],
    "time": "夜晚",
    "mood": "紧张",
    "unresolved_action": True,  # 有未完成动作（如："正要出门"）
    "ending_sentence": "他转身走向房门。",
}
```

#### 生成衔接桥接

```python
"""
【章节衔接要求】

1. 时空连续性
   - 上章结尾：房间 / 夜晚
   - 要求：本章开头应从房间开始，避免突然跳到山顶

2. 人物状态延续
   - 上章在场人物：主角、李二
   - 要求：如有人物消失，需说明原因

3. 情绪/氛围承接
   - 上章氛围：紧张
   - 要求：本章开头延续紧张感，不要突然变轻松

4. 动作/事件衔接
   - 上章结尾句：「他转身走向房门。」
   - ⚠️ 上章有未完成动作，本章应立即承接（不要跳到第二天）

5. 过渡技巧建议
   - 使用「立即承接」：上章刚要出门 → 本章开头推开房门
"""
```

#### 生成结尾指导（为下章铺垫）

```python
"""
【本章结尾要求】

1. 为下章铺垫
   - 下章内容：主角前往天剑宗参加大比
   - 要求：结尾埋下伏笔（如：远处传来钟声，他知道大比即将开始）

2. 避免「总结式」结尾
   - ❌ 不要：「他心中暗想，明天一定要去天剑宗」（过于直白）
   - ✓ 建议：「天边传来剑鸣，他抬头望向天剑宗方向」（含蓄引导）

3. 结尾类型选择
   - 悬念结尾：适合剧情紧张、下章有转折
   - 动作结尾：适合下章有战斗
"""
```

---

## 集成到生成流程

### 修改 `training/adaptive_builder.py` 的 `gen_serial_chapters()`

**原流程**：
```python
for ch_num in pending:
    # 读取章纲
    chapter_outline = _read_file(...)
    
    # 读取前2章正文末尾
    prev_texts = [...]
    
    # 生成正文
    result = llm.generate(prompt)
```

**新流程**：
```python
from core.chapter_diversity import get_diversity_tracker
from core.chapter_transition import ChapterTransitionManager

diversity_tracker = get_diversity_tracker()
transition_manager = ChapterTransitionManager()

for ch_num in pending:
    # 1. 读取章纲
    chapter_outline = _read_file(...)
    
    # 2. 生成多样性要求
    diversity_requirements = diversity_tracker.generate_diversity_requirements(ch_num)
    
    # 3. 分析上章结尾，生成衔接桥接
    if ch_num > 1:
        prev_chapter = _read_file(...)
        transition_bridge = transition_manager.generate_transition_bridge(
            prev_chapter, chapter_outline
        )
    else:
        transition_bridge = "【第一章，无需衔接】"
    
    # 4. 读取下章章纲，生成结尾指导
    next_chapter_outline = _read_file(...) or "（最后一章）"
    ending_guidance = transition_manager.generate_ending_guidance(
        chapter_outline, next_chapter_outline
    )
    
    # 5. 增强 prompt
    enhanced_prompt = f"""
{original_prompt}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
【多样性要求】
{diversity_requirements}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
【章节衔接要求】
{transition_bridge}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
【结尾写作指导】
{ending_guidance}
"""
    
    # 6. 生成正文
    result = llm.generate(enhanced_prompt)
    
    # 7. 记录本章模式（供下章参考）
    diversity_tracker.add_chapter(ch_num, result)
    
    _write_file(out_file, result)
```

---

## 效果对比

### 原方案（无优化）

```
第1章：主角醒来，修炼一天，心中总结今日收获。
第2章：主角醒来，前往市场，心中总结今日经历。
第3章：主角醒来，遇到李二，心中总结当前处境。
  ↓
【问题】：三章都是"醒来"开头，"总结"结尾，读者感觉在看流水账
```

**章节衔接**：
```
第5章结尾：主角正要推门而入...（动作未完成）
第6章开头：第二天清晨，主角来到山顶。（时空突然跳跃）
  ↓
【问题】：读者懵了，昨天那个门推开没有？怎么突然到山顶了？
```

---

### 新方案（有优化）

**多样性控制**：
```
第1章：主角醒来，修炼一天，心中总结今日收获。
      ↓ [追踪器记录：开头=醒来，结尾=总结]
      
第2章：生成时收到要求："避免醒来开头，避免总结结尾"
      → 结果：李二推门而入："师兄，宗门来人了！"（对话开头）
      → 结尾：他转身离开，留下一句："明日再说。"（对话结尾）
      ↓ [追踪器记录：开头=对话，结尾=对话]
      
第3章：生成时收到要求："避免对话开头"
      → 结果：剑光划破长空，数十名修士御剑而来。（动作开头）
      → 结尾：夜色渐浓，远处传来钟声...（环境结尾，为下章铺垫）
```

**章节衔接**：
```
第5章结尾：他深吸一口气，伸手推向房门。（动作未完成）
            ↓ [衔接管理器分析：未完成动作]
            
第6章开头：生成时收到要求："上章有未完成动作，立即承接"
          → 结果：房门应声而开，一股寒气扑面而来...（立即承接）
```

---

## 进一步优化方向

### 1. 基于 LLM 的深度分析

当前的分类（醒来、对话、动作）是基于关键词匹配，不够精准。可以改为：

```python
def _classify_opening_by_llm(self, opening_text):
    """用 LLM 分类开头类型"""
    prompt = f"""
    分析以下段落的开头类型，从以下选项中选择最匹配的一个：
    1. 醒来/起床
    2. 对话
    3. 动作场面
    4. 环境描写
    5. 回忆/闪回
    6. 内心独白
    7. 其他
    
    段落：{opening_text}
    
    输出格式：类型编号
    """
    result = llm.generate(prompt)
    return self._parse_type(result)
```

### 2. 情绪曲线控制

```python
class EmotionCurveManager:
    """控制情绪曲线，避免平铺直叙"""
    
    def __init__(self):
        self.emotion_levels = []  # 1-10 分，记录每章情绪强度
    
    def suggest_emotion_level(self, chapter_num):
        """建议本章情绪强度"""
        recent = self.emotion_levels[-5:]
        
        # 如果最近5章都是低强度（≤4），建议来个高潮
        if all(e <= 4 for e in recent):
            return 8, "建议：安排高潮场景，提升情绪强度"
        
        # 如果最近一章是高强度（≥8），建议缓一缓
        if recent and recent[-1] >= 8:
            return 3, "建议：缓和节奏，给读者喘息空间"
        
        return 5, "建议：保持中等强度"
```

### 3. 伏笔回收提醒

```python
class ForeshadowingReminder:
    """提醒回收伏笔"""
    
    def __init__(self):
        self.foreshadowing = []  # [(chapter, content, resolved)]
    
    def add_foreshadowing(self, chapter_num, content):
        """记录伏笔"""
        self.foreshadowing.append({
            "chapter": chapter_num,
            "content": content,
            "resolved": False,
            "age": 0  # 已经过多少章未回收
        })
    
    def check_overdue(self, current_chapter):
        """检查是否有伏笔过期"""
        reminders = []
        for f in self.foreshadowing:
            if not f["resolved"]:
                f["age"] = current_chapter - f["chapter"]
                if f["age"] > 10:  # 超过10章未回收
                    reminders.append(
                        f"⚠️ 第{f['chapter']}章埋下的伏笔「{f['content']}」"
                        f"已{f['age']}章未回收，建议近期回收"
                    )
        return reminders
```

---

## 使用建议

### 场景 1：生成新小说

在 `novel write` 命令执行前，重置追踪器：

```bash
novel write my-novel --volume 1
# 内部会自动调用 reset_diversity_tracker()
```

### 场景 2：续写已有小说

需要先"学习"已有章节的模式：

```python
# 在 novel write 开始前
diversity_tracker = get_diversity_tracker()
for ch_num in range(1, start_chapter):
    existing_chapter = _read_file(...)
    diversity_tracker.add_chapter(ch_num, existing_chapter)

# 然后继续生成
```

### 场景 3：人工修改后重新生成

如果修改了第10章，需要重新分析：

```python
# 重新分析第10章
chapter_10 = _read_file("chapter_010.md")
diversity_tracker.add_chapter(10, chapter_10)

# 重新生成第11章（会基于新的第10章衔接）
```

---

## 总结

| 问题 | 解决方案 | 关键技术 |
|---|---|---|
| 章节同质化 | ChapterDiversityTracker | 模式记录 + 多样性约束 |
| 开头/结尾重复 | 最近3章模式统计 | Counter + 替代建议 |
| 节奏平缓 | 每3/5章强制插入高潮/互动 | 周期性约束 |
| 章节割裂 | ChapterTransitionManager | 状态提取 + 衔接桥接 |
| 时空跳跃 | 提取上章地点/时间 | 关键词匹配 |
| 动作截断 | 检测未完成动作 | "正要"/"刚要" 等标记 |
| 缺少铺垫 | 读取下章章纲生成结尾指导 | 前瞻式约束 |

这套方案将章节生成从"独立任务"变为"连续过程"，显著提升了长篇小说的可读性。
