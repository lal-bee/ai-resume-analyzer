from typing import Any, Dict, List

from pydantic import BaseModel, Field


class ParseInfo(BaseModel):
    extraction_mode: str = "fallback"
    name: str = ""
    phone: str = ""
    email: str = ""
    address: str = ""
    job_intention: str = ""
    expected_salary: str = ""
    work_years: str = ""
    education: str = ""
    projects: List[Dict[str, Any]] = Field(default_factory=list)


class ParseResponse(BaseModel):
    resume_id: str
    raw_text: str
    clean_text: str
    parsed_info: ParseInfo
    from_cache: bool


class MatchRequest(BaseModel):
    resume_id: str = Field(min_length=1, max_length=128)
    job_description: str = Field(min_length=10, max_length=20000)


class MatchResponse(BaseModel):
    resume_id: str
    job_keywords: List[str]
    matched_keywords: List[str]
    missing_keywords: List[str]
    dimension_scores: Dict[str, float]
    match_score: float
    ai_summary: str
    from_cache: bool

