import json
import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.logging_config import logger
from app.core.redis import redis_manager
from app.models.job_application import JobApplication, JobApplicationStatusHistory, Interview, JobTask, TaskType, \
    TaskStatus
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, date, time


def custom_serializer(obj):
    if isinstance(obj, uuid.UUID):
        return str(obj)
    if isinstance(obj, (date, datetime, time)):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")


def process_job_application_data(job_applications) -> dict[str, Any]:
    job_df = pd.DataFrame(job_applications)
    stats = {
        "applied_count": 0,
        "screened_count": 0,
        "interviewed_count": 0,
        "offers_count": 0,
        "response_count": 0,
        "accepted_count": 0,
        "applied_to_screening_rate": 0,
        "screening_to_interview_rate": 0,
        "interviewed_to_offer_rate": 0,
        "offer_to_accepted_rate": 0,
        "response_rate": 0
    }
    if not job_df.empty:
        job_df.drop_duplicates(subset=['job_id', 'history_id'], keep='first', inplace=True)
        job_df['created_at'] = pd.to_datetime(job_df['created_at'])

        applied_job_df = job_df[job_df['to_status'] == 'applied']
        if not applied_job_df.empty:
            applied_job_df.drop_duplicates(subset=['job_id'], keep='first', inplace=True)
            applied_count = len(applied_job_df)
            stats["applied_count"] = applied_count

        screened_job_df = job_df[job_df['to_status'] == 'screening']
        if not screened_job_df.empty:
            screened_job_df.drop_duplicates(subset=['job_id'], keep='first', inplace=True)
            screened_count = len(screened_job_df)
            stats["screened_count"] = screened_count

        interviewed_job_df = job_df[job_df['to_status'] == 'interviewing']
        if not interviewed_job_df.empty:
            interviewed_job_df.drop_duplicates(subset=['job_id'], keep='first', inplace=True)
            interviewed_count = len(interviewed_job_df)
            stats["interviewed_count"] = interviewed_count

        offer_received_job_df = job_df[job_df['to_status'] == 'offer']
        if not offer_received_job_df.empty:
            offer_received_job_df.drop_duplicates(subset=['job_id'], keep='first', inplace=True)
            offers_count = len(offer_received_job_df)
            stats["offers_count"] = offers_count

        responded_job_df = job_df[job_df['to_status'].isin(['screening', 'assessment', 'interviewing'])]
        if not responded_job_df.empty:
            responded_job_df.drop_duplicates(subset=['job_id'], keep='first', inplace=True)
            response_count = len(responded_job_df)
            stats["response_count"] = response_count

        accepted_job_df = job_df[job_df['to_status'] == 'accepted']
        if not accepted_job_df.empty:
            accepted_job_df.drop_duplicates(subset=['job_id'], keep='first', inplace=True)
            accepted_count = len(accepted_job_df)
            stats["accepted_count"] = accepted_count

        applied_to_screening_rate = (stats["screened_count"] / stats["applied_count"]) * 100 if stats["applied_count"] > 0 else 0
        screening_to_interview_rate = (stats["interviewed_count"] / stats["screened_count"]) * 100 if stats["screened_count"] > 0 else 0
        interviewed_to_offer_rate = (stats["offers_count"] / stats["interviewed_count"]) * 100 if stats["interviewed_count"] > 0 else 0
        offer_to_accepted_rate = (stats["accepted_count"] / stats["offers_count"]) * 100 if stats["offers_count"] > 0 else 0
        response_rate = (stats["response_count"] / stats["applied_count"]) * 100 if stats["applied_count"] > 0 else 0
        stats["applied_to_screening_rate"] = round(applied_to_screening_rate, 2)
        stats["screening_to_interview_rate"] = round(screening_to_interview_rate, 2)
        stats["interviewed_to_offer_rate"] = round(interviewed_to_offer_rate, 2)
        stats["response_rate"] = round(response_rate, 2)
        stats["offer_to_accepted_rate"] = round(offer_to_accepted_rate, 2)

        return stats


