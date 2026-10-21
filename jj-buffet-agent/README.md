# JJ Buffet – 48-hour Google review report

Every 48 hours from 21 Oct 2026, this agent pulls the last 48 hours of Google reviews for JJ Buffet (12 Newport Pl, London) and emails wkteohuk@gmail.com a PDF with:
1. every review from the period, in English (translated where needed)
2. a tactful, professional, human reply for each review
3. the top 3 complaints with corrective and preventive actions

The PDF and email never mention how the reviews were collected or that any tools or AI were used.

| File | What it does |
|---|---|
| `criteria.md` | Settings: place, window, recipient, reply tone, confidentiality. Edit this to change behaviour. |
| `RUN.md` | The step-by-step run the agent follows |
| `scripts/filter_reviews.py` | Raw review export → only reviews inside the 48h window |
| `scripts/build_report.py` | Analysis JSON → PDF |
| `reports/` | Sent PDFs. `reports/raw/` keeps the raw data and analysis per run. |

This folder is on branch `claude/cool-franklin-otwedh`, not the website's `main`, so none of it appears on the public site.

## Schedule
Claude scheduled task "JJ Buffet – 48h Google Reviews Report" (`trig_01UPfFt9XLutfojcxMEb4odJ`) wakes daily at 08:51 London time and resumes the Claude Code session that built this agent. That session has the Gmail and Outscraper connectors. The 46-hour guard means it only sends every other day.

## Decisions
- Non-English reviews are translated to English, with the original kept underneath. Their replies are given in English and in the reviewer's language.
- Replies are signed "The JJ Buffet Team" and never offer refunds or free meals.
- Duplicate guard: a run sends nothing if a report went to the recipient in the last 46 hours (checked in Gmail sent mail). So the schedule can wake daily without double-sending, and every-other-day cron's month-end reset (31st → 1st) doesn't matter.
- The PDF uses built-in Helvetica (about 7 KB) and embeds DejaVu Sans only when a review has characters outside Western European. DejaVu has no Chinese/Japanese glyphs.

## Run log
- 21 Oct 2026 (TEST, not sent): 4 reviews (19–21 Oct), average 3.0/5, top complaint "food served cold" (2 reviews). `reports/TEST_JJ_Buffet_Reviews_2026-10-21.pdf`
