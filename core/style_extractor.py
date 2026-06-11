# 写作风格提取器

class WritingStyleExtractor:
    """从参考小说中提取写作风格特征"""

    def __init__(self):
        self.style_features = {}

    def extract_from_chapters(self, chapters, llm):
        """从章节中提取写作风格"""
        # 抽样：每10章取1章，最多取20章
        sample_chapters = self._sample_chapters(chapters, max_samples=20)

        print(f">>> 正在分析写作风格（抽样 {len(sample_chapters)} 章）<<<")

        # 合并样本文本
        sample_text = "\n\n".join([ch["content"][:2000] for ch in sample_chapters])

        # 调用 LLM 提取风格
        prompt = f"""
你是一位专业的文学风格分析师。请深度分析以下小说样本的写作风格。

【样本文本】
{sample_text}

【分析维度】

请按以下结构输出（使用纯文本，不要 Markdown 符号）：

一、叙述视角与语气
- 人称：第一人称 / 第三人称全知 / 第三人称限知
- 语气：严肃 / 幽默 / 冷峻 / 轻松等
- 举例：（从原文摘录1-2句代表性句子）

二、句式特征
- 平均句长：长句为主 / 短句为主 / 长短结合
- 句式节奏：（如：多用排比、常用短句营造紧迫感等）
- 举例：（从原文摘录2-3个典型句式）

三、遣词造句习惯
- 常用词汇风格：文言色彩 / 白话直白 / 口语化 / 书面化
- 修辞偏好：（如：善用比喻、少用夸张、常用拟人等）
- 高频特色词汇：（列出5-10个作者常用的特色词）
- 举例：（从原文摘录2-3个有特色的表达）

四、对话风格
- 对话占比：多 / 适中 / 少
- 对话方式：（如：简洁直接、迂回含蓄、富含潜台词等）
- 对话标记：使用「」、用"说道"、用破折号等
- 举例：（从原文摘录2-3段对话）

五、描写密度与偏好
- 环境描写：细致入微 / 简略点到 / 很少描写
- 动作描写：详细分解 / 概括性强 / 重点描写
- 心理描写：大量内心独白 / 通过行为暗示 / 很少心理描写
- 举例：（从原文摘录1-2段代表性描写）

六、节奏控制
- 叙事节奏：快节奏（少铺垫直入主题）/ 慢节奏（大量铺垫）
- 张弛变化：（如：战斗场面快节奏，日常场景慢节奏）
- 段落切换：频繁换段 / 长段落为主

七、特色技巧
- 独特的叙事技巧：（如：常用闪回、善用伏笔、喜欢留白等）
- 情节推进方式：（如：悬念驱动、角色驱动、事件驱动）
- 作者标志性写法：（如果有明显的"作者指纹"）

八、禁忌与避免
- 不使用的表达：（如：不用"心中暗想"、避免"随着"开头等）
- 较少使用的技巧：（如：少用景物烘托气氛）

请详细分析，每个维度都要有具体的原文举例。
"""

        result = llm.generate(prompt, max_tokens=4096)
        return result

    def _sample_chapters(self, chapters, max_samples=20):
        """抽样章节"""
        total = len(chapters)
        if total <= max_samples:
            return chapters

        # 均匀抽样
        step = total // max_samples
        return [chapters[i] for i in range(0, total, step)][:max_samples]

    def extract_sentence_patterns(self, chapters, llm):
        """提取句式模板（供仿写时参考）"""
        sample_chapters = self._sample_chapters(chapters, max_samples=10)
        sample_text = "\n\n".join([ch["content"][:1500] for ch in sample_chapters])

        print(f">>> 正在提取句式模板 <<<")

        prompt = f"""
从以下小说样本中提取20个有特色的句式模板。

【样本文本】
{sample_text}

【要求】
1. 提取具有作者风格的典型句式
2. 将具体内容替换为变量占位符
3. 每个模板标注适用场景

【输出格式】
场景：动作描写
模板：[人物][动作]，[身形/方向][移动]，[瞬间/眨眼间][到达位置]
原句：李逍遥身形一闪，御剑而起，瞬间出现在百丈之外

场景：心理描写
模板：[人物]心中[情绪]，暗道：[内心OS]
原句：他心中一惊，暗道：此人竟有如此修为

...（继续输出剩余模板）
"""

        result = llm.generate(prompt, max_tokens=3096)
        return result

    def generate_style_guide(self, ws, chapters, llm):
        """生成完整的风格指南（保存为 STYLE_GUIDE.md）"""
        print("\n>>> 生成写作风格指南 <<<")

        # 1. 风格特征分析
        style_analysis = self.extract_from_chapters(chapters, llm)

        # 2. 句式模板提取
        sentence_patterns = self.extract_sentence_patterns(chapters, llm)

        # 3. 组装风格指南
        style_guide = f"""# 参考小说写作风格指南

本文档由 AI 自动分析参考小说生成，用于指导新小说的写作风格。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## 风格特征分析

{style_analysis}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## 句式模板库

{sentence_patterns}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## 使用说明

1. **仿写时参考**：生成每章正文时，将本风格指南作为上下文传入
2. **句式借鉴**：遇到相同场景时，可参考对应的句式模板
3. **禁忌避免**：严格遵守"禁忌与避免"部分的规则
4. **灵活运用**：不要机械套用，保持创作的自然流畅

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
生成时间：{self._get_timestamp()}
"""

        # 4. 保存
        output_path = f"{ws.file_system}/STYLE_GUIDE.md"
        self._write_file(output_path, style_guide)
        print(f"  -> 风格指南已保存：{output_path}")

        return style_guide

    def _get_timestamp(self):
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def _write_file(self, path, content):
        import os
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)


# 集成到拆书流程
def integrate_style_extraction(ws, chapters, llm):
    """在拆书阶段集成风格提取"""
    extractor = WritingStyleExtractor()

    # 生成风格指南
    style_guide = extractor.generate_style_guide(ws, chapters, llm)

    return style_guide
