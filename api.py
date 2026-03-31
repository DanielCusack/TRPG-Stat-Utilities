from fastapi import FastAPI
from fe_data.models import Character

app = FastAPI()

@app.get("/stats")
def get_stats():
    characters = Character.objects.all()
    return [
        {
            "name": c.name,
        }
        for c in characters
    ]
