# 章节衔接管理 - 消除割裂感

class ChapterTransitionManager:
    """管理章节间的平滑过渡"""

    def __init__(self):
        self.chapters = []  # 存储章节信息

    def analyze_chapter_end(self, chapter_text):
        """分析章节结尾状态"""
        lines = chapter_text.strip().split('\n')
        ending = '\n'.join(lines[-10:])  # 最后10行

        return {
            "location": self._extract_location(ending),
            "characters_present": self._extract_characters(ending),
            "time": self._extract_time(ending),
            "mood": self._extract_mood(ending),
            "unresolved_action": self._has_unresolved_action(ending),
            "ending_sentence": lines[-1] if lines else "",
        }

    def _extract_location(self, text):
        """提取地点"""
        # 简单匹配常见地点词
        locations = ["房间", "街道", "山顶", "洞府", "大殿", "客栈", "森林", "城市"]
        for loc in locations:
            if loc in text:
                return loc
        return "未知地点"

    def _extract_characters(self, text):
        """提取在场人物（简化版，实际需要 NER）"""
        # 这里简化处理，实际应该调用 LLM
        return ["主角"]  # placeholder

    def _extract_time(self, text):
        """提取时间"""
        if any(kw in text for kw in ["夜", "深夜", "月光", "星空"]):
            return "夜晚"
        elif any(kw in text for kw in ["晨", "清晨", "朝阳", "日出"]):
            return "清晨"
        elif any(kw in text for kw in ["午", "正午", "日头"]):
            return "正午"
        else:
            return "未明确"

    def _extract_mood(self, text):
        """提取氛围"""
        if any(kw in text for kw in ["紧张", "危险", "警惕", "小心"]):
            return "紧张"
        elif any(kw in text for kw in ["轻松", "笑", "愉快"]):
            return "轻松"
        elif any(kw in text for kw in ["悲伤", "遗憾", "叹息"]):
            return "沉重"
        else:
            return "平静"

    def _has_unresolved_action(self, text):
        """是否有未完成的动作"""
        markers = ["突然", "正要", "刚要", "准备", "即将"]
        return any(m in text for m in markers)

    def generate_transition_bridge(self, prev_chapter_end, next_chapter_outline):
        """生成过渡桥接内容"""
        prev_state = self.analyze_chapter_end(prev_chapter_end)

        bridge = f"""
【章节衔接要求】

1. 时空连续性
   - 上章结尾：{prev_state['location']} / {prev_state['time']}
   - 要求：本章开头应从相同或相邻的时空开始，避免突然跳转

2. 人物状态延续
   - 上章在场人物：{', '.join(prev_state['characters_present'])}
   - 要求：如有人物消失/新增，需说明原因

3. 情绪/氛围承接
   - 上章氛围：{prev_state['mood']}
   - 要求：开头应延续或自然转变氛围，不要突兀

4. 动作/事件衔接
   - 上章结尾句：「{prev_state['ending_sentence']}」
   - {'⚠️ 上章有未完成动作，本章应立即承接' if prev_state['unresolved_action'] else '✓ 可以自然过渡到本章内容'}

5. 过渡技巧建议
   {self._suggest_transition_technique(prev_state)}
"""
        return bridge

    def _suggest_transition_technique(self, prev_state):
        """建议过渡技巧"""
        techniques = []

        if prev_state['unresolved_action']:
            techniques.append("- 使用「立即承接」：上章刚要XXX → 本章开头紧接着XXX")
        elif prev_state['time'] == "夜晚":
            techniques.append("- 使用「时间过渡」：「一夜无话，翌日清晨...」")
        elif prev_state['mood'] == "紧张":
            techniques.append("- 使用「情绪延续」：本章开头保持紧张感，再逐渐放松")
        else:
            techniques.append("- 使用「自然过渡」：简单交代时间/地点变化即可")

        return "\n".join(techniques) if techniques else "- 自然过渡即可"

    def generate_ending_guidance(self, current_chapter_outline, next_chapter_outline):
        """生成结尾写作指导（为下一章留伏笔）"""
        guidance = f"""
【本章结尾要求】

1. 为下章铺垫
   - 下章内容：{next_chapter_outline[:100]}...
   - 要求：结尾应埋下伏笔/留下悬念/自然引导到下章内容

2. 避免「总结式」结尾
   - ❌ 不要：「XXX心中暗想，明天一定要去找YYY」（过于直白的下章预告）
   - ✓ 建议：「远处传来一声钟响，XXX抬头望向YYY方向」（含蓄引导）

3. 结尾类型选择
   - 悬念结尾：适合剧情紧张、下章有转折
   - 动作结尾：适合下章有战斗/冒险
   - 对话结尾：适合下章有重要谈判/揭秘
   - 环境结尾：适合下章有场景切换

4. 避免突然截断
   - ❌ 不要：动作进行一半突然结束
   - ✓ 建议：完成一个小节奏后自然收尾
"""
        return guidance


# 集成到正文生成流程
def generate_chapter_with_transition(ws, volume, chapter_num, llm):
    """生成章节时考虑衔接"""
    from core.chapter_diversity import get_diversity_tracker

    diversity_tracker = get_diversity_tracker()
    transition_manager = ChapterTransitionManager()

    # 1. 读取上一章正文（用于衔接）
    if chapter_num > 1:
        prev_chapter_file = f"{ws.file_system}/chapters/vol_{volume:02d}/{chapter_num-1:03d}_第{chapter_num-1}章.md"
        prev_chapter_text = _read_file(prev_chapter_file) or ""

        # 分析上章结尾
        transition_bridge = transition_manager.generate_transition_bridge(
            prev_chapter_text,
            current_chapter_outline
        )
    else:
        transition_bridge = "【第一章，无需衔接】"

    # 2. 生成多样性要求
    diversity_requirements = diversity_tracker.generate_diversity_requirements(chapter_num)

    # 3. 读取下一章章纲（用于结尾铺垫）
    next_chapter_outline_file = f"{ws.file_system}/chapter_outlines/vol_{volume:02d}/chapter_{chapter_num+1:03d}.md"
    next_chapter_outline = _read_file(next_chapter_outline_file) or "（无下章章纲）"

    ending_guidance = transition_manager.generate_ending_guidance(
        current_chapter_outline,
        next_chapter_outline
    )

    # 4. 构建完整 prompt
    enhanced_prompt = f"""
{base_prompt}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
【章节衔接要求】
{transition_bridge}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
【多样性要求】
{diversity_requirements}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
【结尾写作指导】
{ending_guidance}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
现在，请开始撰写第{chapter_num}章正文。
"""

    # 5. 生成正文
    result = llm.generate(enhanced_prompt)

    # 6. 记录本章模式（供下章参考）
    diversity_tracker.add_chapter(chapter_num, result)

    return result


def _read_file(path):
    import os
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return f.read().strip()
