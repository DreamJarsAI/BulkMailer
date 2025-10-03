# Evaluation Guide

Use these scenarios to verify the application works end-to-end.

## Scenario 1 – Happy Path

1. Download the sample CSV from the landing page.
2. Replace the sample names with two test recipients and save.
3. Upload the CSV on the **Upload Recipients** step.
4. Paste this subject/body on the **Provide Template** step:
   - Subject: `Reminder for {{ first_name }}`
   - Body:
     ```
     Dear {{ title }} {{ last_name }},

     This is a quick reminder about tomorrow's meeting.

     Best,
     Student Services
     ```
5. Review the previews; toggle one message off and back on.
6. Click **Connect Google account**, complete the OAuth flow, then **Send selected emails**.
7. Confirm the Gmail “Sent” folder shows personalized messages.

## Scenario 2 – Invalid CSV Row

1. Add a row with a malformed email to the CSV.
2. Upload the file. The app should list the row-level validation error and keep valid rows.
3. Fix the email and re-upload to proceed.

## Scenario 3 – Template Placeholder Error

1. Provide a template that references `{{ nickname }}`.
2. Submission should fail with an explanatory error.
3. Replace the placeholder with `{{ first_name }}` and resubmit.

## Scenario 4 – DOCX Template

1. Create a DOCX document with the desired body text (no tables/images).
2. Upload the DOCX on the template step (leave the body textbox empty).
3. Ensure the parsed text appears in the confirmation preview.

## Scenario 5 – OAuth Token Reuse

1. Authorize Gmail once and send a batch.
2. Restart the app (or redeploy) without deleting `data/token_store.json`.
3. Verify you can send another batch without reauthorizing.

## Expected Results Summary

- CSV uploads with valid rows succeed; invalid rows display precise error messages.
- Templates render only when allowed placeholders are used.
- Preview page shows personalized subject and body per recipient.
- Gmail authorization is required only once while the refresh token remains.
- Send results report `sent`, `failed`, or `skipped` status per recipient.
