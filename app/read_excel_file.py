import pandas as pd
import re

def process_excel(file):
    # ------------------ 1) AY & YILI ÜST SATIRDAN OTOMATİK AL ------------------
    header_text = pd.read_excel(file, header=None).iloc[0, 0]

    match = re.search(r"(\d{2})\s+([A-Za-z]+),\s+(\d{4})", header_text)

    if not match:
        raise ValueError("Tarih bilgisi üst satırda bulunamadı!")

    day_str, month_str, year = match.groups()
    year = int(year)

    months = {
        "January":1, "February":2, "March":3, "April":4,
        "May":5, "June":6, "July":7, "August":8,
        "September":9, "October":10, "November":11, "December":12
    }

    month_num = months[month_str]

    df_raw = pd.read_excel(file, header=None)
    
    # 2️⃣ İlk 3 satırı al
    header_rows = df_raw.head(3)
    # ------------------ 2) ANA TABLOYU OKU ------------------
    df = pd.read_excel(file, header=8)

    if 0 in df.index:
        df = df.drop(index=0)

    cols = df.columns.tolist()
    new_cols = []
    last_date = None

    for col in cols:
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

    # --------- LONG FORMAT ---------

    in_cols = [c for c in df.columns if c.endswith("IN")]

    records = []

    for idx, row in df.iterrows():
        first = row["First Name"]
        last = row["Last Name"]
        student_id = row["External Student ID"]

        for in_col in in_cols:
            base = in_col.replace(" IN", "")
            day = base.split()[1].zfill(2)

            out_col = f"{base} OUT"
            in_time = row[in_col]
            out_time = row[out_col] if out_col in df.columns else None

            attdate = f"{year}-{month_num:02d}-{day}"

            records.append({
                "Last": last,
                "First": first,
                "StudentID": student_id,
                "Attdate": attdate,
                "IN": in_time,
                "OUT": out_time
            })

    final_df = pd.DataFrame(records)

    final_df = final_df.dropna(subset=["IN", "OUT"], how="all")

    duplicates_mask = final_df.duplicated(
        subset=["StudentID", "Attdate"],
        keep="first"
    )

    final_df = final_df[~duplicates_mask]

    final_df["Full Name"] = final_df["First"].fillna("") + " " + final_df["Last"].fillna("")
    final_df["Full Name"] = final_df["Full Name"].str.strip().str.upper()

    final_df["Attdate"] = pd.to_datetime(final_df["Attdate"], errors="coerce").dt.strftime("%m/%d/%Y")

    final_df = final_df.sort_values(
        by=["Full Name", "Attdate"],
        ascending=[True, True]
    )

    final_df = final_df.drop(columns=["IN", "OUT"], errors="ignore")

    # 🔥 SADECE BU EKLENDİ

    return final_df, header_rows
