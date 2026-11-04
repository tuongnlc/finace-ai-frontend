from datetime import date
from pydantic import BaseModel
from typing import Optional
from uuid import UUID


class CreateNewspaperSummaryRequest(BaseModel):
    id: UUID
    document_id: UUID
    newspaper_summary: str
    publish_date: Optional[date] = None
    stocks_mention: Optional[str] = None
    person_mention: Optional[str] = None
    newspaper_type: Optional[str] = None
    sentiment_analysis: Optional[str] = None
    circular_and_policy: Optional[str] = None
    legal_documents_and_regulations: Optional[str] = None
    fund_name: Optional[str] = None
    main_topic: Optional[str] = None
    is_favorite: Optional[int] = None


class CreateNewspaperSummaryResponse(BaseModel):
    id: UUID
    document_id: UUID

class GetNewspaperSummaryResponse(BaseModel):
    id: UUID
    document_id: UUID
    newspaper_summary: str
    publish_date: Optional[date] = None
    stocks_mention: Optional[str] = None
    person_mention: Optional[str] = None
    newspaper_type: Optional[str] = None
    sentiment_analysis: Optional[str] = None
    circular_and_policy: Optional[str] = None
    legal_documents_and_regulations: Optional[str] = None
    fund_name: Optional[str] = None
    main_topic: Optional[str] = None
    is_favorite: Optional[int] = None


class DeleteNewspaperSumResponse(BaseModel):
    id: UUID
    document_id: UUID

class UpdateNewspaperSummaryResponse(BaseModel):
    id: UUID
    document_id: UUID