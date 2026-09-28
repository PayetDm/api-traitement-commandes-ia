from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from langfuse import observe

from app.classifier import classer_email_hybride
from app.otel import flush_langfuse
from app.security import verifier_cle_api


router = APIRouter(prefix="/ai", tags=["Classification"])


class TexteEmail(BaseModel):
    text: str = Field(min_length=1, max_length=10000)


@router.post("/classify")
@observe(name="api_classify_email")
async def classifier_email(
    email: TexteEmail,
    _: str = Depends(verifier_cle_api),
):
    categorie = await classer_email_hybride(email.text)
    flush_langfuse()
    return {"categorie": categorie}