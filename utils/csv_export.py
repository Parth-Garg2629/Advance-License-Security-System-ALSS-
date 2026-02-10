import csv
from io import StringIO
from flask import Response


def generate_csv(headers: list, rows: list, filename: str):
    buffer = StringIO()
    writer = csv.writer(buffer)

    writer.writerow(headers)
    for row in rows:
        writer.writerow(row)

    output = buffer.getvalue()
    buffer.close()

    response = Response(
        output,
        mimetype="text/csv",
    )
    response.headers["Content-Disposition"] = f"attachment; filename={filename}"
    return response
