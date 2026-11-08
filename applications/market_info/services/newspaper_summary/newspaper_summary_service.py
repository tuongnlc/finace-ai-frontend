from __future__ import annotations

from datetime import date
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel

from applications.market_info.integrations.newspaper_summary.newspaper_summary_client import NewspaperSummaryClient

from applications.schemas.newspaper_summary import DeleteNewspaperSumResponse


class NewspaperSummary(BaseModel):
    newspaper_title: str
    newspaper_url: str
    publish_date: Optional[date] = None
    newspaper_content: str
    stocks_mention: Optional[list[str]] = None
    main_topic: Optional[list[str]] = None
    person_mention: Optional[list[str]] = None
    newspaper_summary: Optional[str] = None
    sentiment_analysis: Optional[str] = None


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
                newspaper_title=item.newspaper_title,
                newspaper_url=item.newspaper_url,
                publish_date=item.publish_date,
                newspaper_content=item.newspaper_content,
                stocks_mention=item.stocks_mention,
                main_topic=item.main_topic,
                person_mention=item.person_mention,
                newspaper_summary=item.newspaper_summary,
                sentiment_analysis=item.sentiment_analysis,
            )
            for item in response
        ]

    def delete_summaries(self, newspaper_url: str) -> DeleteNewspaperSumResponse | None:
        return self.client.delete_summaries(newspaper_url)
