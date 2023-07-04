from pypdf import PdfReader, PdfWriter
import urllib.request
from pypdf import PdfReader
import pandas as pd
import re


def download_pdf_weather_data(month, year):
    url = f"https://www.vedur.is/media/vedurstofan/utgafa/hlidarefni/climat/climat-Reykjavik-{month}-{year}.pdf"
    url = url.format(month=month, year=year)

    # Download the pdf

    urllib.request.urlretrieve(url, pdf_path)


def crop_pdf(input_path, output_path, x1, y1, x2, y2):
    with open(input_path, "rb") as file:
        input_pdf = PdfReader(file)
        num_pages = len(input_pdf.pages)

        output_pdf = PdfWriter()

        for page_number in range(num_pages):
            page = input_pdf.pages[page_number]
            page.cropbox.lower_left = (x1, y1)
            page.cropbox.upper_right = (x2, y2)
            output_pdf.add_page(page)

        with open(output_path, "wb") as output_file:
            output_pdf.write(output_file)


def read_pdf(pdf_path):
    # creating a pdf file object
    pdf_file = open(pdf_path, "rb")

    # creating a pdf reader object
    reader = PdfReader(pdf_file)

    # creating a page object
    page = reader.pages[0]  # Access the first page

    table_content = page.extract_text(0, 90)
    table_content = table_content.split("\n")

    table_content = table_content[:-27]
    table_content = [x.strip() for x in table_content]

    amount_of_columns = 12
    amount_of_rows = 31
    index_of_end_of_table = []
    for i in range(amount_of_columns):
        index = amount_of_rows - i + (amount_of_rows * i)
        index_of_end_of_table.append(index)

    data = []

    # print(index_of_end_of_table)

    for i, split_index in enumerate(index_of_end_of_table):
        if i == 0:
            data.append(table_content[:split_index])
        else:
            data.append(table_content[index_of_end_of_table[i - 1] : split_index])

    return data


def clean_data(data):
    # fix last cell in each row
    for i, row in enumerate(data):
        last_cell = row[-1]

        if "−" in last_cell:
            last_cell = last_cell.replace("−", " -")
            last_cell = last_cell.split(" ")
            last_cell = [x for x in last_cell if x != ""]

            row[-1] = last_cell[0]

            if i + 1 < len(data):
                data[i + 1].insert(0, last_cell[-1])

        if " " in last_cell:
            last_cell = last_cell.split(" ")

            row[-1] = last_cell[0]

            if i + 1 < len(data):
                data[i + 1].insert(0, last_cell[1])

        if "." in last_cell and len(last_cell) > 4:
            # Match the last decimal place and add a space after it
            modified_string = re.sub(r"(\.\d+)(?!\.)", r"\1 ", last_cell)
            modified_string = modified_string.split(" ")
            modified_string = [x for x in modified_string if x != ""]

            row[-1] = modified_string[0]

            if i + 1 < len(data):
                data[i + 1].insert(0, modified_string[1])

        # if last cell does not match amount of decimals
        if "." in last_cell and len(last_cell.split(".")[-1]) > 1:
            # split after last decimal place
            modified_string = last_cell.split(".")
            modified_string = modified_string[0] + "." + modified_string[1][0]

            new_cell = last_cell.replace(modified_string, "")

            row[-1] = modified_string

            if i + 1 < len(data):
                data[i + 1].insert(0, new_cell)

        # if rain type column
        if (
            i == 5
            and last_cell != ""
            and last_cell != "sn"
            and last_cell != "sl"
            and last_cell != "ri"
        ):
            row[-1] = ""

            if i + 1 < len(data):
                data[i + 1].insert(0, last_cell)

        # if snow type column has too large value
        if i == 6 and len(last_cell) > 2:
            corrected_value = last_cell[:2]
            row[-1] = corrected_value

            if i + 1 < len(data):
                data[i + 1].insert(0, last_cell[2:])

        # if range of snow cover column has too large value
        if i == 7 and len(last_cell) > 1:
            corrected_value = last_cell[:1]
            row[-1] = corrected_value

            if i + 1 < len(data):
                data[i + 1].insert(0, last_cell[1:])

        # replace "−" with "-" in all cells
        for j, cell in enumerate(row):
            if "−" in cell:
                row[j] = cell.replace("−", "-")

    return data
    # print(i, len(row), row)


def format_data(data, month, year):
    header = [
        "day",
        "avg temperature",
        "max temp",
        "min temp",
        "rain",
        "rain type",
        "snow depth",
        "snow type",
        "sun hours",
        "avg wind",
        "max wind",
        "gust",
    ]

    # rotate data
    data = list(map(list, zip(*data)))

    try:
        df = pd.DataFrame(data, columns=header)
        df["day"] = df["day"].astype(int)

        month = int(month)
        if month < 10:
            month = f"0{month}"

        dates = []

        for day in df["day"]:
            if day < 10:
                day = f"0{day}"
            date_str = f"{year}-{str(month)}-{str(day)}"
            date = pd.to_datetime(date_str, format="%Y-%m-%d")
            dates.append(date)

        df["date"] = dates
        df = df.drop(columns=["day"])

        return df
    except Exception as e:
        print("Error in data, could not convert to csv")
        # print(e)


if __name__ == "__main__":
    for year in range(2019, 2024):
        for month in range(1, 13):
            try:
                pdf_path = f"reykjavik-{month}-{year}.pdf"

                assert 1 <= month <= 12
                assert 2019 <= year <= 2023

                download_pdf_weather_data(month, year)
                crop_pdf(pdf_path, pdf_path, 25, 178, 375, 770)

                data = read_pdf(pdf_path)
                data = clean_data(data)
                df = format_data(data, month, year)

                csv_path = pdf_path.split("/")[-1].replace(".pdf", ".csv")
                df.to_csv("./data/climat/" + csv_path, index=False)
            except Exception as e:
                print(e)
                print(f"Error in {month}-{year}")
