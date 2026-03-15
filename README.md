Veteran Disability Claims Journey Copilot is an AI-native assistant that helps users understand where they are in the VA disability claims journey, identify a likely next path, surface possible evidence gaps, and generate a citation-backed readiness summary using a small set of official VA web pages encoded in `backend/data/rules.json`.

## Running the backend

1. Create and activate a Python 3.10+ virtual environment.
2. From the project root, install backend dependencies:

   ```bash
   python -m pip install -r backend/requirements.txt
   ```

3. Set environment variables for your LLM provider (for example):

   ```bash
   set LLM_MODEL=your-model-name
   # and configure backend/utils/llm_client.py for your provider
   ```

4. Start the FastAPI server:

   ```bash
   python -m uvicorn backend.main:app --reload
   ```

The healthcheck is available at `http://localhost:8000/api/health/`.

## Running the frontend

1. From `frontend/`:

   ```bash
   npm install
   npm run dev
   ```

2. By default the frontend expects the backend at `http://localhost:8000`. You can override this by setting `VITE_BACKEND_URL` in a `.env` file in `frontend/`.

## Safety and scope

- The app is educational and organizational only.
- It does **not** file or submit anything to VA on the user’s behalf.
- It does **not** act as an accredited representative or provide legal advice.
- It does **not** predict claim approval, disability ratings, or back pay.
- All official VA process logic (routes, forms, timelines, evidence rules) comes only from `backend/data/rules.json`. If something is not represented there, the app should answer cautiously or say it cannot determine the answer confidently.

