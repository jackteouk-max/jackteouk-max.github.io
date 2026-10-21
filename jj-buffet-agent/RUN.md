# JJ Buffet 48-hour review report – run steps

Follow these steps in order. Settings (place ID, recipient, reply tone, complaint format) are in `criteria.md`; read it first. If the prompt says **nosend**, do everything except step 7 and the duplicate guard.

All paths below are relative to `jj-buffet-agent/`. `DATE` is today's date in London as `YYYY-MM-DD`.

## 1. Get the files
The agent lives on branch `claude/cool-franklin-otwedh`, not on the website's main branch:
```
git fetch origin claude/cool-franklin-otwedh && git checkout claude/cool-franklin-otwedh && git pull origin claude/cool-franklin-otwedh
```

## 2. Duplicate guard
Search Gmail (`search_threads`) for `in:sent to:wkteohuk@gmail.com subject:"Google Reviews Report" newer_than:3d -subject:TEST`. `[TEST]` copies don't count. If a report was sent less than 46 hours ago, stop and say so. Nothing else to do.

## 3. Fetch reviews
- Work out the cutoff: `date -u -d '48 hours ago' +%s`.
- Call Outscraper `google_maps_reviews` with query `["ChIJl_XT4ggFdkgRM62dgnPYPm8"]`, `sort: newest`, `cutoff: <that timestamp>`, `reviews_limit: 200`, `language: en`, `execution_mode: async`. (Sync mode times out.)
- Poll `requests_get` with the returned id until the status is `Success`. If it fails twice, email nothing and report the error.
- Write the result to `reports/raw/DATE_raw.json` as `[{"name": ..., "reviews_data": [...]}]`. For each review keep only `review_id`, `author_title`, `review_text`, `review_rating`, `review_timestamp`, `owner_answer`.

## 4. Filter to the window
```
python3 scripts/filter_reviews.py reports/raw/DATE_raw.json reports/raw/DATE_window.json
```

## 5. Write the analysis
Read `reports/raw/DATE_window.json` and write `reports/raw/DATE_analysis.json` in the format at the top of `scripts/build_report.py`. Use `reports/raw/2026-10-21_analysis.json` as the model for tone and detail. Follow `criteria.md`:
- every review, with `text_en` in English. For non-English reviews also fill `original_text`, `original_language` and `reply_original`.
- a specific, human reply for every review, including rating-only ones
- up to three complaints, most-mentioned first, each with a concrete corrective action and a preventive action. Leave the list empty if there are none.
- a two or three sentence `overview`
- copy `window_start` and `window_end` from the window file

If there were no reviews, write an analysis with empty `reviews` and `complaints` and an overview saying so. The report is still sent.

## 6. Build and check the PDF
```
python3 scripts/build_report.py reports/raw/DATE_analysis.json reports/JJ_Buffet_Reviews_DATE.pdf
python3 -c "import sys,re;from pypdf import PdfReader;t=' '.join(p.extract_text() for p in PdfReader(sys.argv[1]).pages);b=re.findall(r'(?i)outscraper|\bAI\b|artificial intelligence|chatgpt|claude|anthropic|automated|scrap',t);print('FAIL',b) if b else print('clean')" reports/JJ_Buffet_Reviews_DATE.pdf
```
If the check prints FAIL, reword the analysis and rebuild. Render page 1 (`pdftoppm -png -r 60 -f 1 -l 1 ...`) and look at it before sending.

## 7. Email it
- `base64 -w0 reports/JJ_Buffet_Reviews_DATE.pdf` and pass it as the attachment `content` (`mimeType: application/pdf`, filename `JJ_Buffet_Reviews_DATE.pdf`).
- Send with Gmail `send_message` to `wkteohuk@gmail.com`, subject `JJ Buffet – Google Reviews Report – <start> to <end>` (London dates, e.g. `19 Oct to 21 Oct 2026`).
- Plain-text body: a short greeting, the review count and average rating, the top complaint in one line, "Full details and suggested replies are in the attached report.", signed "Jack". Don't mention any tools or AI.
- Then search Gmail sent mail to confirm it went out with the attachment.

## 8. Log and save
Add one line to the run log in `README.md` (date, review count, average, top complaint, sent yes/no). Commit `reports/` and `README.md` and push:
```
git add -A . && git commit -m "JJ Buffet review report DATE" && git push -u origin claude/cool-franklin-otwedh
```
