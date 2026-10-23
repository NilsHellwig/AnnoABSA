# Changelog

All notable changes to AnnoABSA are documented in this file.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses [Semantic Versioning](https://semver.org/).
The current version is defined in [`version.py`](version.py) and shown by `annoabsa --version`, the `/version` endpoint and the web interface header.

## [1.1.0] - 2026-10-23

### Security

- The backend no longer accepts requests from arbitrary websites. Previously, CORS allowed every origin, so a page on another website open in the annotator's browser could modify the annotation data. Requests whose `Origin` is not the AnnoABSA frontend (or that browsers mark as cross-site) are now rejected with `403`. Unknown `Host` headers are rejected too, which blocks DNS-rebinding attacks. Additional origins can be allowed with `--allowed-origins`.
- Backend and frontend responses now send `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Content-Security-Policy: frame-ancestors 'none'` and `Referrer-Policy: no-referrer`.
- Removed the unused legacy endpoint `POST /data/{idx}`, which wrote to a hard-coded `annotations.csv`.

### Fixed

- Concurrent saves (several annotators on one backend and data file) could interleave and leave a data file that was no longer valid JSON or CSV. Read-modify-write cycles are now serialised (across threads and, on POSIX, across processes), and files are written atomically through a temporary file and `os.replace`.
- Saving an item while the "new annotation" form still contained a partly filled tuple silently discarded that tuple. The annotator is now asked to confirm before the tuple is discarded.
- Malformed input files (invalid JSON or CSV, wrong top-level structure, missing `text` column or field, `label` values that are not lists) are now reported with a clear error message and location, both by the CLI at startup and in the web interface. Previously they caused generic server errors.
- Requests for an index that is out of range now return `404` instead of `500`.
- The average annotation time was computed incorrectly for CSV files.
- `--session-id` was ignored by the CLI.
### Added

- `--export PATH` writes the data and annotations to a CSV file that is safe to open in spreadsheet programs: cells starting with `=`, `+`, `-`, `@`, tab or carriage return are prefixed with `'`. The working data file is left unchanged, as altering the text would invalidate stored phrase positions.
- Versioning: `version.py`, `annoabsa --version`, `GET /version`, a `version` field in `GET /settings`, and the version in the UI header.
- Test suites: pytest for the backend (`pytest`) and Playwright end-to-end tests for the web interface (`npm run test:e2e`), covering the fixes above. UI elements used by the tests carry `data-testid` attributes.
- Prettier for the frontend (`npm run format`, `npm run format:check`) and `npm run typecheck`.

### Changed

- Updated dependencies: Vite 8, `@vitejs/plugin-react` 6, Tailwind CSS 4 (migrated with the official upgrade tool), TypeScript 7, React 19.3, FastAPI 0.161, pandas 3, openai 3. `npm audit` reports no known vulnerabilities.
- Minimum requirements are now Python 3.11 and Node.js 20.19 (or 22.12).
- The CLI passes the frontend port and host to Vite through environment variables instead of rewriting `vite.config.js`.
- FastAPI startup uses the `lifespan` handler instead of the deprecated `on_event`.

## [1.0.0] - 2026-10-20

- Version described in the LREC 2026 paper.

[1.1.0]: https://github.com/NilsHellwig/AnnoABSA/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/NilsHellwig/AnnoABSA/releases/tag/v1.0.0
