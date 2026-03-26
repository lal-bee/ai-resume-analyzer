import re
from typing import Dict


SECTION_HINTS = [
    "教育经历",
    "项目经历",
    "工作经历",
    "技能",
    "专业技能",
    "自我评价",
    "实习经历",
]


def clean_text(text: str) -> str:
    cleaned = text.replace("\u3000", " ")
    cleaned = re.sub(r"[ \t]+", " ", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    cleaned = re.sub(r"[•·●▪◦]+", "-", cleaned)
    cleaned = re.sub(r"[^\S\r\n]+\n", "\n", cleaned)
    return cleaned.strip()


def sectionize_text(text: str) -> Dict[str, str]:
    sections: Dict[str, str] = {}
    current = "其他"
    bucket = []

    lines = [line.strip() for line in text.splitlines()]
    for line in lines:
        if not line:
            continue
        target = next((hint for hint in SECTION_HINTS if hint in line), None)
        if target:
            if bucket:
                sections[current] = (sections.get(current, "") + "\n" + "\n".join(bucket)).strip()
                bucket = []
            current = target
            continue
        bucket.append(line)

    if bucket:
        sections[current] = (sections.get(current, "") + "\n" + "\n".join(bucket)).strip()
    return sections

