#!/usr/bin/env python3
"""
Night Shift Protocol for T3MPLATE TV WORLD
Autonomous development 2AM-5AM: new pilots, relationship evolution, set prep.
FULL_VISION.md lines 177-185.
"""

import logging
import time
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class NightShift:
    """Autonomous show development during off-hours."""

    def __init__(self):
        self.start_hour = 2
        self.end_hour = 5
        self.is_active = False
        self.developed_shows = []

    def check_and_run(self):
        now = datetime.now()
        if self.start_hour <= now.hour < self.end_hour:
            if not self.is_active:
                self.activate()
            self.run_protocol()
        elif self.is_active and now.hour >= self.end_hour:
            self.deactivate()

    def activate(self):
        logger.info("Night Shift activated: Autonomous development begin")
        self.is_active = True

    def deactivate(self):
        logger.info("Night Shift deactivated: Morning report ready")
        self.is_active = False
        self.generate_morning_report()

    def run_protocol(self):
        logger.info("Running Night Shift protocol")
        self.autonomous_show_development()
        self.evolve_relationships_off_hours()
        self.prepare_sets_seasonal()
        self.plan_sweeps_events()

    def autonomous_show_development(self):
        """FULL_VISION.md: Autonomous show development using character relationships."""
        from app.living_world import Character, Show, Session

        session = Session()
        chars = session.query(Character).all()

        if len(chars) >= 2:
            import random

            host1, host2 = random.sample(chars, 2)
            pilot_name = f"Night Shift Special {datetime.now().strftime('%Y%m%d')}"
            pilot = Show(
                name=pilot_name,
                status="pitch",
                genre=random.choice(["talk", "news", "game_show"]),
                hosts=[host1.name, host2.name],
            )
            session.add(pilot)
            session.commit()
            self.developed_shows.append(pilot_name)
            logger.info(f"Developed pilot: {pilot_name}")

        session.close()

    def evolve_relationships_off_hours(self):
        """FULL_VISION.md: Relationship evolution driven by off-screen interactions."""
        from app.living_world import Relationship, Session

        session = Session()
        rels = session.query(Relationship).all()

        if rels:
            import random

            rel = random.choice(rels)
            delta = random.randint(-5, 10)
            rel.score = min(100, max(-100, rel.score + delta))
            rel.events.append({"event": "Night shift evolution", "delta": delta})
            session.commit()
            logger.info(f"Evolved relationship {rel.id} by {delta}")

        session.close()

    def prepare_sets_seasonal(self):
        """FULL_VISION.md: Set evolution and seasonal preparation."""
        now = datetime.now()
        month = now.month
        seasonal = (
            "holiday"
            if month in [11, 12]
            else "summer"
            if month in [6, 7, 8]
            else "standard"
        )
        logger.info(f"Preparing {seasonal} sets")
        return seasonal

    def plan_sweeps_events(self):
        """FULL_VISION.md: Gary sweeps week planning."""
        from app.gary import gary

        decision = gary.make_decision(news=["Sweeps week planning"])
        logger.info(f"Gary night sweeps decision: {decision.thought}")

    def generate_morning_report(self):
        """FULL_VISION.md: Morning report generation for creator review."""
        report = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "night_shift_shows": len(self.developed_shows),
            "developed_shows": self.developed_shows,
            "status": "Ready for review",
        }
        output_dir = Path("OUTPUT/morning_reports")
        output_dir.mkdir(parents=True, exist_ok=True)
        report_file = (
            output_dir / f"night_shift_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        import json

        with open(report_file, "w") as f:
            json.dump(report, f, indent=2)
        logger.info(f"Morning report saved: {report_file}")
        return report


night_shift = NightShift()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    shift = NightShift()
    while True:
        shift.check_and_run()
        time.sleep(60)
