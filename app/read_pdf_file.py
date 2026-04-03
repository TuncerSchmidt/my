import fitz  # PyMuPDF
import re
import pandas as pd

def extract_name(lines, start_idx):
    """
    lines: sayfadaki satırlar
    start_idx: NAME: satırının indeksi
    return: full_name, next_line_index
    """
    name_line = lines[start_idx].replace("NAME:", "").strip()
    idx = start_idx + 1

    while idx < len(lines):
        next_line = lines[idx].strip()
        if next_line == "" or re.match(r"^\d", next_line) or next_line.split()[0].upper() == "SWIPE":
            break
        name_line += " " + next_line
        idx += 1

    return name_line.strip(), idx


def process_pdf(file):
    pdf = fitz.open(stream=file.read(), filetype="pdf")

    date_pattern = re.compile(r"^\d{2}/\d{2}/\d{4}")
    number_pattern = re.compile(r"^\d+(\.\d+)?$")

    current_name = ""
    current_case = ""
    current_group = []

    data = []

    for page in pdf:
        lines = page.get_text().splitlines()
        i = 0
        while i < len(lines):
            line = lines[i].strip()

            # CASE/PERSON satırı
            if "CASE/PERSON:" in line:
                part1 = line.split("CASE/PERSON:")[1].strip()
                current_case = part1.split()[0]

                if "NAME:" in line:
                    idx_name = line.find("NAME:") + len("NAME:")
                    lines[i] = line[idx_name:].strip()
                    current_name, j = extract_name(lines, i)
                    i = j - 1

            # Tarih satırı
            elif date_pattern.match(line):
                if current_group:
                    numbers = [x for x in current_group[1:] if number_pattern.match(x)]
                    numbers_to_print = numbers[:2]
                    copay = float(numbers_to_print[0]) if len(numbers_to_print) > 0 else 0.0
                    amount = float(numbers_to_print[1]) if len(numbers_to_print) > 1 else 0.0
                    data.append([current_name, current_case, current_group[0], copay, amount])
                    current_group = []
                current_group.append(line)

            # Tarihten sonraki sayılar
            elif current_group:
                if all(number_pattern.match(x) for x in line.split()):
                    current_group.extend(line.split())
                else:
                    if current_group:
                        numbers = [x for x in current_group[1:] if number_pattern.match(x)]
                        numbers_to_print = numbers[:2]
                        copay = float(numbers_to_print[0]) if len(numbers_to_print) > 0 else 0.0
                        amount = float(numbers_to_print[1]) if len(numbers_to_print) > 1 else 0.0
                        data.append([current_name, current_case, current_group[0], copay, amount])
                        current_group = []

            i += 1

        # Sayfa sonundaki bloğu yazdır
        if current_group:
            numbers = [x for x in current_group[1:] if number_pattern.match(x)]
            numbers_to_print = numbers[:2]
            copay = float(numbers_to_print[0]) if len(numbers_to_print) > 0 else 0.0
            amount = float(numbers_to_print[1]) if len(numbers_to_print) > 1 else 0.0
            data.append([current_name, current_case, current_group[0], copay, amount])
            current_group = []

    df = pd.DataFrame(
        data,
        columns=["FULL NAME", "CASE/PERSON", "SWIPE DATE", "COPAY AP", "AMOUNT PAID"]
    )

    print("✔ PDF işlendi. Toplam satır:", len(df))

    # 🔥 Cloud için sadece return
    return df