import json
import uuid
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.logging_config import logger
from app.core.redis import redis_manager
from app.models.job_application import JobApplication, JobApplicationStatusHistory, Interview
import pandas as pd
import numpy as np
from datetime import datetime


def custom_serializer(obj):
    if isinstance(obj, uuid.UUID):
        return str(obj)
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")


async def retrieve_applications_with_status_history_from_db(db: Session, user_id: str):
    key = f"job_applications_status_history:{user_id}"
    redis_key = f"{key}:lock"
    data = await redis_manager.get_value(redis_key)
    if data:
        result = json.loads(data)
        return result
    else:
        stmt = select(
            JobApplication.id.label("job_id"),
            JobApplication.user_id.label("user_id"),
            JobApplication.job_title.label("job_title"),
            JobApplication.source.label("source"),
            JobApplication.status,
            JobApplicationStatusHistory.id.label("history_id"),
            JobApplicationStatusHistory.job_application_id,
            JobApplicationStatusHistory.from_status,
            JobApplicationStatusHistory.to_status,
            JobApplicationStatusHistory.created_at
        ).outerjoin(
            JobApplicationStatusHistory,
            JobApplication.id == JobApplicationStatusHistory.job_application_id
        ).where(
            JobApplication.user_id == user_id
        ).distinct()

        job_application_rows = db.execute(stmt).all()
        job_application_rows_dict = [dict(row._asdict()) for row in job_application_rows]
        job_application_json_str = json.dumps(job_application_rows_dict, indent=4, default=custom_serializer)
        await redis_manager.set_value(redis_key, job_application_json_str, 86400)
        return job_application_rows_dict


async def retrieve_user_interviews(db: Session, user_id: str):
    key = f"user_interviews:{user_id}"
    redis_key = f"{key}:lock"
    data = await redis_manager.get_value(redis_key)
    if data:
        result = json.loads(data)
        return result
    else:
        interview_stmt = select(
            JobApplication.id.label("job_id"),
            JobApplication.user_id.label("user_id"),
            Interview.id.label("interview_id"),
            Interview.job_application_id,
            Interview.outcome
        ).join(
            Interview,
            JobApplication.id == Interview.job_application_id
        ).where(
            JobApplication.user_id == user_id
        ).distinct()

        interviews_rows = db.execute(interview_stmt).all()
        interviews_rows_dict = [dict(row._asdict()) for row in interviews_rows]
        interviews_json_str = json.dumps(interviews_rows_dict, indent=4, default=custom_serializer)
        await redis_manager.set_value(redis_key, interviews_json_str, 86400)
        return interviews_rows_dict


def process_job_application_data(job_applications):
    job_df = pd.DataFrame(job_applications)
    job_df.drop_duplicates(subset=['job_id', 'history_id'], keep='first', inplace=True)
    job_df['created_at'] = pd.to_datetime(job_df['created_at'])

    applied_job_df = job_df[job_df['to_status'] == 'applied']
    applied_job_df.drop_duplicates(subset=['job_id'], keep='first', inplace=True)
    applied_count = len(applied_job_df)

    screened_job_df = job_df[job_df['to_status'] == 'screening']
    screened_job_df.drop_duplicates(subset=['job_id'], keep='first', inplace=True)
    screened_count = len(screened_job_df)

    interviewed_job_df = job_df[job_df['to_status'] == 'interviewing']
    interviewed_job_df.drop_duplicates(subset=['job_id'], keep='first', inplace=True)
    interviewed_count = len(interviewed_job_df)

    offer_received_job_df = job_df[job_df['to_status'] == 'offer']
    offer_received_job_df.drop_duplicates(subset=['job_id'], keep='first', inplace=True)
    offers_count = len(offer_received_job_df)

    responded_job_df = job_df[job_df['to_status'].isin(['screening', 'assessment', 'interviewing'])]
    responded_job_df.drop_duplicates(subset=['job_id'], keep='first', inplace=True)
    response_count = len(responded_job_df)

    accepted_job_df = job_df[job_df['to_status'] == 'accepted']
    accepted_job_df.drop_duplicates(subset=['job_id'], keep='first', inplace=True)
    accepted_count = len(accepted_job_df)

    applied_to_screening_rate = (screened_count / applied_count) * 100 if applied_count > 0 else 0
    screening_to_interview_rate = (interviewed_count / screened_count) * 100 if screened_count > 0 else 0
    interviewed_to_offer_rate = (offers_count / interviewed_count) * 100 if interviewed_count > 0 else 0
    offer_to_accepted_rate = (accepted_count / offers_count) * 100 if offers_count > 0 else 0
    response_rate = (response_count / applied_count) * 100 if applied_count > 0 else 0
    return {
        "applied_count": applied_count,
        "screened_count": screened_count,
        "interviewed_count": interviewed_count,
        "offers_count": offers_count,
        "response_count": response_count,
        "accepted_count": accepted_count,
        "applied_to_screening_rate": round(applied_to_screening_rate, 2),
        "screening_to_interview_rate": round(screening_to_interview_rate, 2),
        "interviewed_to_offer_rate": round(interviewed_to_offer_rate, 2),
        "offer_to_accepted_rate": round(offer_to_accepted_rate, 2),
        "response_rate": round(response_rate, 2)
    }

