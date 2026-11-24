import logging
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

OUTPUT_PATH = Path("data/master/festival_calendar.csv")
CAL_START = date(2026, 8, 1)
CAL_END = date(2026, 12, 31)


FESTIVALS = [
    ("Dashain", date(2026, 10, 11), date(2026, 10, 16), 1.4),   # Ghatasthapana to build-up
    ("Dashain", date(2026, 10, 17), date(2026, 10, 21), 1.8),   # peak shopping before Bijaya Dashami
    ("Tihar", date(2026, 11, 7), date(2026, 11, 11), 1.7),      # Kaag Tihar to Bhai Tika
    ("Chhath", date(2026, 11, 14), date(2026, 11, 15), 1.1),    # small uplift
]


def date_range(start: date, end: date) -> set:
    
    return {start + timedelta(days=i) for i in range((end - start).days + 1)}


HOLIDAYS = date_range(date(2026, 10, 17), date(2026, 10, 23)) | date_range(date(2026, 11, 8), date(2026, 11, 11))

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("festival_calendar")


def build_calendar() -> pd.DataFrame:
    rows = []
    day = CAL_START
    while day <= CAL_END:
        name, multiplier = "", 1.0
        for festival, start, end, mult in FESTIVALS:
            if start <= day <= end:
                name, multiplier = festival, mult
        rows.append((day.isoformat(), day in HOLIDAYS, name, multiplier))
        day += timedelta(days=1)
    return pd.DataFrame(rows, columns=["date", "is_holiday", "festival_name", "sales_multiplier"])


def main() -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df = build_calendar()
    df.to_csv(OUTPUT_PATH, index=False)
    log.info("Wrote %s (%d rows)", OUTPUT_PATH, len(df))


if __name__ == "__main__":
    main()