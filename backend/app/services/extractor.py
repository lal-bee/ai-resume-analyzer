import re
from typing import Any, Dict, List

from app.services.llm_client import llm_client
from app.utils.text_cleaner import sectionize_text


def _first_match(pattern: str, text: str) -> str:
    match = re.search(pattern, text, re.IGNORECASE)
    return match.group(1).strip() if match else ""


def _fallback_extract(clean_text: str) -> Dict[str, Any]:
    sections = sectionize_text(clean_text)
    phone = _first_match(r"(\+?\d[\d\-\s]{8,}\d)", clean_text)
    email = _first_match(r"([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})", clean_text)
    name = _first_match(r"(?:姓名|Name)[:： ]*([^\n]{2,20})", clean_text)
    address = _first_match(r"(?:地址|现居|居住地)[:： ]*([^\n]{2,50})", clean_text)
    expected_salary = _first_match(r"(?:期望薪资|薪资)[:： ]*([^\n]{2,30})", clean_text)
    job_intention = _first_match(r"(?:求职意向|意向岗位|应聘岗位)[:： ]*([^\n]{2,40})", clean_text)
    work_years = _first_match(r"(\d{1,2}\+?\s*年(?:工作)?经验)", clean_text)

    edu_text = sections.get("教育经历", "")
    education = _first_match(r"(博士|硕士|本科|大专|中专|高中)", edu_text or clean_text)

    project_lines = []
    project_source = sections.get("项目经历", clean_text)
    for line in project_source.splitlines():
        if 4 <= len(line) <= 80 and any(k in line for k in ["项目", "系统", "平台", "App", "管理"]):
            project_lines.append(line.strip("- ").strip())
    projects: List[Dict[str, Any]] = [{"name": item, "description": ""} for item in list(dict.fromkeys(project_lines))[:5]]

    return {
        "extraction_mode": "fallback",
        "name": name,
        "phone": phone,
        "email": email,
        "address": address,
        "job_intention": job_intention,
        "expected_salary": expected_salary,
        "work_years": work_years,
        "education": education,
        "projects": projects,
    }


def _normalize_result(data: Dict[str, Any], mode: str) -> Dict[str, Any]:
    return {
        "extraction_mode": mode,
        "name": str(data.get("name", "") or ""),
        "phone": str(data.get("phone", "") or ""),
        "email": str(data.get("email", "") or ""),
        "address": str(data.get("address", "") or ""),
        "job_intention": str(data.get("job_intention", "") or ""),
        "expected_salary": str(data.get("expected_salary", "") or ""),
        "work_years": str(data.get("work_years", "") or ""),
        "education": str(data.get("education", "") or ""),
        "projects": data.get("projects", []) if isinstance(data.get("projects", []), list) else [],
    }


async def extract_resume_info(clean_text: str) -> Dict[str, Any]:
    fallback = _fallback_extract(clean_text)
    if not llm_client.enabled:
        return fallback

    system_prompt = (
        "你是简历结构化提取助手。"
        "必须只输出 JSON 对象，不要输出任何解释文本。"
        "字段必须包含：name, phone, email, address, job_intention, expected_salary, work_years, education, projects。"
        "projects 必须是数组，每项包含 name 和 description。未提取到请返回空字符串或空数组。"
    )
    user_prompt = f"请提取以下简历文本：\n{clean_text[:12000]}"
    result = await llm_client.chat_json(system_prompt, user_prompt)
    if not result:
        return fallback
    return _normalize_result(result, "llm")

