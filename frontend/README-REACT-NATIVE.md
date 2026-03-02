# Smart Criminal Judgment Analysis — React Native (Web + Mobile)

This is the **React Native (Expo)** version of the Smart Criminal Judgment Analysis System. It runs on **web** and **mobile** (iOS/Android) with a single codebase and a law-sector-focused design.

## Design (Law sector)

- **Colours**: Deep burgundy/maroon primary, gold accent, parchment/cream backgrounds for a professional legal look.
- **Typography**: Serif-style headings, clear hierarchy.
- **Responsive**: Layout adapts to phone, tablet, and desktop; navigation works on touch and mouse.

## Run the app

1. **Install dependencies** (if not already done):
   ```bash
   npm install
   ```

2. **Web**:
   ```bash
   npm run web
   ```
   Then open the URL shown (e.g. http://localhost:8081).

3. **Mobile (Expo Go)**:
   ```bash
   npm start
   ```
   Scan the QR code with Expo Go (Android) or the Camera app (iOS).

4. **Android emulator / iOS simulator**:
   ```bash
   npm run android
   # or
   npm run ios
   ```

## Project structure

- `app/` — Expo Router screens (file-based routes):
  - `index.tsx` — Home (hero, component cards, upload)
  - `about.tsx` — About Us
  - `contact.tsx` — Contact form + useful links
  - `component1.tsx` … `component4.tsx` — Component overview pages
  - `processing.tsx` — Analysis progress (simulated stages)
  - `results.tsx` — Case analysis + arguments report (tabs)
- `components/` — Layout (header/footer), UI (Card, Button, etc.), FileUploadSection
- `theme.ts` — Colours, spacing, typography
- `api.ts` — API base URLs and types (analyze/arguments)

## Backend

Set your backend base URL in `api.ts` or via environment. The app calls:

- `POST /api/v1/analyze` — case analysis
- `POST /api/v1/arguments` — arguments report

If the backend is not available, the upload flow still runs with **demo data** (processing → results with placeholder content).

## Troubleshooting

- **EPERM / "operation not permitted"** when running `npm run web` or `npm start` (e.g. `mkdir 'C:\Users\...\.expo'`): Expo is trying to create a config folder in your user directory. Fixes:
  - Create the folder yourself: `mkdir %USERPROFILE%\.expo` (Windows) or `mkdir ~/.expo` (Mac/Linux), then run the command again.
  - Or run your terminal/IDE as Administrator (Windows) if you’re in a restricted environment.
- **npm audit** reports many high severity issues: These come from Expo and React Native’s dependency tree. `npm audit fix` often can’t fix them without breaking the stack. They are addressed in newer major versions of Expo/React Native when you upgrade.

## Original static site

The previous HTML/CSS/JS version is still in the repo (e.g. `index.html`, `styles/`, `js/`). You can remove those files if you only use this React Native app.
