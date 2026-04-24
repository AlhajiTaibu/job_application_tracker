from datetime import datetime
from typing import Dict, Any

from fastapi import HTTPException
from sqlalchemy import desc

from app.core.logging_config import logger
from app.database import SessionLocal
from app.models.job_application import JobApplication, JobApplicationStatusHistory, Interview


class JobApplicationStateMachine:
    VALID_TRANSITIONS = {
        "saved": ["applied", "withdrawn"],
        "applied": ["screening", "assessment", "stale", "rejected", "withdrawn"],
        "screening": ["interviewing", "assessment", "stale", "rejected", "withdrawn"],
        "interviewing": ["offer", "assessment", "stale", "rejected", "withdrawn"],
        "offer": ["accepted", "rejected", "withdrawn"],
        "stale": ["withdrawn", "applied"],
        "assessment": ["interviewing", "stale", "rejected", "withdrawn"],
        "rejected": [],
        "withdrawn": [],
        "accepted": []
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
                raise HTTPException(status_code=400, detail=f"Invalid transition, valid transitions: {self.VALID_TRANSITIONS.get(job_app.status, [])}")
            from_status = job_app.status
            self._apply_transition_logic(job_app, from_status, to_status)
            job_app.status = to_status
            job_app.updated_at = datetime.now()
            job_app.save_to_db()
            reason = "State Changed"
            if metadata and "reason" in metadata:
                reason = metadata["reason"]
            job_status_history = JobApplicationStatusHistory(
                job_application_id=job_app.id,
                from_status=from_status,
                to_status=to_status,
                reason=reason
            )
            job_status_history.save_to_db()
            return {
                "id": job_app.id,
                "message": f"Job application moved from {from_status} to {to_status}",
                "status": to_status,
                "previous_status": from_status,
                "available_status": self.VALID_TRANSITIONS.get(to_status, [])
            }
        except Exception as error:
            logger.error(error)
            raise HTTPException(status_code=400, detail=str(error))

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

        elif from_status in ["applied", "screening"] and to_status == "assessment":
            self._handle_applied_or_screening_to_assessment(job_app)

        elif from_status in ["saved", "applied", "screening", "interviewing"] and to_status == 'rejected':
            self._handle_active_to_reject(job_app)

        elif from_status in ["applied", "screening", "assessment", "interviewing",
                             "stale"] and to_status == "withdrawn":
            self._handle_active_to_withdrawn(job_app)

        elif from_status in ["applied", "screening", "assessment", "interviewing"] and to_status == "stale":
            self._handle_active_to_stale(job_app)

        elif from_status == "stale" and to_status == "applied":
            self._handle_stale_to_applied(job_app)

    def _handle_applied_to_screening(self, job_app: JobApplication, metadata: Dict[str, Any] = None):
        # TODO The pending follow-up task ("chase if no response") is automatically cancelled —
        #  it's no longer needed because the response came.
        pass

    def _handle_screening_to_interviewing(self, job_app: JobApplication, metadata: Dict[str, Any] = None):
        pass

    def _handle_interviewing_to_offer(self, job_app: JobApplication, metadata: Dict[str, Any] = None):
        # TODO The system immediately creates a task: "Respond to offer — check deadline with recruiter."
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
        # TODO creates a follow-up task: "Chase if no response in 7 days." The clock is running.
        #  The user doesn't have to remember — the system is now watching this application for them.
        pass

    def _handle_active_to_reject(self, job_app, metadata: Dict[str, Any] = None):
        # TODO The system asks for an optional rejection reason —
        #  they select "rejected post-interview" from a dropdown and add a note:
        #  "second round — culture fit feedback." All pending tasks on this application are automatically cancelled.
        db_interview = self.db.query(Interview).filter(Interview.job_application_id == job_app.id).order_by(
            desc(Interview.created_at)).all()
        if db_interview:
            db_interview = db_interview[-1]
            db_interview.outcome = "reject"
            db_interview.save_to_db()

    def _handle_applied_or_screening_to_assessment(self, job_app):
        # TODO The system prompts them to set a deadline, and creates a reminder task 12 hours before the window closes.
        pass

    def _handle_active_to_stale(self, job_app):
        # TODO The application has been in APPLIED for 30 days.
        #  The user followed up once at day 7 (auto-suggested task) and again at day 14 (snoozed task).
        #  Still nothing. On day 30, the system's daily background job detects the inactivity and automatically moves the application to STALE.
        #  The user receives a notification: "Your application to Company X has been marked as stale — no activity in 30 days.
        #  Withdraw, keep waiting, or reactivate?" The user decides to withdraw.
        #  The application moves to WITHDRAWN with a system note: "auto-staled after 30 days, user confirmed withdrawal."
        #  The history shows exactly what happened — applied, two follow-ups, silence, stale, withdrawn.
        pass

    def _handle_stale_to_applied(self, job_app):
        # TODO The system creates a new follow-up task chain as if it were fresh.
        pass

    def _handle_active_to_withdrawn(self, job_app):
        # TODO The system asks for an optional rejection reason —
        #  they select "rejected post-interview" from a dropdown and add a note:
        #  "second round — culture fit feedback." All pending tasks on this application are automatically cancelled.
        pass


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
        # TODO suggest a follow-up task
        pass


interview_state_machine = InterviewStateMachine()
