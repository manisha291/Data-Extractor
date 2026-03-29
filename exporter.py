import pandas as pd
import io


def to_excel(df: pd.DataFrame) -> bytes:
    """
    Converts a DataFrame to a formatted Excel file and returns bytes.
    """
    output = io.BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Tender Data")

        # Auto-adjust column widths
        worksheet = writer.sheets["Tender Data"]
        for col_idx, column in enumerate(df.columns, 1):
            max_len = max(
                len(str(column)),
                df[column].astype(str).map(len).max() if not df.empty else 0
            )
            # Cap width at 60 characters
            worksheet.column_dimensions[
                worksheet.cell(row=1, column=col_idx).column_letter
            ].width = min(max_len + 4, 60)

    return output.getvalue()


def to_csv(df: pd.DataFrame) -> bytes:
    """
    Converts a DataFrame to a CSV file and returns bytes.
    """
    return df.to_csv(index=False).encode("utf-8")
