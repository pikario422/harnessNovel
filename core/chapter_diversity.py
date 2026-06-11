# 章节多样性管理 - 避免描写同质化

import re
from collections import Counter

class ChapterDiversityTracker:
    """追踪章节的开头、结尾、场景模式，避免重复"""

    def __init__(self):
        self.opening_patterns = []  # [(chapter_num, pattern_type)]
        self.ending_patterns = []
        self.scene_types = []  # 场景类型统计

    def analyze_chapter(self, chapter_num, chapter_text):
        """分析章节模式"""
        lines = chapter_text.strip().split('\n')
        opening = '\n'.join(lines[:5])  # 前5行
        ending = '\n'.join(lines[-5:])  # 后5行

        return {
            "opening_type": self._classify_opening(opening),
            "ending_type": self._classify_ending(ending),
            "scene_type": self._classify_scene(chapter_text),
            "has_dialogue": "「" in chapter_text or """ in chapter_text,
            "has_action": self._has_action(chapter_text),
            "has_introspection": self._has_introspection(chapter_text),
        }

    def _classify_opening(self, opening):
        """分类开头类型"""
        patterns = {
            "醒来": ["醒来", "睁开眼", "苏醒", "清晨"],
            "对话": ["「", """, "道：", "说道"],
            "动作": ["冲", "飞", "走", "奔"],
            "环境": ["天空", "房间", "街道", "城市"],
            "回忆": ["想起", "回忆", "记得", "曾经"],
            "独白": ["我", "他知道", "心中"],
        }

        for pattern_type, keywords in patterns.items():
            if any(kw in opening for kw in keywords):
                return pattern_type
        return "其他"

    def _classify_ending(self, ending):
        """分类结尾类型"""
        patterns = {
            "总结": ["想到", "明白", "决定", "打算"],
            "悬念": ["突然", "竟然", "没想到", "？"],
            "对话": ["「", """, "道："],
            "动作": ["离开", "转身", "消失", "前往"],
            "环境": ["夜色", "月光", "天边", "远处"],
        }

        for pattern_type, keywords in patterns.items():
            if any(kw in ending for kw in keywords):
                return pattern_type
        return "其他"

    def _classify_scene(self, text):
        """分类场景类型"""
        if any(kw in text for kw in ["打斗", "战斗", "攻击", "出手"]):
            return "战斗"
        elif any(kw in text for kw in ["修炼", "打坐", "突破", "感悟"]):
            return "修炼"
        elif any(kw in text for kw in ["交谈", "聊天", "对话", "讨论"]):
            return "对话"
        elif any(kw in text for kw in ["探索", "前行", "寻找", "查看"]):
            return "探索"
        else:
            return "日常"

    def _has_action(self, text):
        """是否有动作场面"""
        action_words = ["冲", "飞", "打", "攻", "击", "斩", "劈"]
        return sum(text.count(w) for w in action_words) > 5

    def _has_introspection(self, text):
        """是否有内心戏"""
        thought_markers = ["心想", "想到", "暗道", "明白", "意识到"]
        return any(m in text for m in thought_markers)

    def add_chapter(self, chapter_num, chapter_text):
        """记录章节模式"""
        analysis = self.analyze_chapter(chapter_num, chapter_text)

        self.opening_patterns.append((chapter_num, analysis["opening_type"]))
        self.ending_patterns.append((chapter_num, analysis["ending_type"]))
        self.scene_types.append((chapter_num, analysis["scene_type"]))

    def get_recent_patterns(self, last_n=5):
        """获取最近N章的模式"""
        return {
            "openings": [p[1] for p in self.opening_patterns[-last_n:]],
            "endings": [p[1] for p in self.ending_patterns[-last_n:]],
            "scenes": [p[1] for p in self.scene_types[-last_n:]],
        }

    def generate_diversity_requirements(self, chapter_num):
        """生成多样性要求（用于 prompt）"""
        recent = self.get_recent_patterns(last_n=3)

        requirements = []

        # 1. 避免重复的开头
        if recent["openings"]:
            opening_counts = Counter(recent["openings"])
            most_common = opening_counts.most_common(1)[0]
            if most_common[1] >= 2:  # 最近3章有2章用同样开头
                requirements.append(f"⚠️ 避免使用「{most_common[0]}」类型的开头（最近已用{most_common[1]}次）")
                requirements.append(self._suggest_alternative_opening(most_common[0]))

        # 2. 避免重复的结尾
        if recent["endings"]:
            ending_counts = Counter(recent["endings"])
            most_common = ending_counts.most_common(1)[0]
            if most_common[1] >= 2:
                requirements.append(f"⚠️ 避免使用「{most_common[0]}」类型的结尾（最近已用{most_common[1]}次）")
                requirements.append(self._suggest_alternative_ending(most_common[0]))

        # 3. 场景多样性
        if recent["scenes"]:
            scene_counts = Counter(recent["scenes"])
            most_common = scene_counts.most_common(1)[0]
            if most_common[1] >= 3:  # 连续3章同类场景
                requirements.append(f"⚠️ 避免连续的「{most_common[0]}」场景，增加场景多样性")

        # 4. 节奏调节
        if chapter_num % 3 == 0:
            requirements.append("✓ 建议：每3章插入一个高潮场景（战斗/冲突/突破）")

        if chapter_num % 5 == 0:
            requirements.append("✓ 建议：每5章安排一次角色互动（对话/感情线）")

        return "\n".join(requirements) if requirements else "无特殊要求"

    def _suggest_alternative_opening(self, avoid_type):
        """建议替代的开头方式"""
        alternatives = {
            "醒来": "建议使用：对话开头 / 动作开头（直接进入场景）",
            "对话": "建议使用：环境描写开头 / 动作开头",
            "动作": "建议使用：独白开头 / 对话开头",
            "环境": "建议使用：动作开头 / 回忆开头",
            "回忆": "建议使用：对话开头 / 动作开头",
            "独白": "建议使用：对话开头 / 环境开头",
        }
        return alternatives.get(avoid_type, "建议尝试不同的开头方式")

    def _suggest_alternative_ending(self, avoid_type):
        """建议替代的结尾方式"""
        alternatives = {
            "总结": "建议使用：悬念结尾（留下疑问）/ 对话结尾",
            "悬念": "建议使用：动作结尾 / 环境描写结尾",
            "对话": "建议使用：动作结尾 / 总结结尾",
            "动作": "建议使用：悬念结尾 / 环境描写结尾",
            "环境": "建议使用：对话结尾 / 动作结尾",
        }
        return alternatives.get(avoid_type, "建议尝试不同的结尾方式")


# 全局实例
_global_diversity_tracker = ChapterDiversityTracker()

def get_diversity_tracker():
    return _global_diversity_tracker

def reset_diversity_tracker():
    global _global_diversity_tracker
    _global_diversity_tracker = ChapterDiversityTracker()
