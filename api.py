from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from fe_data.models import Character
from fe_data.domain.statistics import calculate_stat_percentiles


class StatBlock(BaseModel):
    hp: int
    strength: int
    magic: int
    skill: int
    speed: int
    luck: int
    defense: int
    resistance: int


class PercentileRequest(BaseModel):
    name: str = Field(
        ...,
        description="Name of FE9 character. To include blossom for Sothe,"
        " input 'Sothe (Random Blossom)' or 'Sothe (Fixed Blossom)'.",
    )
    stats: StatBlock
    level: int
    promoted: bool = True

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "Ike",
                "stats": {
                    "hp": 21,
                    "strength": 5,
                    "magic": 1,
                    "skill": 8,
                    "speed": 7,
                    "luck": 16,
                    "defense": 6,
                    "resistance": 1,
                },
                "level": 3,
                "promoted": False,
            }
        }
    }


class PercentileResponse(BaseModel):
    hp: float
    strength: float
    magic: float
    skill: float
    speed: float
    luck: float
    defense: float
    resistance: float

    model_config = {
        "json_schema_extra": {
            "example": {
                "hp": 0.5625,
                "strength": 1.0,
                "magic": 1.0,
                "skill": 0.25,
                "speed": 1.0,
                "luck": 1.0,
                "defense": 0.64,
                "resistance": 0.64,
            }
        }
    }


app = FastAPI()


@app.get("/health")
def health():
    """Readiness probe: confirms the process is up *and* the read-only
    database is actually reachable, not just that uvicorn is listening."""
    try:
        Character.objects.exists()
    except Exception:
        raise HTTPException(status_code=503, detail="database unavailable")
    return {"status": "ok"}


@app.get("/names")
def get_names():
    characters = Character.objects.all()
    return [c.name for c in characters]


@app.post("/percentiles", response_model=PercentileResponse)
def calculate_percentiles(payload: PercentileRequest):
    try:
        character = Character.objects.get(name=payload.name)
    except Character.DoesNotExist:
        raise HTTPException(
            status_code=400, detail=f"Character {payload.name} not found."
        )

    percentiles = calculate_stat_percentiles(
        character=character,
        stats=payload.stats.model_dump(),
        promoted=payload.promoted,
        level=payload.level,
    )
    return percentiles
