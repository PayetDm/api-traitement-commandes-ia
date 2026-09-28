from fastapi import APIRouter


router = APIRouter(tags=["Système"])


@router.get("/health")
def health_check():
    return {"statut": "ok", "base_de_donnees": "connectee"}
