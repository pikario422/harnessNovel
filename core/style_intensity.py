# 风格强度控制模块

import os
import json

class StyleIntensityController:
    """控制写作风格的保留程度（0-100%）"""

    DEFAULT_INTENSITY = 80  # 默认保留80%参考风格

    def __init__(self, ws):
        self.ws = ws
        self.config_path = ws.style_config
        self.config = self._load_config()

    def _load_config(self):
        """加载风格配置"""
        if os.path.exists(self.config_path):
            with open(self.config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {
            "style_intensity": self.DEFAULT_INTENSITY,
            "flexible_aspects": [],  # 允许灵活处理的方面
            "strict_aspects": [],     # 必须严格遵循的方面
        }

    def save_config(self):
        """保存配置"""
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(self.config, f, ensure_ascii=False, indent=2)

    def set_intensity(self, intensity):
        """设置风格强度（0-100）"""
        if not 0 <= intensity <= 100:
            raise ValueError("风格强度必须在 0-100 之间")

        self.config["style_intensity"] = intensity
        self.save_config()
        print(f"  -> 风格保留度已设置为 {intensity}%")

    def set_flexible_aspects(self, aspects):
        """设置允许灵活处理的方面"""
        valid_aspects = [
            "对话风格",   # 可以更现代化
            "句式节奏",   # 可以调整长短
            "描写密度",   # 可以增减描写
            "叙述视角",   # 可以改变人称
        ]

        invalid = [a for a in aspects if a not in valid_aspects]
        if invalid:
            print(f"⚠️ 无效的方面：{invalid}")
            print(f"有效选项：{valid_aspects}")
            return

        self.config["flexible_aspects"] = aspects
        self.save_config()
        print(f"  -> 灵活处理方面：{', '.join(aspects)}")

    def set_strict_aspects(self, aspects):
        """设置必须严格遵循的方面"""
        valid_aspects = [
            "禁忌词汇",   # 必须避免
            "对话标记",   # 如「」符号
            "人称视角",   # 第一/三人称
            "叙事节奏",   # 快/慢节奏
        ]

        invalid = [a for a in aspects if a not in valid_aspects]
        if invalid:
            print(f"⚠️ 无效的方面：{invalid}")
            print(f"有效选项：{valid_aspects}")
            return

        self.config["strict_aspects"] = aspects
        self.save_config()
        print(f"  -> 严格遵循方面：{', '.join(aspects)}")

    def generate_style_instruction(self, base_style_guide):
        """根据强度生成风格指令"""
        intensity = self.config["style_intensity"]
        flexible = self.config.get("flexible_aspects", [])
        strict = self.config.get("strict_aspects", [])

        # 强度分级
        if intensity >= 90:
            level = "极高"
            instruction = "必须严格遵循参考小说的所有风格特征，不允许任何偏离。"
        elif intensity >= 70:
            level = "高"
            instruction = "应该保持参考小说的主要风格特征，允许少量创新。"
        elif intensity >= 50:
            level = "中等"
            instruction = "在保留参考小说风格基础上，可以适度融入新元素。"
        elif intensity >= 30:
            level = "低"
            instruction = "仅保留参考小说的核心风格，其他方面可以自由发挥。"
        else:
            level = "极低"
            instruction = "参考小说风格仅供借鉴，可以大胆创新。"

        # 构建指令
        style_instruction = f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
【写作风格控制】

风格保留度：{intensity}%（{level}）

{instruction}

"""

        # 添加灵活处理说明
        if flexible:
            style_instruction += f"""
【允许灵活处理的方面】
{self._format_aspects(flexible, base_style_guide)}

"""

        # 添加严格遵循说明
        if strict:
            style_instruction += f"""
【必须严格遵循的方面】
{self._format_aspects(strict, base_style_guide)}

"""

        # 根据强度调整风格指南
        if intensity < 100:
            style_instruction += f"""
【创新空间】（{100 - intensity}%）
在不违背上述要求的前提下，可以：
"""
            if intensity < 70:
                style_instruction += "- 尝试不同的句式结构\n"
            if intensity < 50:
                style_instruction += "- 调整对话风格以适应现代读者\n"
            if intensity < 30:
                style_instruction += "- 增加或减少描写密度\n"

        style_instruction += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"

        return style_instruction

    def _format_aspects(self, aspects, base_style_guide):
        """从风格指南中提取对应方面的内容"""
        result = []

        mapping = {
            "对话风格": "四、对话风格",
            "句式节奏": "二、句式特征",
            "描写密度": "五、描写密度与偏好",
            "叙述视角": "一、叙述视角与语气",
            "禁忌词汇": "八、禁忌与避免",
            "对话标记": "四、对话风格",
            "人称视角": "一、叙述视角与语气",
            "叙事节奏": "六、节奏控制",
        }

        for aspect in aspects:
            section_title = mapping.get(aspect)
            if section_title:
                # 从风格指南中提取对应章节（简化实现）
                if section_title in base_style_guide:
                    result.append(f"- {aspect}：参考风格指南「{section_title}」部分")
                else:
                    result.append(f"- {aspect}")
            else:
                result.append(f"- {aspect}")

        return "\n".join(result) if result else "（无）"


def apply_style_with_intensity(ws, base_style_guide):
    """应用带强度控制的风格指南"""
    controller = StyleIntensityController(ws)

    # 生成风格指令
    style_instruction = controller.generate_style_instruction(base_style_guide)

    # 合并到完整指南
    full_guide = f"""
{style_instruction}

{base_style_guide}
"""

    return full_guide
