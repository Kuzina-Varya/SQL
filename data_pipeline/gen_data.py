from __future__ import annotations
import random
from datetime import datetime, timedelta
from typing import Literal, Optional

import numpy as np
import pandas as pd

# ---------- справочники ----------
_CITIES = [
    "Moscow", "Saint-Petersburg", "Novosibirsk", "Yekaterinburg",
    "Kazan", "Omsk", "Samara", "Rostov-on-Don", "Ufa", "Krasnoyarsk"
]
_SEGMENTS = ["retail", "B2B", "VIP"]
_NAMES = [
    "Ivan Petrov", "Anna Smirnova", "Pavel Ivanov", "Olga Sokolova",
    "Dmitry Kozlov", "Elena Morozova", "Sergey Popov", "Natalia Lebedeva",
    "Maksim Novikov", "Maria Fedorova"
]

def _rng(seed: Optional[int] = None) -> np.random.Generator:
    return np.random.default_rng(seed)

def _rand_date(rng: np.random.Generator, start: datetime, end: datetime) -> datetime:
    delta = (end - start).days
    return start + timedelta(days=int(rng.integers(0, max(delta, 1))))

def _make_email(full_name: str) -> str:
    base = full_name.lower().replace(" ", ".")
    return f"{base}@example.com"

# ---------- 1) генерация «чистого» датасета ----------
def get_dataset(
    n_rows: int = 1000,
    historicity: Literal["type1", "type2"] = "type2",
    date_from: str = "2024-01-01",
    date_to: str = "2024-12-31",
    seed: Optional[int] = 42
) -> pd.DataFrame:
    """
    Возвращает DataFrame с 10 полями:
    raw_id, full_name, city, segment, income, age, email, event_date, updated_at, notes
    """
    rng = _rng(seed)
    random.seed(seed)  # чтобы выбор из списков тоже был воспроизводим

    start_dt = datetime.fromisoformat(date_from)
    end_dt = datetime.fromisoformat(date_to)

    base_ids = np.arange(1, n_rows + 1)
    rows = []
    for rid in base_ids:
        n_versions = 1 if historicity == "type1" else int(rng.choice([1, 2, 3], p=[0.55, 0.35, 0.10]))

        name = random.choice(_NAMES)
        city = random.choice(_CITIES)
        segment = random.choice(_SEGMENTS)

        income = float(np.round(np.exp(rng.normal(10, 0.5)) / 100, 2))  # ~ 5k..15k
        age = int(rng.integers(18, 70))
        email = _make_email(name)
        notes = rng.choice(["", "priority client", "new lead", ""])

        current_updated = _rand_date(rng, start_dt, end_dt)
        for v in range(n_versions):
            event_date = _rand_date(rng, start_dt, end_dt)
            updated_at = current_updated + timedelta(days=v)

            city_v = city if rng.random() > 0.3 else random.choice(_CITIES)
            segment_v = segment if rng.random() > 0.85 else random.choice(_SEGMENTS)
            income_v = income * float(rng.normal(1.0, 0.1))  # ±10%

            rows.append({
                "raw_id": rid,
                "full_name": name,
                "city": city_v,
                "segment": segment_v,
                "income": float(np.round(income_v, 2)),
                "age": age,
                "email": email,
                "event_date": event_date.date().isoformat(),
                "updated_at": updated_at.strftime("%Y-%m-%d %H:%M:%S"),
                "notes": notes
            })

    df = pd.DataFrame(rows, columns=[
        "raw_id","full_name","city","segment","income","age","email","event_date","updated_at","notes"
    ])

    if historicity == "type1":
        df["updated_at_ts"] = pd.to_datetime(df["updated_at"])
        df = (
            df.sort_values(["raw_id", "updated_at_ts"], ascending=[True, False])
              .drop_duplicates(subset=["raw_id"], keep="first")
              .drop(columns=["updated_at_ts"])
              .reset_index(drop=True)
        )
    return df.reset_index(drop=True)