async def application_funnel(db: Session, user_id: str):
    try:
        job_applications = await retrieve_applications_with_status_history_from_db(db, user_id)
        result = process_job_application_data(job_applications)
        interviews = await retrieve_user_interviews(db, user_id)
        interviews_df = pd.DataFrame(interviews)
        completed_interviews_df = interviews_df[interviews_df['outcome'].isin(['passed', 'rejected'])]
        completed_interviews_count = len(completed_interviews_df)
        interview_to_offer_rate = (result['offers_count'] / completed_interviews_count) * 100 \
            if completed_interviews_count > 0 else 0

        return {
            "count_applications_sent": result['applied_count'],
            "count_offers_received": result['offers_count'],
            "count_responses": result["response_count"],
            "count_completed_interviews": completed_interviews_count,
            "response_rate": result["response_rate"],
            "interview_to_offer_rate": interview_to_offer_rate,
            "applied_to_screening": {
                "applied_count": result["applied_count"],
                "screened_count": result["screened_count"],
                "rate": f"{result['applied_to_screening_rate']}% of applied job applications"
            },
            "screening_to_interview": {
                "interviewed_count": result["interviewed_count"],
                "rate": f"{result['screening_to_interview_rate']}% of screened job applications"
            },
            "interview_to_offer": {
                "offers_count": result["offers_count"],
                "rate": f"{result['interviewed_to_offer_rate']}% of interviewed job applications"
            },
            "offer_to_accepted": {
                "accepted_count": result["accepted_count"],
                "rate": f"{result['offer_to_accepted_rate']}% of offer received job applications"
            }

        }
    except Exception as error:
        logger.error(error)
        raise Exception(str(error))


async def time_in_stage_analytics(db: Session, user_id: str):
    try:
        job_applications = await retrieve_applications_with_status_history_from_db(db, user_id)
        job_df = pd.DataFrame(job_applications)
        job_df.drop_duplicates(subset=['job_id', 'history_id'], keep='first', inplace=True)
        job_df['created_at'] = pd.to_datetime(job_df['created_at'])
        applied_job_df = job_df[job_df['to_status'] == 'applied']
        screened_job_df = job_df[job_df['to_status'] == 'screening']
        applied_to_screening_job_df = pd.merge(applied_job_df[['job_id', 'from_status', 'to_status', 'created_at']],
                                               screened_job_df[['job_id', 'from_status', 'to_status', 'created_at']],
                                               on='job_id', how='inner')
        applied_to_screening_job_df['time_in_days'] = (
                applied_to_screening_job_df['created_at_y'] - applied_to_screening_job_df['created_at_x']).dt.days
        avg_time_applied_to_screening = applied_to_screening_job_df['time_in_days'].mean() \
            if not applied_to_screening_job_df.empty else 0

        interview_job_df = job_df[job_df['to_status'] == 'interviewing']
        screening_to_interview_job_df = pd.merge(screened_job_df[['job_id', 'from_status', 'to_status', 'created_at']],
                                                 interview_job_df[['job_id', 'from_status', 'to_status', 'created_at']],
                                                 on='job_id', how='inner')
        screening_to_interview_job_df['time_in_days'] = (
                screening_to_interview_job_df['created_at_y'] - screening_to_interview_job_df['created_at_x']).dt.days
        avg_time_screening_to_interview = screening_to_interview_job_df['time_in_days'].mean() \
            if not screening_to_interview_job_df.empty else 0

        offer_job_df = job_df[job_df['to_status'] == 'offer']
        interview_to_offer_job_df = pd.merge(interview_job_df[['job_id', 'from_status', 'to_status', 'created_at']],
                                             offer_job_df[['job_id', 'from_status', 'to_status', 'created_at']],
                                             on='job_id', how='inner')
        interview_to_offer_job_df['time_in_days'] = (
                interview_to_offer_job_df['created_at_y'] - interview_to_offer_job_df['created_at_x']).dt.days

        avg_time_interview_to_offer = interview_to_offer_job_df['time_in_days'].mean() \
            if not interview_to_offer_job_df.empty else 0
        return {
            "average_time_applied_to_screening": round(avg_time_applied_to_screening, 2),
            "average_time_screening_to_interview": round(avg_time_screening_to_interview, 2),
            "average_time_interview_to_offer": round(avg_time_interview_to_offer, 2)
        }
    except Exception as error:
        logger.error(error)
        Exception(str(error))


async def source_analytics(db: Session, user_id: str):
    try:
        job_applications = await retrieve_applications_with_status_history_from_db(db, user_id)
        job_df = pd.DataFrame(job_applications)
        unique_sources = list(job_df['source'].drop_duplicates())
        data = {}
        for source in unique_sources:
            source_df = job_df[job_df['source'] == source]
            source_data = source_df.to_dict('records')
            results = process_job_application_data(source_data)
            data[source] = results
        return data
    except Exception as error:
        logger.error(error)
        raise Exception(str(error))


async def role_analytics(db: Session, user_id: str):
    try:
        job_applications = await retrieve_applications_with_status_history_from_db(db, user_id)
        job_df = pd.DataFrame(job_applications)
        unique_job_titles = list(job_df['job_title'].drop_duplicates())
        data = {}
        for job_title in unique_job_titles:
            job_title_df = job_df[job_df['job_title'] == job_title]
            job_title_data = job_title_df.to_dict('records')
            results = process_job_application_data(job_title_data)
            data[job_title] = results
        return data
    except Exception as error:
        logger.error(error)
        raise Exception(str(error))