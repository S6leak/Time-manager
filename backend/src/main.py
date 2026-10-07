"""Point d'entrée de l'API Time Manager."""

import os

from fastapi import FastAPI

""" APPLICATION """

app = FastAPI(
    title="Time Manager API",
    version="0.1.0",
    docs_url="/api/docs",
    redoc_url=None,
    openapi_url="/api/openapi.json",
)


""" ROUTES """


@app.get("/api/health", tags=["health"])
def health():
    """Indique que l'API répond et dans quel environnement elle tourne.

    Returns
    -------
    dict
        Statut de l'API et nom de l'environnement (development, preprod, production).
    """
    return {"status": "ok", "env": os.getenv("APP_ENV", "development")}
