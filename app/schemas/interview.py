import uuid
from datetime import date, time
from typing import List, Optional, Literal

from fastapi.params import Query
from pydantic import BaseModel


class InterviewCreate(BaseModel):
    job_application_id: uuid.UUID
    format: Optional[Literal[
        "phone", "video", "onsite", "technical", "system design", "behavioural", "case study", "pair programming", "panel"]]
    date: Optional[str]
    time: Optional[str]
    round: Optional[int]
    notes: Optional[str] = None
    estimated_duration: Optional[str] = None
    actual_duration: Optional[str] = None
    timezone: Optional[str] = None
    interviewer_name: Optional[str] = None


class InterviewUpdate(BaseModel):
    format: Optional[Literal[
        "phone", "video", "onsite", "technical", "system design", "behavioural", "case study", "pair programming", "panel"]] = None
    outcome: Optional[
        Literal["scheduled", "pending", "passed", "rejected", "waiting", "withdrawn", "no feedback"]] = None
    date: Optional[str] = None
    time: Optional[str] = None
    round: Optional[int] = None
    notes: Optional[str] = None
    estimated_duration: Optional[str] = None
    actual_duration: Optional[str] = None
    timezone: Optional[str] = None
    interviewer_name: Optional[str] = None
    feedback: Optional[str] = None


class InterviewDetail(BaseModel):
    id: uuid.UUID
    format: Optional[Literal[
        "phone", "video", "onsite", "technical", "system design", "behavioural", "case study", "pair programming", "panel"]]
    outcome: Optional[Literal["pending", "scheduled", "passed", "rejected", "withdrawn", "no feedback"]]
    date: Optional[date]
    time: Optional[time]
    round: Optional[int]
    notes: Optional[str]
    estimated_duration: Optional[str]
    actual_duration: Optional[str]
    timezone: Optional[str]
    interviewer_name: Optional[str]
    feedback: Optional[str]


class InterviewDetailShort(BaseModel):
    id: uuid.UUID
    format: Optional[Literal[
        "phone", "video", "onsite", "technical", "system design", "behavioural", "case study", "pair programming", "panel"]]
    outcome: Optional[Literal["pending", "scheduled", "passed", "rejected", "withdrawn", "no feedback"]]
    round: int
    date: Optional[date]
    time: Optional[time]


class InterviewList(BaseModel):
    data: List[InterviewDetail] = []


class InterviewJoin(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    company_name: str
    job_title: str
    format: str
    round: int
    outcome: Optional[str]
    date: date
    time: time


class InterviewJoinList(BaseModel):
    data: List[InterviewJoin] = []
    next_cursor: Optional[str] = None


class InterviewFilterParams:
    def __init__(
            self,
            format: Optional[str] = None,
            outcome: Optional[str] = None,
            round: Optional[int] = None,
            start_date: Optional[date] = Query(None, description="Filter from this date (YYYY-MM-DD)"),
            end_date: Optional[date] = Query(None, description="Filter until this date (YYYY-MM-DD)"),
            start_time: Optional[time] = Query(None, description="Filter from this time (HH:MM:SS)"),
            end_time: Optional[time] = Query(None, description="Filter until this time (HH:MM:SS)"),
            q: Optional[str] = Query(None, min_length=3, description="Search term"),
            sort_by: str = Query("created_at", pattern="^(created_at|format|outcome|date)$"),
            order: str = Query("asc", pattern="^(asc|desc)$")
    ):
        self.format = format
        self.outcome = outcome
        self.round = round
        self.start_date = start_date
        self.end_date = end_date
        self.start_time = start_time
        self.end_time = end_time
        self.sort_by = sort_by
        self.order = order
        self.q = q
