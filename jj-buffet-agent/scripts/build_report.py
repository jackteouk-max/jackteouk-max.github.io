#!/usr/bin/env python3
"""Turn the analysis JSON into the PDF report.

Usage: build_report.py ANALYSIS.json OUT.pdf

ANALYSIS.json:
{
  "business": "JJ Buffet",
  "window_start": ISO8601, "window_end": ISO8601,
  "overview": "two or three sentences",
  "reviews": [{"author", "rating", "datetime_utc", "text_en",
               "original_text" (optional), "original_language" (optional),
               "reply_en", "reply_original" (optional)}],
  "complaints": [{"title", "mentions", "what_guests_said",
                  "corrective_action", "preventive_action"}]
}
"""
import json
import os
import re
import sys
from datetime import datetime
from xml.sax.saxutils import escape
from zoneinfo import ZoneInfo

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.pdfmetrics import registerFontFamily
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (KeepTogether, Paragraph, SimpleDocTemplate,
                                Spacer, Table, TableStyle)

LONDON = ZoneInfo("Europe/London")
ACCENT = colors.HexColor("#8a1c1c")
MUTED = colors.HexColor("#666666")
RULE = colors.HexColor("#dddddd")

# Built-in Helvetica covers Western European text and keeps the PDF small (it is
# sent to Gmail as base64). Embed a Unicode TTF only when a review needs it.
FONT_CANDIDATES = [
    ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
     "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
    ("/Library/Fonts/Arial Unicode.ttf", "/Library/Fonts/Arial Unicode.ttf"),
]


def register_fonts(text):
    try:
        text.encode("cp1252")
        return "Helvetica", "Helvetica-Bold"
    except UnicodeEncodeError:
        pass
    for regular, bold in FONT_CANDIDATES:
        if os.path.exists(regular) and os.path.exists(bold):
            pdfmetrics.registerFont(TTFont("Body", regular))
            pdfmetrics.registerFont(TTFont("Body-Bold", bold))
            registerFontFamily("Body", normal="Body", bold="Body-Bold",
                               italic="Body", boldItalic="Body-Bold")
            return "Body", "Body-Bold"
    return "Helvetica", "Helvetica-Bold"


def local(iso):
    return datetime.fromisoformat(iso).astimezone(LONDON)


def p(text):
    """Escape user text and keep line breaks."""
    return escape(text or "").replace("\n", "<br/>")


