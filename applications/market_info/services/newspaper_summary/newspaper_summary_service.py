from __future__ import annotations

from datetime import date
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel

from applications.market_info.integrations.newspaper_summary.newspaper_summary_client import NewspaperSummaryClient

# from ai_engineer.applications.topic_summary.backend.schemas.newspaper_summary import DeleteNewspaperSumResponse


class NewspaperSummary(BaseModel):
    summary_id: UUID
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


class NewspaperSummaryService:
    def __init__(self, client = None):
        if client is None:
            client = NewspaperSummaryClient()
        self.client = client

    def list_summaries(
        self,
        min_date: Optional[date] = None,
        max_date: Optional[date] = None,
    ) -> List[NewspaperSummary]:
        response = self.client.list_summaries(min_date, max_date)

        return [
            NewspaperSummary(
                summary_id=item.id,
                document_id=item.document_id,
                newspaper_summary=item.newspaper_summary,
                publish_date=item.publish_date,
                stocks_mention=item.stocks_mention,
                person_mention=item.person_mention,
                newspaper_type=item.newspaper_type,
                sentiment_analysis=item.sentiment_analysis,
                circular_and_policy=item.circular_and_policy,
                legal_documents_and_regulations=item.legal_documents_and_regulations,
                fund_name=item.fund_name,
                main_topic=item.main_topic,
                is_favorite=item.is_favorite,
            )
            for item in response
        ]

    # def delete_summaries(self, summary_id: str) -> DeleteNewspaperSumResponse | None:
    #     return self.client.delete_summaries(summary_id)

    # def add_to_favorite(self, summary_id: str) -> None:
    #     return self.client.add_to_favorite(summary_id)