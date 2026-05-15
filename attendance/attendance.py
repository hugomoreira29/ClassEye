import os
import pandas as pd
from datetime import datetime


def mark_attendance(present_students: list, all_students: list = None,
                    output_dir: str = None) -> str:
    """
    Marks attendance for all known students.
    - present_students : names recognised in the photo
    - all_students     : full class list (everyone in the dataset).
                         If omitted, only present students are recorded.
    Returns the path to the saved Excel file.
    """
    if output_dir is None:
        output_dir = os.path.join(os.path.dirname(__file__),
                                  "..", "output", "attendance")
    os.makedirs(output_dir, exist_ok=True)

    # Use full class list when available; fall back to just present
    roster = sorted(set(all_students)) if all_students else sorted(set(present_students))
    present_set = set(present_students)

    date_str = datetime.now().strftime("%Y-%m-%d")
    time_str = datetime.now().strftime("%H:%M:%S")

    rows = [
        {
            "Name":   name,
            "Status": "Present" if name in present_set else "Absent",
            "Date":   date_str,
            "Time":   time_str,
        }
        for name in roster
    ]

    if not rows:
        return ""

    df = pd.DataFrame(rows)
    filename = f"attendance_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    path = os.path.join(output_dir, filename)
    df.to_excel(path, index=False)
    print(f"Attendance saved to: {path}")
    return path
