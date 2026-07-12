# MonkeyZoo Production Workflow System — Studio Landing Page Static Preview

This folder contains a fully static client-side preview of the **MonkeyZoo Studio** workspace. It has been prepared for hosting via GitHub Pages.

## Hosted Preview Notice
This preview runs entirely inside your browser using static demonstration data. All interface behaviors, dashboard metrics, navigation routing tabs, overlap comparisons, and the 5-step Story Builder Wizard run client-side.

- **Mock Data Enabled**: Interactive elements fetch mock records from `static/app.js` to showcase character data and story planning.
- **Backend-dependent Features**: Functions that save YAML configs, build issues, execute local python scripts, or trigger ComfyUI image render queues are disabled and labeled for safety.

## Run Local Backend for Full Production Features
To run the full interactive studio suite with active Flask API endpoints, database operations, and generation pipelines:
1. Open your terminal in the workspace root.
2. Run:
   ```bash
   python character-bibles/_review_app/app.py
   ```
3. Navigate to: `http://127.0.0.1:8765`