def main():
    src, out = sys.argv[1], sys.argv[2]
    with open(src) as f:
        a = json.load(f)

    font, bold = register_fonts(json.dumps(a, ensure_ascii=False))
    base = dict(fontName=font, fontSize=9.5, leading=13.5, alignment=TA_LEFT)
    s = {
        "title": ParagraphStyle("title", **{**base, "fontName": bold, "fontSize": 20, "leading": 24, "textColor": ACCENT}),
        "sub": ParagraphStyle("sub", **{**base, "textColor": MUTED}),
        "h2": ParagraphStyle("h2", **{**base, "fontName": bold, "fontSize": 13, "leading": 17, "spaceBefore": 10, "spaceAfter": 6, "textColor": ACCENT}),
        "h3": ParagraphStyle("h3", **{**base, "fontName": bold, "fontSize": 10.5, "leading": 14}),
        "body": ParagraphStyle("body", **base),
        "muted": ParagraphStyle("muted", **{**base, "fontSize": 8.5, "leading": 12, "textColor": MUTED}),
        "label": ParagraphStyle("label", **{**base, "fontName": bold, "fontSize": 8.5, "textColor": ACCENT}),
    }

    reviews = a.get("reviews", [])
    complaints = a.get("complaints", [])
    start, end = local(a["window_start"]), local(a["window_end"])
    ratings = [r["rating"] for r in reviews if r.get("rating")]
    avg = f"{sum(ratings) / len(ratings):.1f}/5" if ratings else "–"

    story = [
        Paragraph(f"{escape(a.get('business', 'JJ Buffet'))} – Google Reviews Report", s["title"]),
        Spacer(1, 3),
        Paragraph(f"Reviews posted {start:%a %d %b %Y, %H:%M} to {end:%a %d %b %Y, %H:%M} (London time)", s["sub"]),
        Spacer(1, 8),
    ]

    stats = Table(
        [[Paragraph("<b>Reviews</b>", s["body"]), Paragraph("<b>Average rating</b>", s["body"]),
          Paragraph("<b>5/5 or 4/5</b>", s["body"]), Paragraph("<b>1/5 or 2/5</b>", s["body"])],
         [Paragraph(str(len(reviews)), s["h3"]), Paragraph(avg, s["h3"]),
          Paragraph(str(sum(1 for x in ratings if x >= 4)), s["h3"]),
          Paragraph(str(sum(1 for x in ratings if x <= 2)), s["h3"])]],
        colWidths=[42 * mm] * 4)
    stats.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.5, RULE),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f6f1ef")),
        ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story += [stats, Spacer(1, 8)]
    if a.get("overview"):
        story.append(Paragraph(p(a["overview"]), s["body"]))

    # 1 + 2: reviews and suggested replies
    story.append(Paragraph("1. Reviews and suggested replies", s["h2"]))
    if not reviews:
        story.append(Paragraph("No new Google reviews were posted in this period.", s["body"]))
    for i, r in enumerate(reviews, 1):
        when = local(r["datetime_utc"])
        block = [
            Paragraph(f"{i}. {escape(r.get('author', 'Guest'))} – {r.get('rating', '–')}/5", s["h3"]),
            Paragraph(f"{when:%a %d %b %Y, %H:%M}", s["muted"]),
            Spacer(1, 3),
            Paragraph(p(r.get("text_en")) or "<i>(Rating only, no written review.)</i>", s["body"]),
        ]
        if r.get("original_text"):
            block += [Spacer(1, 2), Paragraph(
                f"Original ({escape(r.get('original_language', ''))}): {p(r['original_text'])}", s["muted"])]
        block += [Spacer(1, 4), Paragraph("SUGGESTED REPLY", s["label"]), Paragraph(p(r.get("reply_en")), s["body"])]
        if r.get("reply_original"):
            block += [Spacer(1, 3),
                      Paragraph(f"SUGGESTED REPLY ({escape(r.get('original_language', '').upper())})", s["label"]),
                      Paragraph(p(r["reply_original"]), s["body"])]
        card = Table([[block]], colWidths=[168 * mm])
        card.setStyle(TableStyle([
            ("LINEBEFORE", (0, 0), (0, -1), 2, ACCENT),
            ("LEFTPADDING", (0, 0), (-1, -1), 8), ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        story += [KeepTogether(card), Spacer(1, 8)]

    # 3: complaints
    story.append(Paragraph("2. Top complaints and recommended actions", s["h2"]))
    if not complaints:
        story.append(Paragraph("No complaints were raised in this period.", s["body"]))
    for i, c in enumerate(complaints[:3], 1):
        n = c.get("mentions", 1)
        story.append(KeepTogether([
            Paragraph(f"{i}. {escape(c['title'])} ({n} review{'s' if n != 1 else ''})", s["h3"]),
            Spacer(1, 2),
            Paragraph(f"<b>What guests said:</b> {p(c.get('what_guests_said'))}", s["body"]),
            Spacer(1, 2),
            Paragraph(f"<b>Corrective action now:</b> {p(c.get('corrective_action'))}", s["body"]),
            Spacer(1, 2),
            Paragraph(f"<b>To prevent it happening again:</b> {p(c.get('preventive_action'))}", s["body"]),
            Spacer(1, 8),
        ]))

    def footer(canvas, doc):
        canvas.saveState()
        canvas.setFont(font, 7.5)
        canvas.setFillColor(MUTED)
        canvas.drawString(20 * mm, 10 * mm, f"{a.get('business', 'JJ Buffet')} – Google Reviews Report")
        canvas.drawRightString(190 * mm, 10 * mm, f"Page {doc.page}")
        canvas.restoreState()

    doc = SimpleDocTemplate(out, pagesize=A4, leftMargin=20 * mm, rightMargin=20 * mm,
                            topMargin=18 * mm, bottomMargin=18 * mm,
                            title=f"{a.get('business', 'JJ Buffet')} Google Reviews Report",
                            author="", creator="", producer="")
    doc.build(story, onFirstPage=footer, onLaterPages=footer)

    # Blank the library's comment lines; same-length replacement keeps xref offsets valid.
    with open(out, "rb") as f:
        data = f.read()
    data = re.sub(rb" ReportLab[^\n]*", lambda m: b" " * len(m.group()), data)
    with open(out, "wb") as f:
        f.write(data)
    print(f"Wrote {out} ({os.path.getsize(out) // 1024} KB)")


if __name__ == "__main__":
    main()
