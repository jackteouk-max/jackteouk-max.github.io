# JJ Buffet Reviews – Project Memory

## Goal
Every 48 hours from 21 Oct 2026: pull the last 48 hours of Google reviews for JJ Buffet London, analyse them, and email a PDF to wkteohuk@gmail.com containing:
1. All reviews from the window, shown in English
2. A tactful, professional, human reply for every review
3. Top 3 complaints with corrective and preventive actions
4. No mention of the tools used (data source or AI) anywhere in the PDF or email

## How it works (built 21 Oct 2026)
| Piece | Path | Purpose |
|---|---|---|
| Settings | `criteria.md` | Place ID, window, recipient, reply tone, complaint format, confidentiality. Edit this to change behaviour. |
| Agent steps | `.claude/skills/restaurant-sweep/SKILL.md` | The step-by-step run (`/restaurant-sweep`, add `nosend` to skip the email) |
| Filter | `scripts/filter_reviews.py` | Raw review export → only reviews inside the 48h window |
| PDF | `scripts/build_report.py` | Analysis JSON → branded PDF (reportlab) |
| Output | `reports/` | PDFs; `reports/raw/` keeps the raw data and analysis JSON per run; `reports/last_run.json` records the last send |
| Schedule | Claude app → Scheduled → "JJ Buffet – 48h Google Reviews Report" (`jj-buffet-review-report`) | Wakes daily ~09:03 London time; only sends when 46+ hours have passed since the last report |

Flow: fetch (Outscraper Google Maps reviews, sorted newest, cutoff 48h) → filter → Claude writes translations, replies, complaints → PDF → Gmail send with attachment → log.

## Key facts
- Google place: "JJ Buffet", place ID `ChIJl_XT4ggFdkgRM62dgnPYPm8`, rating 3.7 from 275 reviews (21 Oct 2026).
- Many reviewers are tourists writing in French, German, Italian etc.
- Python is the macOS system 3.9; reportlab installed with `pip install --user`. Don't run the scripts with `python3 -I` (it hides user-installed packages).
- PDF uses built-in Helvetica (no embedded font) with compression, so it stays around 10 KB; Arial Unicode is embedded only if a review has characters outside Western European (e.g. Thai, Chinese), which makes it ~70 KB. Small matters because the PDF is passed to Gmail as base64 text.
- Ratings are shown as "5/5" text; star symbols rendered as boxes in some viewers.
- Emails are sent from the connected Gmail account jackteouk@gmail.com.

## Decisions
- 21 Oct 2026: "List reviews in English" interpreted as **show every review, translating non-English ones to English** (original kept underneath), rather than dropping non-English reviews. Replies to non-English reviews are given in English and in the reviewer's language.
- 21 Oct 2026: Schedule uses a daily wake-up plus a 46-hour gate instead of an "every 2 days" cron, because cron's every-other-day resets at month end (31st → 1st would be only 24h apart).
- 21 Oct 2026: Replies signed "The JJ Buffet Team"; no refunds or free meals offered in replies.
- Scheduled task saved in Auto mode, so it sends without asking. The app must be open at 09:00 or the run happens on next launch.

## Learnings
- First test (window 19–21 Oct 2026): 4 reviews (two 5★, two 1★). Main complaint: food served cold (2 reviews), then limited choice / no desserts, then drinks pricing and no glasses.

## Run log
- 21 Oct 2026 02:38 (TEST): 4 reviews, avg 3.0, top complaint "food served cold". Emailed to wkteohuk@gmail.com with subject marked [TEST]; attachment verified in Gmail. Did not update last_run.json, so the 09:00 scheduled run still sends the first real report. Sample: `reports/TEST_JJ_Buffet_Reviews_2026-10-21.pdf`