def process_interview_rounds(df):
    outcome_counts = df['outcome'].value_counts().to_dict()
    outcome_percentages = {k: round((int(v) / len(df)) * 100, 2) for k, v in outcome_counts.items()}
    return {
        "total_interviews": len(df),
        "passed": outcome_counts['passed'],
        "passed_percentage": outcome_percentages['passed']
    }


def check_progress(data, time_in_stage):
    now = datetime.now()
    if data['status'] == 'applied':
        period = (now - data['updated_at']).days
        return period < time_in_stage['average_time_applied_to_screening']
    if data['status'] == 'screening':
        period = (now - data['updated_at']).days
        return period < time_in_stage['average_time_screening_to_interview']
    if data['status'] == 'interviewing':
        period = (now - data['updated_at']).days
        return period < time_in_stage['average_time_interview_to_offer']
    return False


def calculate_idle_period(data):
    now = datetime.now()
    idle_period = (now - data['updated_at']).days
    return idle_period


async def retrieve_applications_with_status_history_from_db(db: Session, user_id: str):
    # key = f"job_applications_status_history:{user_id}"
    # redis_key = f"{key}:lock"
    # data = await redis_manager.get_value(redis_key)
    # if data:
    #     result = json.loads(data)
    #     return result
    # else:
        job_application_json_str, job_application_rows_dict = get_applications_with_status_history(db, user_id)
        # await redis_manager.set_value(redis_key, job_application_json_str, 86400)
        return job_application_rows_dict


