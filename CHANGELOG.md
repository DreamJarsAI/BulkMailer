# Changelog

## 2024-04-04
- Initial implementation of the Email Batch Assistant FastAPI app.
- Added CSV upload, template handling (text/DOCX), previews, and Gmail OAuth send flow.
- Created encrypted token storage, sample CSV, and simple Jinja UI.
- Added pytest coverage for CSV parsing, template rendering, and preview flow.
- Documented setup, evaluation scenarios, and backlog tasks.

## 2025-10-03
- Redesigned UI with guided Gmail Cloud setup, in-session storage of OAuth client credentials, and inline connection prompts.
- Combined recipient upload and template capture on a single step with clearer sample CSV access.
- Added subject entry and per-recipient body editing on the preview screen with approval toggles and bulk send guidance.
- Updated routes/templates to support session-scoped Gmail credentials securely and refreshed smoke tests.
