from fastapi import APIRouter, File, HTTPException, UploadFile

from app.schemas import MatchRequest, MatchResponse, ParseResponse
from app.services.cache_service import cache_service
from app.services.extractor import extract_resume_info
from app.services.matcher import match_resume_with_job
from app.utils.hash_util import sha256_bytes, sha256_text
from app.utils.pdf_parser import parse_pdf_text
from app.utils.text_cleaner import clean_text

router = APIRouter()


@router.get("/health")
async def health():
    return {"status": "ok"}


@router.post("/api/resumes/parse", response_model=ParseResponse)
async def parse_resume(file: UploadFile = File(...)):
    filename = file.filename or ""
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="仅支持 PDF 文件上传。")

    pdf_bytes = await file.read()
    if not pdf_bytes:
        raise HTTPException(status_code=400, detail="上传文件为空。")

    file_hash = sha256_bytes(pdf_bytes)
    cache_key = f"resume:parse:{file_hash}"
    cached = await cache_service.get_json(cache_key)
    if cached:
        return {**cached, "from_cache": True}

    try:
        raw_text = parse_pdf_text(pdf_bytes)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"PDF 解析失败：{exc}") from exc

    if len(raw_text.strip()) < 20:
        raise HTTPException(
            status_code=422,
            detail="PDF 可提取文本过少，请确认文件是否为图片型扫描件或内容为空。",
        )

    cleaned = clean_text(raw_text)
    parsed_info = await extract_resume_info(cleaned)
    resume_id = cache_service.upsert_resume(
        file_hash,
        {"raw_text": raw_text, "clean_text": cleaned, "parsed_info": parsed_info},
    )

    response = {
        "resume_id": resume_id,
        "raw_text": raw_text,
        "clean_text": cleaned,
        "parsed_info": parsed_info,
        "from_cache": False,
    }
    await cache_service.set_json(cache_key, response)
    return response


@router.post("/api/resumes/match", response_model=MatchResponse)
async def match_resume(payload: MatchRequest):
    resume_data = cache_service.get_resume(payload.resume_id)
    if not resume_data:
        raise HTTPException(status_code=404, detail="未找到该 resume_id，请先调用解析接口。")

    jd_hash = sha256_text(payload.job_description)
    cache_key = f"resume:match:{payload.resume_id}:{jd_hash}"
    cached = await cache_service.get_json(cache_key)
    if cached:
        return {**cached, "from_cache": True}

    result = await match_resume_with_job(
        parsed_info=resume_data["parsed_info"],
        clean_text=resume_data["clean_text"],
        job_description=payload.job_description,
    )
    response = {"resume_id": payload.resume_id, **result, "from_cache": False}
    await cache_service.set_json(cache_key, response)
    return response

