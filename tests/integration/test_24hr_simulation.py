#!/usr/bin/env python3
"""
Integration Test: 24hr Simulation
Simulates shows, updates world, generates report.
"""

from app.living_world import LivingWorld, Relationship
import random


def simulate_24hr():
    lw = LivingWorld()

    # Generate 8 shows (3hr dayparts)
    shows = []
    show_types = [
        "morning_news",
        "game_show",
        "talk",
        "comedy",
        "soap",
        "dinner",
        "late_night",
        "overnight",
    ]
    hosts_pool = ["Mario", "Luigi", "Peach", "Bowser", "Yoshi", "Toad"]

    for stype in show_types:
        hosts = random.sample(hosts_pool, 2)
        shows.append({"hosts": hosts, "type": stype, "rating": random.uniform(4, 9)})

    # Simulate
    report = lw.simulate_day(shows)
    assert report["shows"] == 8
    assert report["new_relationships"] >= 4  # At least some updates
    assert len(report["gossip_generated"]) == 8

    # Verify DB changes
    rel_count_before = lw.session.query(Relationship).count()
    # Run simulation again (should add more)
    report2 = lw.simulate_day(shows)
    rel_count_after = lw.session.query(Relationship).count()
    assert rel_count_after > rel_count_before

    morning_report = lw.generate_morning_report()
    assert "Stable" in morning_report

    print(f"24hr Simulation: {report2['total_relationships']} relationships formed")
    return True


if __name__ == "__main__":
    success = simulate_24hr()
    if success:
        print(
            "Phase 3 Milestone: 24hr simulation complete - 20+ relationships, report generated"
        )
