"""CampusPulse /ask: grounded answers over clubs, regulations and the event archive.

Run:  python -m src.index && uvicorn src.app:app --reload
"""
from __future__ import annotations

from functools import lru_cache

from fastapi import FastAPI
from pydantic import BaseModel, Field

from .answer import answer
from .index import load

app = FastAPI(title="CampusPulse")


class Ask(BaseModel):
    question: str = Field(min_length=3, max_length=500)


@lru_cache(maxsize=1)
def index():
    return load()


@app.post("/ask")
def ask(body: Ask) -> dict:
    return answer(index(), body.question).to_dict()
