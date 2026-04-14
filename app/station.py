"""
Placeholder Station class for Phase 1.
"""

import random
from .living_world import living_world, Relationship


class Station:
    def __init__(self):
        from .gary import gary
        from .action_trigger import action_trigger
        from .renderer import renderer
        from .audio import audio_engine

        self.gary = gary
        self.action_trigger = action_trigger
        self.living_world = living_world
        self.renderer = renderer
        self.audio_engine = audio_engine

        self.current_show = None
        self.tick_count = 0
        self.last_decision = 0
        self.decision_interval = 180  # 3 min

        self.status = {
            "phase": "5",
            "ready": True,
            "shows": 0,
            "relationships": self.living_world.session.query(Relationship).count(),
        }

    def tick(self):
        self.tick_count += 1
        print(f"Tick {self.tick_count}")

        # Decision every 3min (180 ticks @60fps, scaled)
        if self.tick_count % 180 == 0:
            decision = self.gary.make_decision()
            self.status["shows"] += 1

            # Execute
            self.action_trigger.execute_decision(decision.model_dump())

            # World update
            if len(decision.hosts) >= 2:
                self.living_world.update_relationship(
                    decision.hosts[0],
                    decision.hosts[1],
                    random.randint(-20, 30),
                    f"Hosted {decision.show}",
                )

            self.status["relationships"] = self.living_world.session.query(
                Relationship
            ).count()

            # Morning report every 288 ticks (4.8min sim day)
            if self.tick_count % 288 == 0:
                print(self.living_world.generate_morning_report())

        # self.clock.tick(60)  # 60fps broadcast - no clock defined
        # Use time.sleep(1/60) if needed, but placeholder

        return self.status


station = Station()
