from pathlib import Path
from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import model_validator

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')
    environment: Literal['development', 'production'] = 'development'
    artifacts_dir: Path = Path('artifacts')
    database_path: Path = Path('runtime/cineverse.db')
    tmdb_api_key: str = ''
    session_secret: str = 'development-only-change-this-secret-before-deploying'
    allowed_origins: str = 'http://localhost:3000,http://127.0.0.1:3000'
    hybrid_alpha: float = .65
    hybrid_blend: Literal['linear', 'harmonic'] = 'linear'
    rate_limit_per_minute: int = 120
    demo_profiles: bool = True

    @model_validator(mode='after')
    def production_checks(self) -> 'Settings':
        if not 0 <= self.hybrid_alpha <= 1: raise ValueError('HYBRID_ALPHA must be in [0,1]')
        if self.environment == 'production':
            if len(self.session_secret) < 32 or self.session_secret.startswith('development-'):
                raise ValueError('Production requires a unique SESSION_SECRET of 32+ characters')
            if self.demo_profiles: raise ValueError('Disable DEMO_PROFILES in production')
            if '*' in self.allowed_origins: raise ValueError('Production requires explicit CORS origins')
        return self
