# ================= AI MODULE =================

from textblob import TextBlob


# ---------- Leave Priority AI ----------
def analyze_leave_reason(reason):

    reason_lower = reason.lower()

    # Keyword priority
    if any(word in reason_lower for word in ["medical", "hospital", "emergency", "surgery"]):
        return "High Priority"

    # Sentiment analysis
    blob = TextBlob(reason)
    polarity = blob.sentiment.polarity

    if polarity < -0.3:
        return "Urgent"

    if len(reason.strip()) < 5:
        return "Low Information"

    return "Normal"


# ---------- Attendance Insight AI ----------
def attendance_insight(present, absent):

    total = present + absent

    if total == 0:
        return "No Records Found"

    percent = (present / total) * 100

    if percent < 60:
        return "⚠ Attendance Critical"

    elif percent < 75:
        return "⚠ Attendance Warning"

    else:
        return "✅ Good Attendance"
