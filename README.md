# XinYa TOCFL — public student interface

Student website: https://colinkristianti.github.io/tocfl-practice-web/

Band A and Band B Volumes 1–5 now contain official mock-test question images and audio: 50 listening and 50 reading items per band and volume (1,000 items total). The October 10 import adds 800 items and 400 per-question audio clips for Volumes 2–5. New-volume explanations remain unwritten; Thai copy still needs native-speaker review. Teacher-assigned band and volume permissions remain enforced by the private backend.

This repository stores the public student interface and official-derived image/audio assets. Student data, credentials, answer keys, progress and teacher management remain in the private Google backend. Original content retains its original rights. Source URLs and checksums are recorded in assets/official/volumes2-5-manifest.json and scripts/import-volumes/manifest.json; Volume 1 attribution is in assets/official/vol1/README.md.

## Publish and maintenance

GitHub Pages publishes main, root directory. Keep API_URL pointed at the owner’s deployed backend. The backend must allow the exact GitHub Pages origin and preserve authentication and band/volume checks. Never commit student exports, passwords, tokens or private backend configuration. Browser code and its API endpoint are public.

Chinese/Thai copy loads from the translation backend. Updates are cached for about 30 seconds; users must reload to see changes. Existing book caches can last up to 60 seconds. The manual GitHub Actions workflow Build verified official volumes 2–5 rebuilds assets from the 48 official public source URLs only when their SHA-256 checksums match; it has no Google Sheets or student-data access.

Private source, import audit, full question snapshots and handover details are in colinkristianti/tocfl-practice, content-import/volumes2-5/README.md. Next: teacher feedback, explanations and proofreading, then a small-class pilot.

## Handover

Transfer this repository and the private source repository separately. Google Sheets and Apps Script ownership must also be handled separately. The new owner must authorize/deploy their backend if changing ownership, update the allowed website origin and API_URL, and verify login, volume restrictions, answer persistence and mobile audio before retiring the old deployment.
