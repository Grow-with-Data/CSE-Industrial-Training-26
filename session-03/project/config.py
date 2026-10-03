"""Configuration for the ShopWise assistant — project version v0.2.

Session 2 read settings with `os.getenv(...)`. That works until a setting is not
a string: `SHOPWISE_USE_FEW_SHOT=false` arrives as the string "false", and a
non-empty string is truthy, so the switch can never be turned off. From v0.2 the
configuration is a Pydantic model. Same library as schemas.py, other boundary:

    schemas.py   checks what comes in from the model and from tickets.yml
    config.py    checks what comes in from the environment

Every field is read from `SHOPWISE_<FIELD>` (SHOPWISE_MODEL, SHOPWISE_USE_FEW_SHOT).
The prefix keeps our settings apart from every other program on your machine that
also wants a variable called MODEL. `GEMINI_API_KEY` keeps its plain name because
Google's SDK looks for exactly that name.

    uv run python config.py      # prints what it resolved to
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# session-03/project/config.py -> repo root, the folder holding data/ and .env
LABS = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    """Everything the assistant can be told that is not code. Read it top to bottom."""

    model_config = SettingsConfigDict(
        env_file=LABS / ".env",
        env_prefix="SHOPWISE_",
        extra="ignore",          # the shared .env also holds keys for later sessions
    )

    APP_NAME: str = "ShopWise Support Assistant"
    VERSION: str = "0.2.0"
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"

    # SecretStr prints as '**********', so the key never ends up in a log line,
    # a traceback or a screen share. Reading it takes .get_secret_value().
    GEMINI_API_KEY: SecretStr = Field(
        default=SecretStr(""),
        validation_alias="GEMINI_API_KEY",   # no SHOPWISE_ prefix: the SDK's own name
    )

    # The same five model names as v0.1. Code says settings.MODEL; a model ID is
    # never typed at a call site.
    MODEL: str = "gemini-3.5-flash-lite"
    MODEL_STRONG: str = "gemini-3.8-flash"
    MODEL_SEARCH: str = "gemini-3.5-flash-lite"
    MODEL_PRO: str = "gemini-2.5-pro"
    EMBED_MODEL: str = "gemini-embedding-2"

    MAX_OUTPUT_TOKENS: int = Field(default=1024, ge=64, le=8192)
    REQUEST_TIMEOUT_S: float = Field(default=60.0, gt=0)
    MAX_RETRIES: int = Field(default=4, ge=1, le=8)

    # Few-shot examples in the triage prompt. Measured with ../score.py --compare;
    # the result is written in session 3's notebook, section 4. Turn them on for
    # one run with SHOPWISE_USE_FEW_SHOT=true.
    USE_FEW_SHOT: bool = False

    DATA_DIR: Path = LABS / "data"

    @field_validator("MODEL", "MODEL_STRONG", "MODEL_SEARCH", "MODEL_PRO", "EMBED_MODEL")
    @classmethod
    def no_blank_model_ids(cls, value: str) -> str:
        """`SHOPWISE_MODEL=` with nothing after it should fail here, not as a 404 later."""
        value = value.strip()
        if not value:
            raise ValueError("must not be empty: delete the line or give it a model ID")
        return value

    @model_validator(mode="after")
    def production_needs_a_key(self) -> Settings:
        """You can read the notebooks without a key. Production can't run without one."""
        if self.ENVIRONMENT == "production" and not self.has_key:
            raise ValueError("GEMINI_API_KEY is required when ENVIRONMENT=production")
        return self

    @property
    def has_key(self) -> bool:
        return bool(self.GEMINI_API_KEY.get_secret_value())


@lru_cache
def get_settings() -> Settings:
    """Build the settings once. Every caller gets the same object.

    load_dotenv is still needed: Google's SDK reads GEMINI_API_KEY from os.environ
    itself, so the variable has to be there, not only inside this object.
    """
    load_dotenv(LABS / ".env", override=True)
    return Settings()


settings = get_settings()


if __name__ == "__main__":
    print(f"{settings.APP_NAME} v{settings.VERSION}  [{settings.ENVIRONMENT}]")
    for name, value in settings.model_dump().items():
        print(f"  {name:18} {value}")
