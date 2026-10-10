"""
Rate limiting maison (alternative à slowapi).
Utilise un dict en mémoire : {ip: [timestamps]}.
⚠️ Ne marche que sur 1 seule instance (pas distribué).
"""
from collections import defaultdict
from time import time
from fastapi import HTTPException, Request
import logging
import uuid

logger = logging.getLogger(__name__)

# ID unique du module (pour debug)
MODULE_ID = str(uuid.uuid4())[:8]
logger.info(f"MODULE_LOADED: rate_limit.py id={MODULE_ID}")

# Stockage en mémoire : {ip: [timestamp1, timestamp2, ...]}
_rate_counters: dict[str, list[float]] = defaultdict(list)


def check_rate_limit(
    request: Request,
    max_requests: int = 5,
    window_seconds: int = 60,
) -> None:
    """
    Vérifie le rate limit pour l'IP du client.
    Lève HTTPException 429 si dépassé.
    """
    client_ip = request.client.host if request.client else "unknown"
    now = time()

    logger.info(
        f"DEBUG-RATE-LIMIT: module_id={MODULE_ID} ip={client_ip} "
        f"count_actuel={len(_rate_counters[client_ip])}"
    )

    # Garde seulement les requêtes dans la fenêtre
    _rate_counters[client_ip] = [
        t for t in _rate_counters[client_ip]
        if now - t < window_seconds
    ]

    # Vérifie si la limite est dépassée
    if len(_rate_counters[client_ip]) >= max_requests:
        logger.warning(
            f"RATE-LIMIT-DEPASSE: IP={client_ip} "
            f"path={request.url.path} ({len(_rate_counters[client_ip])} requetes)"
        )
        raise HTTPException(
            status_code=429,
            detail={
                "error": "Trop de requetes",
                "detail": f"Maximum {max_requests} requetes par {window_seconds} secondes",
                "retry_after": window_seconds,
            },
        )

    # Enregistre cette requête
    _rate_counters[client_ip].append(now)