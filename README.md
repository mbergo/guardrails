# AIREADY Guardrails Demo (FastAPI Version)

This project is an interactive web application demonstrating various "guardrail" concepts for AI-driven data queries. It features a Python FastAPI backend to securely manage API keys and serve the dynamic frontend, which allows users to test AI responses from **Google Gemini** and **OpenAI** against predefined safety and validation mechanisms.

The application showcases how to build layers of checks around AI outputs for accuracy, consistency, safety, and adherence to expected structures (like SQL or JSON).

**This version enhances security by managing API keys on the backend, loaded from a `.env` file.**

## Features

*   **FastAPI Backend:**
    *   Serves the single-page HTML application.
    *   Securely manages API keys for Google Gemini and OpenAI, loaded from a `.env` file (keys are never exposed to the client).
    *   Fetches available models from AI providers and injects them into the frontend.
    *   Proxies AI calls from the client to the respective AI provider APIs.
*   **Interactive UI (Served by FastAPI):**
    *   **Custom Header:** "AIREADY Guardrails by D. Joncas®" in the top-left.
    *   **Improved Left Sidebar Menu:** Enhanced styling for navigation.
    *   **Center Panel:** Main interaction area for inputting prompts, triggering guardrail scenarios, and viewing AI responses with guardrail feedback.
    *   **Right Panel (Settings):**
        *   AI Provider selection (Google Gemini / OpenAI).
        *   Dynamic model selection dropdown, populated based on configured API keys.
        *   Advanced feature toggles:
            *   Enable Web Search (Google Gemini Only via native API support).
            *   Request Structured Output (JSON mode for compatible models).
        *   Model parameter adjustments (Temperature, Max Output Tokens).
        *   History log of actions and guardrail triggers.
*   **Live AI Integration (via Backend):**
    *   Connects to Google Gemini models.
    *   Connects to OpenAI models.
*   **Comprehensive Guardrail Demonstrations:**
    *   **Level 1 Base Rails:** Empty/Incomplete output, Invalid SQL, Mismatched JSON, Unexpected Data Types, API Timeouts.
    *   **Edge Case Rails:** Phantom Data, Temporal (Future Data), Contradiction Detection.
    *   **Query Variations (Mocked):** Echo, Déjà, Butterfly Rails (kept mocked for consistent demonstration).
    *   **Other Rails:** Bias Detection, Confidence Threshold, Sensitivity Rail.

## Project Structure

*   `main.py`: Single Python file containing the FastAPI application, all HTML, CSS, and JavaScript for the frontend.
*   `requirements.txt`: Lists Python dependencies.
*   `.env` (User-created): Stores API keys for Google and OpenAI. **This file is crucial and must be created by the user.**

## Prerequisites

*   Python 3.8+
*   An active API key for Google AI Studio (for Gemini models).
*   An active API key for OpenAI.
*   Access to a terminal or command prompt.

## Setup and Running

1.  **Clone/Download:** Get the project files (`main.py`, `requirements.txt`).

2.  **Create `.env` File:**
    In the same directory as `main.py`, create a file named `.env` and add your API keys:
    ```env
    GOOGLE_API_KEY=your_google_gemini_api_key_here
    OPENAI_API_KEY=your_openai_api_key_here
    ```
    Replace the placeholder values with your actual keys.

3.  **Create a Virtual Environment (Recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

4.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

5.  **Run the FastAPI Application:**
    ```bash
    uvicorn main:app --reload
    ```
    *   `--reload` enables auto-reloading during development if you modify `main.py`.
    *   The application will typically be available at `http://127.0.0.1:8000`.

6.  **Access in Browser:** Open your web browser and navigate to `http://127.0.0.1:8000`.

## How to Use the Application

1.  **AI Provider and Model Selection:**
    *   The right-hand panel will show available AI providers.
    *   Upon selecting a provider, the "Selected Model" dropdown will populate with models fetched by the backend using your configured API keys. If there's an error (e.g., invalid key), a message will appear.
2.  **Advanced Features:**
    *   **Web Search:** Can be enabled for Google Gemini to allow the model to ground its responses with web search results.
    *   **Structured Output (JSON):** Can be toggled to request the AI to respond in JSON format (model compatibility varies).
3.  **Select a Guardrail Demo:** Click on a guardrail name in the left-hand menu.
4.  **Interact with the Demo:**
    *   The center panel will display the demo interface.
    *   Enter a relevant prompt to test the specific guardrail.
    *   Click "Run Demo". The request will be sent to your FastAPI backend, which then calls the selected AI provider.
5.  **Observe Results:**
    *   The AI's response (or an error message) will appear in the output box.
    *   Guardrail feedback and history logs are displayed as before.

## Guardrail Concepts Demonstrated

*(This section can mirror the one in the previous README, outlining the purpose of each guardrail category and specific rails.)*

*   **Level 1 Base for Rails:** Fundamental checks on AI output validity.
*   **Edge Case Rail Buttons:** Handling specific problematic AI behaviors.
*   **Buttons for Identifying Query Variations:** Tools to understand why query results might differ (demonstrated with mocked data).
*   **Other Specific Rails:** Addressing concerns like bias, confidence, and sensitivity.

## Important Considerations

*   **Backend Management:** API keys are now managed securely on the backend. The client-side JavaScript no longer handles them directly.
*   **Model Availability:** The models listed are those accessible with your API keys and filtered by basic criteria in the backend.
*   **Prompt Engineering:** Effective demonstration still relies on crafting good prompts to trigger desired AI behaviors and test guardrail responses.
*   **API Costs:** Live API calls made via the backend will incur costs based on your provider's pricing.
*   **Error Handling:** The application includes error handling for both backend operations (like model fetching) and AI provider API calls. Check the browser console and terminal output for detailed error messages.

---

*This README has been updated for the FastAPI version of the AIREADY Guardrails Demo.*