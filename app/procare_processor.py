import pandas as pd
import re

# --------------------------------------------------
# Saat formatını ayıkla (08:05 AM gibi)
# --------------------------------------------------
def extract_time(val):
    if pd.isna(val):
        return None
    match = re.search(r"(\d{1,2}:\d{2}\s*(AM|PM))", str(val))
    return match.group(1) if match else None


def process_procare(df_raw: pd.DataFrame, header_text: str) -> pd.DataFrame:
    # --------------------------------------------------
    # 1️⃣ AY / GÜN / YIL HEADER TEXT’TEN AL
    # --------------------------------------------------
    match = re.search(r"(\d{2})\s+([A-Za-z]+),\s+(\d{4})", header_text)
    if not match:
        raise ValueError("Tarih bilgisi header text içinde bulunamadı")

    day_str, month_str, year = match.groups()
    year = int(year)

    months = {
        "January":1, "February":2, "March":3, "April":4,
        "May":5, "June":6, "July":7, "August":8,
        "September":9, "October":10, "November":11, "December":12
    }
    month_num = months[month_str]

    # --------------------------------------------------
    # 2️⃣ DATAFRAME KOPYASI
    # --------------------------------------------------
    df = df_raw.copy()

    if 0 in df.index:
        df = df.drop(index=0)

    # --------------------------------------------------
    # 3️⃣ KOLON İSİMLERİNİ DÜZELT (IN / OUT)
    # --------------------------------------------------
    new_cols = []
    last_date = None

    for col in df.columns:
        if isinstance(col, str) and re.match(r"^[A-Za-z]{3}\s+\d{2}$", col):
            last_date = col.strip()
            new_cols.append(f"{last_date} IN")
        elif "Unnamed" in str(col):
            if last_date:
                new_cols.append(f"{last_date} OUT")
            else:
                new_cols.append(col)
        else:
            new_cols.append(col)

    df.columns = new_cols

    # --------------------------------------------------
    # 4️⃣ LONG FORMAT (RAW IN / OUT)
    # --------------------------------------------------
    in_cols = [c for c in df.columns if c.endswith("IN")]
    records = []

    for _, row in df.iterrows():
        first = row.get("First Name")
        last = row.get("Last Name")
        student_id = row.get("External Student ID")

        for in_col in in_cols:
            base = in_col.replace(" IN", "")
            day = base.split()[1].zfill(2)
            out_col = f"{base} OUT"

            in_time = extract_time(row[in_col])
            out_time = extract_time(row[out_col]) if out_col in df.columns else None

            if pd.isna(in_time):
                continue

            attdate = f"{year}-{month_num:02d}-{day}"

            records.append({
                "StudentID": student_id,
                "First": first,
                "Last": last,
                "Attdate": attdate,
                "IN": in_time,
                "OUT": out_time
            })

    final_df = pd.DataFrame(records)

    # --------------------------------------------------
    # 5️⃣ FULL NAME + DATETIME
    # --------------------------------------------------
    final_df["Full Name"] = (
        final_df["First"].fillna("") + " " + final_df["Last"].fillna("")
    ).str.strip().str.upper()

    final_df["Attdate"] = pd.to_datetime(final_df["Attdate"], errors="coerce")

    final_df["IN_dt"] = pd.to_datetime(
        final_df["Attdate"].dt.strftime("%Y-%m-%d") + " " + final_df["IN"],
        errors="coerce"
    )

    final_df["OUT_dt"] = pd.to_datetime(
        final_df["Attdate"].dt.strftime("%Y-%m-%d") + " " + final_df["OUT"],
        errors="coerce"
    )

    # --------------------------------------------------
    # 6️⃣ MORNING / AFTERNOON AYRIMI
    # --------------------------------------------------
    final_df["IN_Period"] = final_df["IN_dt"].dt.hour.apply(
        lambda x: "Morning" if x < 12 else "Afternoon"
    )

    final_df["OUT_Period"] = final_df["OUT_dt"].dt.hour.apply(
        lambda x: "Morning" if x < 12 else "Afternoon"
    )

    # --------------------------------------------------
    # 7️⃣ LONG FORMAT (DHS STYLE)
    # --------------------------------------------------
    rows = []

    for _, r in final_df.iterrows():
        if pd.notna(r["IN_dt"]):
            rows.append({
                "Full Name": r["Full Name"],
                "StudentID": r["StudentID"],
                "Attdate": r["Attdate"],
                "Column": f"{r['IN_Period']}_IN",
                "Time": r["IN_dt"]
            })

        if pd.notna(r["OUT_dt"]):
            rows.append({
                "Full Name": r["Full Name"],
                "StudentID": r["StudentID"],
                "Attdate": r["Attdate"],
                "Column": f"{r['OUT_Period']}_OUT",
                "Time": r["OUT_dt"]
            })

    long_df = pd.DataFrame(rows)

    # --------------------------------------------------
    # 8️⃣ AYNI SLOT İÇİN EN ERKEN ZAMAN
    # --------------------------------------------------
    agg = (
        long_df
        .groupby(["Full Name", "StudentID", "Attdate", "Column"])["Time"]
        .min()
        .reset_index()
    )

    # --------------------------------------------------
    # 9️⃣ PIVOT (YAN YANA)
    # --------------------------------------------------
    pivot_df = agg.pivot(
        index=["Full Name", "StudentID", "Attdate"],
        columns="Column",
        values="Time"
    ).reset_index()

    # --------------------------------------------------
    # 🔟 FORMATLAR
    # --------------------------------------------------
    for c in pivot_df.columns:
        if c.endswith("_IN") or c.endswith("_OUT"):
            pivot_df[c] = pivot_df[c].dt.strftime("%H:%M")

    pivot_df["Attdate"] = pivot_df["Attdate"].dt.strftime("%m/%d/%Y")

    pivot_df = pivot_df.sort_values(by=["Full Name", "Attdate"])

    return pivot_df
