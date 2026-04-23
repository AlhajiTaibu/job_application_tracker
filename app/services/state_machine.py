from typing import Dict, Any

from fastapi import HTTPException
from sqlalchemy import desc

from app.core.logging_config import logger
from app.database import SessionLocal
from app.models.job_application import JobApplication, JobApplicationStatusHistory, Interview


class JobApplicationStateMachine:
    VALID_TRANSITIONS = {
        'saved': ["applied", "rejected", "withdrawn"],
        "applied": ["screening", "rejected", "withdrawn"],
        'screening': ['interviewing', 'rejected', 'withdrawn'],
        'interviewing': ['offer', 'rejected', 'withdrawn'],
        'offer': ['accepted', 'rejected', 'withdrawn'],
    }

    def __init__(self):
        try:
            self.db = SessionLocal()
        finally:
            self.db.close()

    def can_transition(self, from_status: str, to_status: str):
        return to_status in self.VALID_TRANSITIONS.get(from_status, [])

    def transition_state(self, job_app: JobApplication, to_status: str, metadata: Dict[str, Any] = None):
        try:
            if not job_application_state_machine.can_transition(job_app.status, to_status):
                raise HTTPException(status_code=400, detail="Invalid transition")
            from_status = job_app.status
            self._apply_transition_logic(job_app, from_status, to_status)
            job_app.status = to_status
            job_app.save_to_db()
            job_status_history = JobApplicationStatusHistory(
                job_application_id=job_app.id,
                from_status=from_status,
                to_status=to_status,
                reason="Status changed"
            )
            job_status_history.save_to_db()
        except Exception as error:
            logger.error(error)
            raise HTTPException(status_code=400, detail="Invalid transition")

    def _apply_transition_logic(self, job_app: JobApplication, from_status: str, to_status: str,
                                metadata: Dict[str, Any] = None):

        if from_status == "applied" and to_status == "screening":
            self._handle_applied_to_screening(job_app)

        elif from_status == "saved" and to_status == "applied":
            self._handle_saved_to_applied(job_app)

        elif from_status == "screening" and to_status == "interviewing":
            self._handle_screening_to_interviewing(job_app)

        elif from_status == "interviewing" and to_status == "offer":
            self._handle_interviewing_to_offer(job_app)

        elif from_status == "offer" and to_status == "accepted":
            self._handle_offer_to_accepted(job_app)

        elif from_status in ["saved", "applied", "screening", "interviewing"] and to_status == ['rejected','withdrawn']:
            self._handle_to_reject_or_withdrawn(job_app)

    def _handle_applied_to_screening(self, job_app: JobApplication, metadata: Dict[str, Any] = None):
        pass

    def _handle_screening_to_interviewing(self, job_app: JobApplication, metadata: Dict[str, Any] = None):
        pass

    def _handle_interviewing_to_offer(self, job_app: JobApplication, metadata: Dict[str, Any] = None):
        db_interview = self.db.query(Interview).filter(Interview.job_application_id == job_app.id).order_by(
            desc(Interview.created_at)).all()
        if not db_interview:
            raise HTTPException(status_code=400, detail="Update Error")
        else:
            db_interview = db_interview[-1]
            db_interview.outcome = "passed"
            db_interview.save_to_db()

    def _handle_offer_to_accepted(self, job_app, metadata: Dict[str, Any] = None):
        pass

    def _handle_saved_to_applied(self, job_app, metadata: Dict[str, Any] = None):
        pass

    def _handle_to_reject_or_withdrawn(self, job_app, metadata: Dict[str, Any] = None):
        db_interview = self.db.query(Interview).filter(Interview.job_application_id == job_app.id).order_by(
            desc(Interview.created_at)).all()
        if db_interview:
            db_interview = db_interview[-1]
            db_interview.outcome = "reject"
            db_interview.save_to_db()


job_application_state_machine = JobApplicationStateMachine()


class InterviewStateMachine:
    def __init__(self):
        try:
            self.db = SessionLocal()
        finally:
            self.db.close()

    def transition_state(self, interview: Interview):
        try:
            self._apply_transition_logic(interview)
            return True
        except Exception as error:
            logger.error(error)
            raise HTTPException(status_code=400, detail="Invalid transition")

    def _apply_transition_logic(self, interview: Interview, metadata: Dict[str, Any] = None):
        if interview.outcome == "passed":
            self._handle_passed(interview)
        elif interview.outcome == "rejected":
            self._handle_rejected(interview)
        elif interview.outcome == "withdrawn":
            self._handle_withdrawn(interview)
        elif interview.outcome == "waiting":
            self._handle_waiting(interview)

    def _handle_rejected(self, interview: Interview):
        job_app = self.db.query(JobApplication).filter(JobApplication.id == interview.job_application_id).first()
        job_application_state_machine.transition_state(job_app, "rejected")

    def _handle_withdrawn(self, interview: Interview):
        job_app = self.db.query(JobApplication).filter(JobApplication.id == interview.job_application_id).first()
        job_application_state_machine.transition_state(job_app, "withdrawn")

    def _handle_passed(self, interview):
        new_interview = Interview(
            job_application_id=interview.job_application_id
        )
        new_interview.save_to_db()

    def _handle_waiting(self, interview):
        #TODO suggest a follow-up task
        pass


interview_state_machine = InterviewStateMachine()
