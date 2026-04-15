from fastapi import FastAPI
from app.config import CONFIG
from .living_world import Character, Relationship

app = FastAPI(title=CONFIG.project_name)


@app.get("/")
def root():
    return {"message": f"{CONFIG.project_name} v0.1.0 - Phase 1 Complete"}


@app.get("/status")
def status():
    from .station import station

    return station.status


@app.get("/gary")
def gary_status():
    from .gary import gary

    return {
        "energy": gary.energy,
        "history_count": len(gary.show_history),
        "last_decision": gary.last_decision_time,
    }


@app.get("/world")
def world_status():
    from .living_world import living_world

    return {
        "relationships": living_world.session.query(Relationship).count(),
        "characters": living_world.session.query(Character).count(),
    }


@app.get("/schedule")
def schedule():
    from .station import station

    return {
        "dayparts": ["morning", "prime", "late", "overnight"],
        "current": station.current_show.name if station.current_show else "Off-air",
    }


@app.get("/obs")
def obs_guide():
    return {
        "capture": "RetroArch Lutro window (1280x720 60fps)",
        "script": "scripts/obs_setup.bat",
        "audio": "PyAudio mix -> VB-Audio Cable",
    }


from prometheus_client import Counter, generate_latest

tick_counter = Counter("station_ticks_total", "Total station ticks")


@app.get("/metrics")
def metrics():
    return generate_latest()