def get_applications_with_status_history(db: Session, user_id: str):
    stmt = select(
        JobApplication.id.label("job_id"),
        JobApplication.user_id.label("user_id"),
        JobApplication.job_title.label("job_title"),
        JobApplication.source.label("source"),
        JobApplication.status,
        JobApplication.updated_at,
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
    return job_application_json_str, job_application_rows_dict


async def retrieve_user_interviews(db: Session, user_id: str):
    # key = f"user_interviews:{user_id}"
    # redis_key = f"{key}:lock"
    # data = await redis_manager.get_value(redis_key)
    # if data:
    #     result = json.loads(data)
    #     return result
    # else:
        interviews_json_str, interviews_rows_dict = get_user_interviews(db, user_id)
        # await redis_manager.set_value(redis_key, interviews_json_str, 86400)
        return interviews_rows_dict


def get_user_interviews(db: Session, user_id: str):
    interview_stmt = select(
        JobApplication.id.label("job_id"),
        JobApplication.user_id.label("user_id"),
        JobApplication.company_name.label("company_name"),
        Interview.id.label("interview_id"),
        Interview.job_application_id,
        Interview.outcome,
        Interview.round,
        Interview.date,
        Interview.time,
        Interview.created_at
    ).join(
        Interview,
        JobApplication.id == Interview.job_application_id
    ).where(
        JobApplication.user_id == user_id
    ).distinct()

    interviews_rows = db.execute(interview_stmt).all()
    interviews_rows_dict = [dict(row._asdict()) for row in interviews_rows]
    interviews_json_str = json.dumps(interviews_rows_dict, indent=4, default=custom_serializer)
    return interviews_json_str, interviews_rows_dict


async def retrieve_user_tasks(db: Session, user_id: str):
    # key = f"user_task:{user_id}"
    # redis_key = f"{key}:lock"
    # data = await redis_manager.get_value(redis_key)
    # if data:
    #     result = json.loads(data)
    #     return result
    # else:
        task_json_str, tasks_rows_dict = get_user_tasks(db, user_id)
        # await redis_manager.set_value(redis_key, task_json_str, 86400)
        return tasks_rows_dict


def get_user_tasks(db: Session, user_id: str):
    task_stmt = select(
        JobApplicationStatusHistory.id,
        JobApplicationStatusHistory.job_application_id.label("job_id"),
        JobApplicationStatusHistory.to_status,
        JobApplicationStatusHistory.created_at,
        JobTask.id.label("task_id"),
        JobTask.job_application_id,
        JobTask.user_id,
        JobTask.task_type,
        JobTask.due_date,
        JobTask.status,
        JobTask.created_at.label('job_task_created_at'),
        JobTask.updated_at
    ).join(
        JobTask,
        JobApplicationStatusHistory.job_application_id == JobTask.job_application_id
    ).where(
        JobTask.user_id == user_id
    ).distinct()

    tasks_rows = db.execute(task_stmt).all()
    tasks_rows_dict = [dict(row._asdict()) for row in tasks_rows]
    task_json_str = json.dumps(tasks_rows_dict, indent=4, default=custom_serializer)
    return task_json_str, tasks_rows_dict


async def application_funnel(db: Session, user_id: str):
    try:
        job_applications = await retrieve_applications_with_status_history_from_db(db, user_id)
        result = process_job_application_data(job_applications)
        stats = {}
        if result:
            stats = {
            "count_applications_sent": result.get('applied_count', 0),
            "count_offers_received": result.get('offers_count', 0),
            "count_responses": result.get("response_count", 0),
            "response_rate": result.get("response_rate", 0),
            "applied_to_screening": {
                "applied_count": result.get("applied_count", 0),
                "screened_count": result.get("screened_count", 0),
                "rate": f"{result.get('applied_to_screening_rate', 0)}% of applied job applications"
            },
            "screening_to_interview": {
                "interviewed_count": result.get("interviewed_count", 0),
                "rate": f"{result.get('screening_to_interview_rate', 0)}% of screened job applications"
            },
            "interview_to_offer": {
                "offers_count": result.get("offers_count", 0),
                "rate": f"{result.get('interviewed_to_offer_rate', 0)}% of interviewed job applications"
            },
            "offer_to_accepted": {
                "accepted_count": result.get("accepted_count", 0),
                "rate": f"{result.get('offer_to_accepted_rate', 0)}% of offer received job applications"
            }

        }
        interviews = await retrieve_user_interviews(db, user_id)
        interviews_df = pd.DataFrame(interviews)
        if not interviews_df.empty:
            completed_interviews_df = interviews_df[interviews_df['outcome'].isin(['passed', 'rejected'])]
            completed_interviews_count = len(completed_interviews_df)
            interview_to_offer_rate = (result['offers_count'] / completed_interviews_count) * 100 \
                if completed_interviews_count > 0 else 0
            stats["interview_to_offer_rate"] = round(interview_to_offer_rate, 2)
            stats["count_completed_interviews"] = completed_interviews_count

        return stats
    except Exception as error:
        logger.error(error)
        raise Exception(str(error))


async def time_in_stage_analytics(db: Session, user_id: str):
    try:
        job_applications = await retrieve_applications_with_status_history_from_db(db, user_id)
        job_df = pd.DataFrame(job_applications)
        stats = {}
        if not job_df.empty:
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
            stats = {
                "average_time_applied_to_screening": round(avg_time_applied_to_screening, 2),
                "average_time_screening_to_interview": round(avg_time_screening_to_interview, 2),
                "average_time_interview_to_offer": round(avg_time_interview_to_offer, 2)
            }
        return stats
    except Exception as error:
        logger.error(error)
        Exception(str(error))


async def source_analytics(db: Session, user_id: str):
    try:
        job_applications = await retrieve_applications_with_status_history_from_db(db, user_id)
        job_df = pd.DataFrame(job_applications)
        data = {}
        if not job_df.empty:
            unique_sources = list(job_df['source'].drop_duplicates())
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
        data = {}
        if not job_df.empty:
            unique_job_titles = list(job_df['job_title'].drop_duplicates())
            for job_title in unique_job_titles:
                job_title_df = job_df[job_df['job_title'] == job_title]
                job_title_data = job_title_df.to_dict('records')
                results = process_job_application_data(job_title_data)
                data[job_title] = results
        return data
    except Exception as error:
        logger.error(error)
        raise Exception(str(error))


async def weekly_application_activity(db: Session, user_id: str):
    try:
        job_applications = await retrieve_applications_with_status_history_from_db(db, user_id)
        job_df = pd.DataFrame(job_applications)
        stats = {}
        if not job_df.empty:
            job_df = job_df[job_df['to_status'] == 'applied']
            job_df.drop_duplicates(subset=['job_id', 'history_id'], keep='first', inplace=True)
            job_df['created_at'] = pd.to_datetime(job_df['created_at'])
            job_df['week_number'] = job_df['created_at'].apply(lambda t: t.isocalendar().week)
            job_df['week_period'] = job_df['created_at'].dt.to_period('W')
            job_df['week'] = job_df['created_at'].dt.to_period('W').apply(lambda r: r.start_time)
            weekly_data = job_df.groupby(['week_number', 'week_period']).size().reset_index(name='application_count')
            weekly_data['week_period'] = weekly_data['week_period'].astype(str)
            stats = weekly_data.to_dict('records')
        return stats
    except Exception as error:
        logger.error(error)
        raise Exception(str(error))


async def interview_analytics(db: Session, user_id: str):
    try:
        interviews = await retrieve_user_interviews(db, user_id)
        interviews_df = pd.DataFrame(interviews)
        if interviews_df.empty:
            return {}
        interviews_df.drop_duplicates(subset=['interview_id'], keep='first', inplace=True)
        interviews_df['round'] = interviews_df['round'].astype(str)
        interviews_df['outcome'] = interviews_df['outcome'].fillna('scheduled')
        first_round_interviews_df = interviews_df[interviews_df['round'].isin(['1', '1.0'])]
        second_round_interviews_df = interviews_df[interviews_df['round'].isin(['2', '2.0'])]
        third_round_interviews_df = interviews_df[interviews_df['round'].isin(['3', '3.0'])]
        first_round_interview_outcome = process_interview_rounds(first_round_interviews_df)
        second_round_interview_outcome = process_interview_rounds(second_round_interviews_df)
        third_round_interview_outcome = process_interview_rounds(third_round_interviews_df)

        return {
            "first_round_interview": first_round_interview_outcome,
            "second_round_interview": second_round_interview_outcome,
            "third_round_interview": third_round_interview_outcome
        }
    except Exception as error:
        logger.error(error)
        raise Exception(str(error))


async def follow_up_analytics(db: Session, user_id: str):
    try:
        tasks = await retrieve_user_tasks(db, user_id)
        tasks_df = pd.DataFrame(tasks)
        if tasks_df.empty:
            return {}
        tasks_df = tasks_df[tasks_df['to_status'].isin(['screening', 'assessment', 'interviewing'])]
        tasks_df.drop_duplicates(subset=['task_id'], keep='first', inplace=True)
        tasks_df['created_at'] = pd.to_datetime(tasks_df['created_at'])
        follow_up_tasks_df = tasks_df[tasks_df['task_type'] == TaskType.FOLLOW_UP.value]
        followed_up_tasks_df = follow_up_tasks_df[follow_up_tasks_df['status'] == TaskStatus.COMPLETED.value]
        unfollowed_up_tasks_df = follow_up_tasks_df[
            follow_up_tasks_df['status'].isin([TaskStatus.PENDING.value, TaskStatus.CANCELLED.value])]
        followed_up_rate = (len(followed_up_tasks_df) / len(
            follow_up_tasks_df)) * 100 if not follow_up_tasks_df.empty else 0
        unfollowed_up_rate = (len(unfollowed_up_tasks_df) / len(
            follow_up_tasks_df)) * 100 if not follow_up_tasks_df.empty else 0
        return {
            "followed_up_job_response_rate": round(followed_up_rate, 2),
            "unfollowed_up_job_response_rate": round(unfollowed_up_rate, 2)
        }
    except Exception as error:
        logger.error(error)
        raise Exception(str(error))


async def health_view_analytics(db: Session, user_id: str):
    try:
        time_in_stage = await time_in_stage_analytics(db, user_id)
        job_applications = await retrieve_applications_with_status_history_from_db(db, user_id)
        tasks = await retrieve_user_tasks(db, user_id)
        job_df = pd.DataFrame(job_applications)
        stats = {}
        if not job_df.empty:
            job_df.drop_duplicates(subset=['job_id', 'history_id'], keep='first', inplace=True)
            job_df['created_at'] = pd.to_datetime(job_df['created_at'])
            job_df['updated_at'] = pd.to_datetime(job_df['updated_at'])
            active_job_df = job_df[job_df['status'].isin(['applied', 'screening', 'interviewing', 'assessment'])]
            if not active_job_df.empty:
                active_job_df['is_normal_progress'] = active_job_df.apply(lambda col: check_progress(col, time_in_stage),axis=1)
                active_job_df['stale_period'] = active_job_df.apply(lambda col: calculate_idle_period(col), axis=1)
                normal_progress_job_df = active_job_df[active_job_df['is_normal_progress'] == True]
                delayed_progress_job_df = active_job_df[active_job_df['is_normal_progress'] == False]
                normal_progress_job_applications = list(normal_progress_job_df['job_id'].drop_duplicates())
                staled_job_applications = delayed_progress_job_df[
                    ['job_id', 'status', 'stale_period']].drop_duplicates().to_dict('records')
                stats["normal_progress_job_applications"] = normal_progress_job_applications
                stats["staled_job_applications"] = staled_job_applications

        tasks_df = pd.DataFrame(tasks)
        if not tasks_df.empty:
            tasks_df.drop_duplicates(subset=['task_id'], keep='first', inplace=True)
            tasks_df['due_date'] = pd.to_datetime(tasks_df['due_date'])
            tasks_df['due_date'] = tasks_df['due_date'].fillna((datetime.now() - timedelta(days=1)))
            tasks_df['due_date'] = pd.to_datetime(tasks_df['due_date'])
            tasks_df = tasks_df[tasks_df['status'].isin([TaskStatus.PENDING.value])]
            tasks_df['is_overdue'] = np.where(tasks_df['due_date'] < datetime.now(), True, False)
            upcoming_tasks_df = tasks_df[tasks_df['is_overdue'] == False]
            overdue_tasks_df = tasks_df[tasks_df['is_overdue'] == True]
            stats["upcoming_tasks"] = len(upcoming_tasks_df)
            stats["overdue_tasks"] = len(overdue_tasks_df)
        return stats
    except Exception as error:
        logger.error(error)
        raise Exception(str(error))


def weekly_digest(db: Session, user_id: str, period: datetime):
    try:
        period_start_date = period - timedelta(days=7)
        last_week_start_date = period - timedelta(days=14)
        _, job_applications = get_applications_with_status_history(db, user_id)
        job_df = pd.DataFrame(job_applications)
        stats = {}
        if not job_df.empty:
            job_df.drop_duplicates(subset=['job_id', 'history_id'], keep='first', inplace=True)
            job_df['created_at'] = pd.to_datetime(job_df['created_at'])
            job_df['updated_at'] = pd.to_datetime(job_df['updated_at'])
            follow_up_due_applied_jobs_df = job_df[
                (job_df['status'] == 'applied') & (period - job_df['updated_at']).dt.days.isin([1, 2, 3, 4, 5, 6])]
            applied_jobs_df = job_df[job_df['to_status'] == 'applied']
            responded_jobs_df = job_df[job_df['to_status'].isin(['screening'])]
            this_week_applied_jobs_df = applied_jobs_df[applied_jobs_df['created_at'] >= period_start_date]
            this_week_responded_jobs_df = responded_jobs_df[responded_jobs_df['created_at'] >= period_start_date]
            this_week_response_rate = (len(this_week_responded_jobs_df) / len(
                this_week_applied_jobs_df)) * 100 if not this_week_applied_jobs_df.empty else 0

            last_week_applied_jobs_df = applied_jobs_df[(applied_jobs_df['created_at'] >= last_week_start_date) & (
                        applied_jobs_df['created_at'] < period_start_date)]
            last_week_responded_jobs_df = responded_jobs_df[
                (responded_jobs_df['created_at'] >= last_week_start_date) & (
                            responded_jobs_df['created_at'] < period_start_date)]
            last_week_response_rate = (len(last_week_responded_jobs_df) / len(
                last_week_applied_jobs_df)) * 100 if not last_week_applied_jobs_df.empty else 0
            stats['this_week'] = {
                "applications_sent": len(this_week_applied_jobs_df),
                "response_received": len(this_week_responded_jobs_df),
                "response_rate": round(this_week_response_rate, 2),
                "last_week_response_rate": round(last_week_response_rate, 2)
            }
            stats['next_week'] = {
                "follow_up_due_applications": len(follow_up_due_applied_jobs_df)
            }

        _, tasks = get_user_tasks(db, user_id)
        tasks_df = pd.DataFrame(tasks)
        if not tasks_df.empty:
            tasks_df.drop_duplicates(subset=['job_id', 'to_status'], keep='first', inplace=True)
            tasks_df['due_date'] = tasks_df['due_date'].fillna((datetime.now() - timedelta(days=1)))
            tasks_df['due_date'] = pd.to_datetime(tasks_df['due_date'])
            tasks_df['updated_at'] = pd.to_datetime(tasks_df['updated_at'])
            tasks_df['job_task_created_at'] = pd.to_datetime(tasks_df['job_task_created_at'])
            completed_tasks_df = tasks_df[tasks_df['status'].isin([TaskStatus.COMPLETED.value])]
            completed_tasks_df = completed_tasks_df[completed_tasks_df['updated_at'] >= period_start_date]
            pending_tasks_df = tasks_df[(tasks_df['job_task_created_at'] >= period_start_date) & (
                tasks_df['status'].isin([TaskStatus.PENDING.value]))]
            pending_tasks_df['is_overdue'] = np.where(pending_tasks_df['due_date'] < datetime.now(), True, False)
            completed_tasks = len(completed_tasks_df)
            overdue_tasks = len(pending_tasks_df[pending_tasks_df['is_overdue'] == True])
            stats['this_week'] = stats.get('this_week', {})
            stats['this_week']['tasks_completed'] = completed_tasks
            stats['this_week']['overdue_tasks'] = overdue_tasks

        _, interviews = get_user_interviews(db, user_id)
        interviews_df = pd.DataFrame(interviews)
        if not interviews_df.empty:
            interviews_df.drop_duplicates(subset=['interview_id'], keep='first', inplace=True)
            interviews_df['created_at'] = pd.to_datetime(interviews_df['created_at'])
            interviews_df['date'] = pd.to_datetime(interviews_df['date']).dt.date
            interviews_df = interviews_df[interviews_df['created_at'] >= period_start_date]
            completed_interviews_df = interviews_df[interviews_df['outcome'].isin(['passed', 'rejected'])]
            completed_interviews_count = len(completed_interviews_df)
            completed_interviews = completed_interviews_df[['company_name', 'round', 'outcome']].to_dict('records')
            scheduled_interviews_df = interviews_df[
                (interviews_df['outcome'] == 'scheduled') & (interviews_df['date'].notna()) & (
                            interviews_df['date'] >= period.date())]
            scheduled_interviews_count = len(scheduled_interviews_df)
            scheduled_interviews = scheduled_interviews_df[['company_name', 'round', 'date', 'time']].to_dict('records')
            stats['next_week'] = stats.get('next_week', {})
            stats['this_week'] = stats.get('this_week', {})
            stats['this_week']['interviews_completed_count'] = completed_interviews_count
            stats['this_week']['interviews_completed'] = completed_interviews
            stats['next_week']['scheduled_interviews'] = scheduled_interviews
            stats['next_week']['scheduled_interviews_count'] = scheduled_interviews_count
        return stats
    except Exception as error:
        logger.error(error)
        raise Exception(str(error))
