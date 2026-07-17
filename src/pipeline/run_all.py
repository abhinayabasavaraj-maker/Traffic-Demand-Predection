"""
Single entry-point: regenerates every processed artifact from the raw CSV.
Usage:
    python -m src.pipeline.run_all
"""
import logging
import time

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)s  %(message)s")
log = logging.getLogger(__name__)


def main() -> None:
    t0 = time.time()

    log.info("=" * 60)
    log.info("ParkPulse — Full Pipeline")
    log.info("=" * 60)

    # Phase 1 — Cleaning
    log.info("\n── Phase 1: Cleaning ───────────────────────────────────")
    from src.pipeline.clean import run_cleaning
    run_cleaning()

    # Phase 2 — Aggregation
    log.info("\n── Phase 2a: Aggregation ───────────────────────────────")
    from src.pipeline.aggregate import run_aggregation
    run_aggregation()

    # Phase 2 — Hotspot Detection
    log.info("\n── Phase 2b: Hotspot Detection (DBSCAN) ────────────────")
    from src.pipeline.hotspots import run_dbscan
    run_dbscan()

    # Phase 3 — PPI
    log.info("\n── Phase 3a: Parking Pressure Index ────────────────────")
    from src.models.ppi import run_ppi
    run_ppi()

    # Phase 3 — Forecasting
    log.info("\n── Phase 3b: Forecasting ───────────────────────────────")
    from src.models.forecast import run_forecast
    run_forecast()

    # Phase 4 — Allocation
    log.info("\n── Phase 4: Patrol Allocation ──────────────────────────")
    from src.models.allocation import precompute_allocations
    precompute_allocations()

    elapsed = time.time() - t0
    log.info("\n%s", "=" * 60)
    log.info("Pipeline complete in %.1f seconds.", elapsed)
    log.info("Artifacts written to data/processed/")
    log.info("=" * 60)


if __name__ == "__main__":
    main()
