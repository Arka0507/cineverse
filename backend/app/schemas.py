from typing import Literal
from pydantic import BaseModel, Field, ConfigDict

class StrictModel(BaseModel):
    model_config = ConfigDict(extra='forbid')

class Movie(BaseModel):
    movie_id: int
    title: str
    year: int | None = None
    genres: list[str]
    directors: str = ''
    actors: str = ''
    rating: float
    rating_count: int
    score: float | None = None
    match: int | None = None
    reason: str | None = None
    poster_url: str | None = None
    backdrop_url: str | None = None
    overview: str = ''
    runtime: int | None = None
    trailer_key: str | None = None
    metadata_source: Literal['tmdb', 'fallback', 'curated'] = 'fallback'

class Catalog(BaseModel):
    items: list[Movie]
    total: int
    page: int
    page_size: int

class UserRecommendation(StrictModel):
    user_id: int = Field(gt=0, le=2_147_483_647)
    top_k: int = Field(default=20, ge=1, le=100)

class ItemRecommendation(StrictModel):
    movie_id: int = Field(gt=0)
    top_k: int = Field(default=20, ge=1, le=100)

class Rating(StrictModel):
    user_id: int = Field(gt=0, le=2_147_483_647)
    movie_id: int = Field(gt=0)
    rating: float = Field(ge=1, le=5, allow_inf_nan=False)

class SessionRequest(StrictModel):
    demo_user_id: int | None = Field(default=None, ge=1, le=943)

class SessionResponse(BaseModel):
    user_id: int
    token: str
    expires_in: int
