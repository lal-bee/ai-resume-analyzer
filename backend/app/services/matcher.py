import re
from typing import Any, Dict, List, Set, Tuple

from app.services.llm_client import llm_client

STOPWORDS = {
    "负责",
    "熟悉",
    "参与",
    "以上",
    "优先",
    "相关",
    "岗位",
    "能力",
    "经验",
    "工作",
    "开发",
    "进行",
    "以及",
    "我们",
    "公司",
    "职位",
    "and",
    "with",
    "for",
    "the",
    "you",
}


def _tokenize(text: str) -> List[str]:
    raw = re.findall(r"[A-Za-z][A-Za-z0-9+#.\-]{1,}|[\u4e00-\u9fff]{2,8}", text)
    tokens = [t.lower() for t in raw if t.lower() not in STOPWORDS]
    return list(dict.fromkeys(tokens))


def extract_job_keywords(job_description: str) -> List[str]:
    tokens = _tokenize(job_description)
    return tokens[:40]


def _parse_years(text: str) -> int:
    match = re.search(r"(\d{1,2})\+?\s*年", text)
    return int(match.group(1)) if match else 0


def _education_rank(text: str) -> int:
    text = text.lower()
    if "博士" in text or "phd" in text:
        return 4
    if "硕士" in text or "master" in text:
        return 3
    if "本科" in text or "bachelor" in text:
        return 2
    if "大专" in text or "专科" in text:
        return 1
    return 0


def _education_required(job_description: str) -> int:
    return _education_rank(job_description)


def _build_resume_keyword_pool(parsed_info: Dict[str, Any], clean_text: str) -> Set[str]:
    text_blocks = [
        parsed_info.get("job_intention", ""),
        parsed_info.get("education", ""),
        parsed_info.get("work_years", ""),
        clean_text,
    ]
    for item in parsed_info.get("projects", []):
        if isinstance(item, dict):
            text_blocks.append(item.get("name", ""))
            text_blocks.append(item.get("description", ""))
    return set(_tokenize("\n".join([str(x) for x in text_blocks if x])))


async def _generate_ai_summary(
    match_score: float,
    matched_keywords: List[str],
    missing_keywords: List[str],
    parsed_info: Dict[str, Any],
) -> Tuple[str, float]:
    default_summary = (
        f"规则评分结果为 {match_score:.1f} 分。"
        f"命中关键词 {len(matched_keywords)} 个，缺失关键词 {len(missing_keywords)} 个。"
    )
    if not llm_client.enabled:
        return default_summary, 0.0

    system_prompt = (
        "你是招聘匹配分析助手。"
        "请只输出 JSON：{\"summary\":\"...\",\"score_adjustment\":number}。"
        "score_adjustment 取值范围 -5 到 5。"
    )
    user_prompt = (
        f"规则分: {match_score}\n"
        f"命中关键词: {matched_keywords[:20]}\n"
        f"缺失关键词: {missing_keywords[:20]}\n"
        f"简历关键信息: {parsed_info}"
    )
    result = await llm_client.chat_json(system_prompt, user_prompt)
    if not result:
        return default_summary, 0.0

    summary = str(result.get("summary", default_summary))
    adjustment = float(result.get("score_adjustment", 0))
    adjustment = max(-5.0, min(5.0, adjustment))
    return summary, adjustment


async def match_resume_with_job(
    parsed_info: Dict[str, Any], clean_text: str, job_description: str
) -> Dict[str, Any]:
    job_keywords = extract_job_keywords(job_description)
    resume_keywords = _build_resume_keyword_pool(parsed_info, clean_text)
    matched_keywords = [k for k in job_keywords if k in resume_keywords]
    missing_keywords = [k for k in job_keywords if k not in resume_keywords]

    skill_ratio = (len(matched_keywords) / len(job_keywords)) if job_keywords else 0.0
    skill_match = round(skill_ratio * 100, 2)

    resume_years = _parse_years(parsed_info.get("work_years", ""))
    required_years = _parse_years(job_description)
    if required_years == 0:
        experience_relevance = 70.0 if resume_years > 0 else 50.0
    else:
        experience_relevance = min(100.0, round((resume_years / required_years) * 100, 2))

    resume_edu = _education_rank(parsed_info.get("education", ""))
    required_edu = _education_required(job_description)
    if required_edu == 0:
        education_match = 70.0 if resume_edu > 0 else 50.0
    else:
        education_match = 100.0 if resume_edu >= required_edu else 40.0

    base_score = round(skill_match * 0.5 + experience_relevance * 0.3 + education_match * 0.2, 2)
    ai_summary, score_adjustment = await _generate_ai_summary(
        base_score, matched_keywords, missing_keywords, parsed_info
    )
    final_score = max(0.0, min(100.0, round(base_score + score_adjustment, 2)))

    return {
        "job_keywords": job_keywords,
        "matched_keywords": matched_keywords,
        "missing_keywords": missing_keywords,
        "dimension_scores": {
            "skill_match": round(skill_match, 2),
            "experience_relevance": round(experience_relevance, 2),
            "education_match": round(education_match, 2),
        },
        "match_score": final_score,
        "ai_summary": ai_summary,
    }

