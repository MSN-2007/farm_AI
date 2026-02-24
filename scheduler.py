from apscheduler.schedulers.background import BackgroundScheduler
from database import SessionLocal
from models import Poll
from datetime import datetime

scheduler = BackgroundScheduler()
scheduler.start()


def analyze_poll(poll_id):
    db = SessionLocal()

    poll = db.query(Poll).filter(Poll.id == poll_id).first()

    if poll and not poll.analyzed:
        # fetch poll results from WhatsApp API
        # run advisory LLM again
        poll.analyzed = True
        db.commit()


def schedule_poll_analysis(poll_id):
    scheduler.add_job(
        analyze_poll,
        "date",
        run_date=datetime.utcnow() + timedelta(hours=24),
        args=[poll_id]
    )