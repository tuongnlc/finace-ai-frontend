from datetime import date
from pydantic import BaseModel
from typing import Optional
from uuid import UUID


class CreateNewspaperSummaryRequest(BaseModel):
    newspaper_title: str
    newspaper_url: str
    publish_date: Optional[date] = None
    newspaper_content: str
    stocks_mention: Optional[list[str]] = None
    main_topic: Optional[list[str]] = None
    person_mention: Optional[list[str]] = None
    newspaper_summary: Optional[str] = None
    sentiment_analysis: Optional[str] = None


class CreateNewspaperSummaryResponse(BaseModel):
    newspaper_url: str

class GetNewspaperSummaryResponse(BaseModel):
    newspaper_title: str
    newspaper_url: str
    publish_date: Optional[date] = None
    newspaper_content: str
    stocks_mention: Optional[list[str]] = None
    main_topic: Optional[list[str]] = None
    person_mention: Optional[list[str]] = None
    newspaper_summary: Optional[str] = None
    sentiment_analysis: Optional[str] = None


class DeleteNewspaperSumResponse(BaseModel):
    id: UUID
    document_id: UUID

class UpdateNewspaperSummaryResponse(BaseModel):
    id: UUID
    document_id: UUID