# ---------- 2) намеренно «ломаем» датасет ----------
def break_dataset(
    df: pd.DataFrame,
    null_rate: float = 0.05,
    whitespace_rate: float = 0.10,
    typo_rate: float = 0.05,
    bad_email_rate: float = 0.05,
    negative_income_rate: float = 0.02,
    huge_income_rate: float = 0.02,
    bad_age_rate: float = 0.03,
    out_of_range_date_rate: float = 0.04,
    duplicate_rate: float = 0.05,
    seed: Optional[int] = 123
) -> pd.DataFrame:
    rng = _rng(seed)
    random.seed(seed)
    dfb = df.copy()

    n = len(dfb)
    idx = np.arange(n)

    def _mask(rate: float) -> np.ndarray:
        k = int(rate * n)
        return rng.choice(idx, size=max(k, 0), replace=False)

    # NULL
    for col in ["full_name", "city", "segment", "income", "age", "email", "event_date", "updated_at", "notes"]:
        m = _mask(null_rate)
        dfb.loc[m, col] = None

    # пробелы/регистр
    ws_mask = _mask(whitespace_rate)
    def _noisify_text(x: str | None) -> str | None:
        if x is None or not isinstance(x, str):
            return x
        variants = [f"  {x}  ", x.upper(), x.lower(), x.title(), f"\t{x}\n"]
        return random.choice(variants)
    for col in ["full_name", "city", "segment", "email", "notes"]:
        dfb.loc[ws_mask, col] = dfb.loc[ws_mask, col].astype(str).map(_noisify_text)

    # опечатки городов
    def _city_typo(c: str | None) -> str | None:
        if c is None or not isinstance(c, str):
            return c
        mapping = {
            "moscow": ["msc", "moskva", "mos0w", "mos cow"],
            "saint-petersburg": ["spb", "sankt-peterburg", "st.petersburg", "saint petersburg"]
        }
        cl = c.strip().lower()
        if "moscow" in cl:
            return random.choice(mapping["moscow"])
        if "saint" in cl or "petersburg" in cl or "spb" in cl:
            return random.choice(mapping["saint-petersburg"])
        return c
    typo_mask = _mask(typo_rate)
    dfb.loc[typo_mask, "city"] = dfb.loc[typo_mask, "city"].map(_city_typo)

    # email
    bad_email_mask = _mask(bad_email_rate)
    def _break_email(e: str | None) -> str | None:
        if e is None or not isinstance(e, str):
            return e
        variants = [
            e.replace("@", ""), " " + e, e.replace(".com", ".con"),
            e.split("@")[0], "user_at_example.com",
        ]
        return random.choice(variants)
    dfb.loc[bad_email_mask, "email"] = dfb.loc[bad_email_mask, "email"].map(_break_email)

    # доход
    neg_mask = _mask(negative_income_rate)
    huge_mask = _mask(huge_income_rate)
    dfb.loc[neg_mask, "income"] = dfb.loc[neg_mask, "income"].apply(lambda x: -abs(float(x)) if pd.notna(x) else x)
    dfb.loc[huge_mask, "income"] = dfb.loc[huge_mask, "income"].apply(lambda x: float(x) * 1_000_000 if pd.notna(x) else x)

    # возраст
    bad_age_mask = _mask(bad_age_rate)
    def _break_age(a) -> object:
        if pd.isna(a):
            return a
        return random.choice([0, 150, "N/A", "unknown"])
    dfb.loc[bad_age_mask, "age"] = dfb.loc[bad_age_mask, "age"].map(_break_age)

    # даты
    date_mask = _mask(out_of_range_date_rate)
    def _bad_date(s: str | None) -> str | None:
        if s is None:
            return s
        return random.choice(["1900-01-01", "2099-12-31", "31-02-2024", "2024/13/01", "not-a-date"])
    dfb.loc[date_mask, "event_date"] = dfb.loc[date_mask, "event_date"].map(_bad_date)
    dfb.loc[date_mask, "updated_at"] = dfb.loc[date_mask, "updated_at"].map(
        lambda x: None if random.random() < 0.5 else "2024-99-99 25:61:61"
    )

    # дубликаты
    dup_mask = _mask(duplicate_rate)
    dups = dfb.loc[dup_mask].copy()
    if not dups.empty:
        tweak_idx = dups.sample(frac=0.5, random_state=seed).index
        def _tweak_ts(ts: str | None) -> str | None:
            if ts is None or not isinstance(ts, str):
                return ts
            try:
                dt = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
                return (dt + timedelta(hours=random.randint(1, 48))).strftime("%Y-%m-%d %H:%M:%S")
            except Exception:
                return ts
        dups.loc[tweak_idx, "updated_at"] = dups.loc[tweak_idx, "updated_at"].map(_tweak_ts)
    dfb = pd.concat([dfb, dups], ignore_index=True)

    # всё в строки, чтобы грузить в TEXT
    for col in dfb.columns:
        dfb[col] = dfb[col].astype(object).where(dfb[col].notna(), None)
        dfb[col] = dfb[col].astype(str).where(dfb[col].notna(), None)

    return dfb.reset_index(drop=True)
