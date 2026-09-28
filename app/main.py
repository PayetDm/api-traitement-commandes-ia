import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from apscheduler.schedulers.background import BackgroundScheduler
from langfuse import get_client

from app.database import SessionLocal, engine
from app.models import Base
from app.email_service import relever_et_traiter_emails
from app.limiter import limiter
from app.routers import commandes, systeme, classifier
from app.otel import setup_langfuse, flush_langfuse

Base.metadata.create_all(bind=engine)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()


def job_verification_email():
    db = SessionLocal()
    try:
        langfuse = get_client()
        with langfuse.start_as_current_observation(
            as_type="span", name="job_verification_email"
        ) as span:
            relever_et_traiter_emails(db)
            span.update(output="Job completed")
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_langfuse(app)
    logger.info("Démarrage du scanner de mails automatique...")
    scheduler.add_job(job_verification_email, "interval", seconds=30)
    scheduler.start()
    yield
    logger.info("Arrêt du scanner de mails.")
    scheduler.shutdown()
    flush_langfuse()


app = FastAPI(title="API Traitement Commandes IA", lifespan=lifespan)

# CORS
origins = [
    "http://localhost:8501",
    "http://interface_streamlit:8501",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH"],
    allow_headers=["Authorization", "Content-Type", "X-API-Key"],
)

# Rate Limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# Route racine pour éviter le 404
@app.get("/")
def read_root():
    return {"message": "API Traitement Commandes IA en ligne", "docs": "/docs"}


# Inclusion des routeurs
app.include_router(systeme.router)
app.include_router(commandes.router)
app.include_router(classifier.router)