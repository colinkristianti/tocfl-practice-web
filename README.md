# Xinya TOCFL — public student interface

This repository contains only the student website. Student data, credentials, answer keys and teacher management remain in the private Google backend. Band A and Band B Volume 1 contain official mock-test question images and audio: 50 listening and 50 reading items per band (200 items total). Volumes 2–5 remain unavailable. Original content retains its original rights; see assets/official/vol1/README.md for source attribution.

## Publish
In Settings → Pages select Deploy from a branch, main, / (root). No build or paid service is required.

## Maintenance
Edit index.html through a reviewed GitHub change. Keep the API_URL pointed at the owner’s deployed backend. The private backend must allow the exact GitHub Pages origin and preserve its student authentication and band/volume checks. Never commit student exports, passwords, tokens, spreadsheet contents, or private backend configuration. Browser code and its API endpoint are public.

Chinese/Thai wording loads from the private translation backend; Thai text still needs native-speaker review.

## Handover
Transfer this repository and the private source repository separately. The new owner must copy/transfer the Google sheets, authorize and deploy their Apps Script, update the backend’s allowed website origin and API_URL, and test login, volume restrictions, answer persistence and mobile audio before retiring the old deployment.
