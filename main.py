import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles # Not strictly needed for single file, but good practice
from fastapi.templating import Jinja2Templates # Not strictly needed for pure string HTML, but good for future
from dotenv import load_dotenv
import httpx # For making API calls from backend to fetch models
import asyncio # For concurrent model fetching

# Load environment variables from .env file
load_dotenv()

# --- Configuration ---
# It's better to get these from environment variables as well for flexibility
# but for simplicity in this single file, we'll define some defaults.
# You should ideally have these in your .env too or a config system.
DEFAULT_GOOGLE_API_URL = "https://generativelanguage.googleapis.com"
DEFAULT_OPENAI_API_URL = "https://api.openai.com"

# --- FastAPI App Setup ---
app = FastAPI()

# In a real app, you'd serve static files like CSS/JS separately.
# For this single file demo, we embed them in HTML.
# app.mount("/static", StaticFiles(directory="static"), name="static") # Example

# --- Helper function to fetch models (backend-side) ---
async def fetch_provider_models(provider_name: str, api_key: str):
    models = []
    default_model_id = ""
    if not api_key:
        return {"models": [], "default_model": "", "error": f"{provider_name} API Key not configured."}

    try:
        async with httpx.AsyncClient() as client:
            if provider_name == "Google Gemini":
                url = f"{DEFAULT_GOOGLE_API_URL}/v1beta/models?key={api_key}"
                response = await client.get(url)
                response.raise_for_status() # Raise an exception for HTTP errors
                data = response.json()
                fetched_models = data.get("models", [])
                models = sorted([
                    {"id": m.get("name", "").replace("models/", ""), "name": m.get("displayName", m.get("name", "").replace("models/", ""))}
                    for m in fetched_models
                    if m.get("supportedGenerationMethods") and "generateContent" in m.get("supportedGenerationMethods") and ("gemini" in m.get("name", "") or "text-" in m.get("name", ""))
                ], key=lambda x: x["name"])
                default_model_id = next((m["id"] for m in models if m["id"] == "gemini-1.5-pro-latest"), models[0]["id"] if models else "")

            elif provider_name == "OpenAI":
                url = f"{DEFAULT_OPENAI_API_URL}/v1/models"
                headers = {"Authorization": f"Bearer {api_key}"}
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                data = response.json()
                fetched_models = data.get("data", [])
                models = sorted([
                    {"id": m.get("id"), "name": m.get("id")}
                    for m in fetched_models
                    if "gpt" in m.get("id", "") or "text-davinci" in m.get("id", "") # Basic filter
                ], key=lambda x: x["id"], reverse=True)
                default_model_id = next((m["id"] for m in models if m["id"] == "gpt-3.5-turbo"), models[0]["id"] if models else "")
        return {"models": models, "default_model": default_model_id}
    except httpx.HTTPStatusError as e:
        error_detail = "Unknown error"
        try:
            error_detail = e.response.json().get("error", {}).get("message", e.response.text)
        except:
            error_detail = e.response.text
        return {"models": [], "default_model": "", "error": f"Error fetching {provider_name} models: {e.response.status_code} - {error_detail}"}
    except Exception as e:
        return {"models": [], "default_model": "", "error": f"Error fetching {provider_name} models: {str(e)}"}

# --- HTML Content ---
# This will be a very long string. In a real app, use Jinja2Templates.
HTML_CONTENT = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AIREADY Guardrails by D. Joncas®</title>
    <style>
        :root {{
            --bg-color: #1a1a1d; /* Slightly darker bg */
            --sidebar-bg: #232328; /* Darker sidebar */
            --content-bg: #1a1a1d;
            --text-color: #e0e0e0; /* Brighter text */
            --accent-color: #4A90E2; /* A nice blue */
            --accent-hover-color: #357ABD;
            --border-color: #38383f;
            --input-bg: #2c2c31;
            --button-bg: var(--accent-color);
            --button-text: #ffffff;
            --hover-bg: #333338;
            --active-bg: var(--accent-hover-color);
            --error-color: #e74c3c;
            --warning-color: #f39c12;
            --success-color: #2ecc71;
            --header-font: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; /* Modern font */
        }}

        body {{
            font-family: 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
            margin: 0;
            background-color: var(--bg-color);
            color: var(--text-color);
            display: flex;
            height: 100vh;
            overflow: hidden;
        }}

        .app-container {{ display: flex; width: 100%; height: 100%; }}

        .sidebar {{
            background-color: var(--sidebar-bg);
            padding: 0; /* Remove padding to use full width for header */
            overflow-y: auto;
            border-right: 1px solid var(--border-color);
            min-height: 100%;
            display: flex;
            flex-direction: column;
            box-shadow: 2px 0 5px rgba(0,0,0,0.1);
        }}

        .sidebar-left {{ width: 280px; }}
        .sidebar-right {{ width: 360px; border-left: 1px solid var(--border-color); border-right: none; padding: 15px;}} /* Restore padding for content */

        .sidebar-header {{
            padding: 20px 15px;
            background-color: var(--accent-color); /* Header bg */
            color: var(--button-text);
            text-align: left;
            border-bottom: 1px solid var(--accent-hover-color);
        }}
        .sidebar-header h1 {{
            font-family: var(--header-font);
            font-size: 1.6em;
            margin: 0 0 5px 0;
            font-weight: 600;
        }}
        .sidebar-header .subtitle {{
            font-size: 0.9em;
            opacity: 0.9;
            font-weight: 300;
        }}

        .sidebar-nav {{ padding: 15px; flex-grow: 1; }} /* Add padding for nav items */

        .sidebar .sidebar-nav ul {{ list-style: none; padding: 0; }}
        .sidebar .sidebar-nav ul li strong {{
            display: block;
            color: var(--accent-color);
            font-size: 0.95em;
            padding: 12px 10px 8px 10px;
            margin-top: 10px;
            border-bottom: 1px solid var(--border-color);
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        .sidebar .sidebar-nav ul li a {{
            display: flex; /* Use flex for icon alignment */
            align-items: center;
            gap: 8px; /* Space between icon and text */
            padding: 10px 12px;
            text-decoration: none;
            color: var(--text-color);
            border-radius: 5px;
            margin: 5px 0;
            font-size: 0.9em;
            transition: background-color 0.2s ease, color 0.2s ease;
        }}
        .sidebar .sidebar-nav ul li a:before {{ /* Basic icon placeholder */
            content: '▹'; /* Or use ::before with background images for real icons */
            font-size: 1.1em;
            opacity: 0.7;
        }}
        .sidebar .sidebar-nav ul li a:hover {{ background-color: var(--hover-bg); color: #fff; }}
        .sidebar .sidebar-nav ul li a.active {{ background-color: var(--active-bg); color: var(--button-text); font-weight: 500; }}
        .sidebar .sidebar-nav ul li a.active:before {{ color: var(--button-text); opacity: 1;}}


        .main-content {{ flex-grow: 1; background-color: var(--content-bg); padding: 25px; overflow-y: auto; display: flex; flex-direction: column; }}
        .main-content h2 {{ margin-top: 0; border-bottom: 1px solid var(--border-color); padding-bottom: 15px; font-size: 1.8em; font-weight: 500; }}

        .demo-area {{ flex-grow: 1; background-color: var(--sidebar-bg); padding: 20px; border-radius: 8px; border: 1px solid var(--border-color); display: flex; flex-direction: column; box-shadow: 0 2px 8px rgba(0,0,0,0.15);}}
        .demo-area .controls {{ margin-bottom: 20px; }}
        .demo-area p {{ margin-bottom: 12px; line-height: 1.6;}}
        .demo-area button {{ background-color: var(--button-bg); color: var(--button-text); border: none; padding: 12px 18px; border-radius: 5px; cursor: pointer; margin-right: 10px; margin-bottom: 10px; font-size: 0.95em; transition: background-color 0.2s ease; }}
        .demo-area button:hover {{ background-color: var(--accent-hover-color); }}
        .demo-area button:disabled {{ background-color: #555; cursor: not-allowed; }}
        .demo-area input[type="text"], .demo-area textarea, .demo-area select {{ width: calc(100% - 24px); padding: 12px; background-color: var(--input-bg); color: var(--text-color); border: 1px solid var(--border-color); border-radius: 5px; margin-bottom: 12px; font-size: 0.95em; }}
        .demo-area textarea {{ min-height: 90px; resize: vertical; flex-grow: 1; }}

        .output-box {{ background-color: var(--bg-color); padding: 15px; border: 1px solid var(--border-color); border-radius: 5px; white-space: pre-wrap; word-wrap: break-word; margin-top: 15px; min-height: 120px; flex-grow: 1; overflow-y: auto; font-family: 'Consolas', 'Monaco', monospace; font-size: 0.9em; }}
        .output-box.error {{ border-left: 4px solid var(--error-color); background-color: rgba(231, 76, 60, 0.05);}}
        .output-box.warning {{ border-left: 4px solid var(--warning-color); background-color: rgba(243, 156, 18, 0.05);}}
        .output-box.success {{ border-left: 4px solid var(--success-color); background-color: rgba(46, 204, 113, 0.05);}}


        .settings-panel {{ flex-grow: 1; display: flex; flex-direction: column; }} /* For history log to stick to bottom */
        .settings-panel-content {{ flex-grow: 1; overflow-y: auto; }} /* Scrollable content */
        .settings-panel .setting {{ margin-bottom: 18px; }}
        .settings-panel label {{ display: block; margin-bottom: 6px; font-size: 0.9em; font-weight: 500; }}
        .settings-panel input[type="range"] {{ width: 100%; }}
        .settings-panel input[type="number"], .settings-panel input[type="password"], .settings-panel input[type="text"], .settings-panel select {{ width: calc(100% - 16px); padding: 10px 8px; background-color: var(--input-bg); color: var(--text-color); border: 1px solid var(--border-color); border-radius: 4px; margin-bottom: 5px; font-size:0.9em; }}

        .toggle-switch {{ position: relative; display: inline-block; width: 50px; height: 24px; margin-left: 10px; vertical-align: middle;}}
        .toggle-switch input {{ opacity: 0; width: 0; height: 0; }}
        .toggle-slider {{ position: absolute; cursor: pointer; top: 0; left: 0; right: 0; bottom: 0; background-color: #505055; transition: .4s; border-radius: 24px; }}
        .toggle-slider:before {{ position: absolute; content: ""; height: 18px; width: 18px; left: 3px; bottom: 3px; background-color: white; transition: .4s; border-radius: 50%; }}
        input:checked + .toggle-slider {{ background-color: var(--accent-color); }}
        input:checked + .toggle-slider:before {{ transform: translateX(26px); }}

        .history-log-container {{ border-top: 1px solid var(--border-color); padding-top:15px; margin-top: auto; /* Pushes to bottom */ }}
        .history-log {{ font-size: 0.8em; max-height: 180px; overflow-y: auto; border: 1px solid var(--border-color); padding: 8px; background-color: var(--bg-color); border-radius: 4px; }}
        .history-log div {{ padding: 4px 0; border-bottom: 1px dotted #444; font-family: 'Consolas', 'Monaco', monospace; }}
        .history-log div:last-child {{ border-bottom: none; }}
        .loading-indicator {{ display: none; margin: 10px 0; color: var(--accent-color); font-weight: 500; }}
        .status-message {{ padding: 8px 12px; margin-bottom: 15px; border-radius: 4px; font-size: 0.9em; border: 1px solid transparent; }}
        .status-message.success {{ background-color: rgba(46, 204, 113, 0.1); color: var(--success-color); border-color: var(--success-color);}}
        .status-message.error {{ background-color: rgba(231, 76, 60, 0.1); color: var(--error-color); border-color: var(--error-color);}}
        .status-message.info {{ background-color: rgba(52, 152, 219, 0.1); color: #3498db; border-color: #3498db;}}

    </style>
</head>
<body>
    <div class="app-container">
        <aside class="sidebar sidebar-left">
            <div class="sidebar-header">
                <h1>AIREADY Guardrails</h1>
                <div class="subtitle">by D. Joncas®</div>
            </div>
            <nav class="sidebar-nav">
                <ul id="guardrail-list"></ul>
            </nav>
        </aside>

        <main class="main-content">
            <h2 id="current-guardrail-title">Welcome to AI Guardrails Demo</h2>
            <div class="demo-area" id="demo-area-content">
                <p>Select a guardrail from the left menu to begin. <br>AI provider and model can be configured in the right-side panel.</p>
            </div>
        </main>

        <aside class="sidebar sidebar-right">
            <div class="settings-panel">
                <div class="settings-panel-content">
                    <h3>API & Model Settings</h3>
                    <div id="api-status-message" class="status-message" style="display:none;"></div>
                    <div class="setting">
                        <label for="api-provider">AI Provider:</label>
                        <select id="api-provider">
                            <option value="google">Google Gemini</option>
                            <option value="openai">OpenAI</option>
                        </select>
                    </div>
                    <div class="setting">
                        <label for="model-selector">Selected Model:</label>
                        <select id="model-selector">
                            <!-- Models will be populated by JavaScript -->
                        </select>
                        <div id="model-error-message" class="status-message error" style="display:none; font-size:0.8em; padding:5px; margin-top:5px;"></div>
                    </div>
                    <hr style="border-color: var(--border-color); margin: 20px 0;">
                    <h3>Advanced Features</h3>
                    <div class="setting">
                        <label for="web-search-toggle" style="display:inline-block;">Enable Web Search (Gemini Only):</label>
                        <label class="toggle-switch">
                            <input type="checkbox" id="web-search-toggle">
                            <span class="toggle-slider"></span>
                        </label>
                    </div>
                    <div class="setting">
                        <label for="structured-output-toggle" style="display:inline-block;">Request Structured Output (JSON):</label>
                        <label class="toggle-switch">
                            <input type="checkbox" id="structured-output-toggle">
                            <span class="toggle-slider"></span>
                        </label>
                    </div>
                    <hr style="border-color: var(--border-color); margin: 20px 0;">
                    <h3>AI Model Parameters</h3>
                    <div class="setting">
                        <label for="temperature">Temperature: <span id="temp-value">0.7</span></label>
                        <input type="range" id="temperature" name="temperature" min="0" max="2" step="0.1" value="0.7">
                    </div>
                    <div class="setting">
                        <label for="max-tokens">Max Output Tokens:</label>
                        <input type="number" id="max-tokens" name="max-tokens" value="1024">
                    </div>
                </div>
                <div class="history-log-container">
                    <h3>History</h3>
                    <div class="history-log" id="history-log-content">
                        <div>App Initialized.</div>
                    </div>
                </div>
            </div>
        </aside>
    </div>

    <script>
        // --- Global Variables & Constants ---
        const guardrails = [ /* ... (Your existing guardrails array) ... */ 
            { id: "emptyIncomplete", name: "Empty/Incomplete AI Output", category: "Level 1 Base" }, { id: "invalidSql", name: "Invalid SQL Query by AI", category: "Level 1 Base" }, { id: "mismatchedOutput", name: "Mismatched AI JSON & Structure", category: "Level 1 Base" }, { id: "unexpectedDataTypes", name: "Unexpected Data Types in AI JSON", category: "Level 1 Base" }, { id: "timeoutsFailures", name: "API Timeouts/Failures", category: "Level 1 Base" }, { id: "phantomRail", name: "Phantom Data Rail", category: "Edge Case Rails" }, { id: "temporalRail", name: "Temporal Rail (Future Data)", category: "Edge Case Rails" }, { id: "contradictionRail", name: "Contradiction Detection Rail", category: "Edge Case Rails" }, { id: "echoRail", name: "Echo Rail (Data Changes - Mocked)", category: "Query Variations" }, { id: "dejaRail", name: "Déjà Rail (Env. Factors - Mocked)", category: "Query Variations" }, { id: "butterflyRail", name: "Butterfly Rail (Subtle Factors - Mocked)", category: "Query Variations" }, { id: "biasDetection", name: "Bias Detection Rail", category: "Other Rails" }, { id: "confidenceThreshold", name: "Confidence Threshold Rail", category: "Other Rails" }, { id: "sensitivityRail", name: "Sensitivity Rail", category: "Other Rails" },
        ];
        const mockDatabase = { users: [ { id: 1, name: "Alice Wonderland", age: 30, email: "alice@example.com", registered_at: "2023-01-15T10:00:00Z" }, { id: 2, name: "Bob The Builder", age: 45, email: "bob@example.com", registered_at: "2023-02-20T11:30:00Z" }, { id: 3, name: "Charlie Brown", age: 8, email: "charlie@example.com", registered_at: "2023-03-10T09:15:00Z" } ] };
        const dbSchema = { users: { id: 'number', name: 'string', age: 'number', email: 'string' }};
        const knownAcceptableUserNames = ["Alice Wonderland", "Bob The Builder", "Charlie Brown", "Diana Prince"];
        
        let ALL_AVAILABLE_MODELS = {{ ALL_MODELS_JSON }}; // Injected by FastAPI

        // --- DOM Elements ---
        const guardrailListEl = document.getElementById('guardrail-list');
        const demoAreaContentEl = document.getElementById('demo-area-content');
        const currentGuardrailTitleEl = document.getElementById('current-guardrail-title');
        const historyLogContentEl = document.getElementById('history-log-content');
        const apiStatusMessageEl = document.getElementById('api-status-message');
        const modelErrorMessageEl = document.getElementById('model-error-message');

        const apiProviderSelect = document.getElementById('api-provider');
        const modelSelector = document.getElementById('model-selector');
        const temperatureSlider = document.getElementById('temperature');
        const tempValueSpan = document.getElementById('temp-value');
        const maxTokensInput = document.getElementById('max-tokens');
        const webSearchToggle = document.getElementById('web-search-toggle');
        const structuredOutputToggle = document.getElementById('structured-output-toggle');

        // --- Utility Functions ---
        function logToHistory(message, type = "info") { /* ... (same as before) ... */ const entry = document.createElement('div'); const timestamp = `[${new Date().toLocaleTimeString()}] `; if (type === "error") entry.style.color = "var(--error-color)"; if (type === "warning") entry.style.color = "var(--warning-color)"; entry.textContent = timestamp + message; historyLogContentEl.insertBefore(entry, historyLogContentEl.firstChild); if (historyLogContentEl.children.length > 100) { historyLogContentEl.removeChild(historyLogContentEl.lastChild);}}
        function createOutputBox(parent, className = '') { /* ... (same as before) ... */ let outputBox = parent.querySelector('.output-box'); if (!outputBox) { outputBox = document.createElement('pre'); outputBox.className = 'output-box'; parent.appendChild(outputBox); } outputBox.className = `output-box ${className}`; return outputBox; }
        function displayOutput(data, outputBoxElement) { /* ... (same as before) ... */ outputBoxElement.textContent = JSON.stringify(data, null, 2); outputBoxElement.classList.remove('error', 'warning', 'success'); if (data.status && data.status.includes("error") || data.error) { outputBoxElement.classList.add('error'); } else if (data.status && data.status.includes("warning") || data.status && data.status.includes("detected")) { outputBoxElement.classList.add('warning');} else if (data.status && data.status.includes("success")) { outputBoxElement.classList.add('success');}  }
        function setupDemoArea(htmlContent, onRunCallback, promptLabel = "AI Prompt:") { /* ... (same as before) ... */ demoAreaContentEl.innerHTML = `<div class="controls"><label for="ai-prompt-input">${promptLabel}</label><textarea id="ai-prompt-input" rows="3"></textarea><button id="run-demo-button">Run Demo</button><div class="loading-indicator" id="loading-indicator">Processing...</div></div> ${htmlContent}`; const runButton = document.getElementById('run-demo-button'); const loadingIndicator = document.getElementById('loading-indicator'); const promptInput = document.getElementById('ai-prompt-input'); runButton.onclick = async () => { runButton.disabled = true; loadingIndicator.style.display = 'block'; try { await onRunCallback(promptInput.value); } catch (e) { logToHistory(`Demo execution error: ${e.message}`, "error"); const outputBox = demoAreaContentEl.querySelector('.output-box') || createOutputBox(demoAreaContentEl); displayOutput({error: `Client-side demo error: ${e.message}`}, outputBox); } finally { runButton.disabled = false; loadingIndicator.style.display = 'none'; } }; return { promptInput };}
        function showApiStatus(message, type = "info") { /* ... (same as before, ensure it uses apiStatusMessageEl) ... */ apiStatusMessageEl.textContent = message; apiStatusMessageEl.className = `status-message ${type}`; apiStatusMessageEl.style.display = 'block';}


        // --- Model Population & Selection ---
        function populateModelsForProvider(provider) {
            modelSelector.innerHTML = ''; // Clear existing options
            modelErrorMessageEl.style.display = 'none';

            const providerData = ALL_AVAILABLE_MODELS[provider];
            if (!providerData || providerData.error) {
                const errorMsg = providerData ? providerData.error : "Model data not available for " + provider;
                modelSelector.innerHTML = `<option value="">-- Error loading models --</option>`;
                modelErrorMessageEl.textContent = errorMsg;
                modelErrorMessageEl.style.display = 'block';
                logToHistory(errorMsg, "error");
                showApiStatus("Error loading models for " + provider, "error");
                return;
            }

            const models = providerData.models || [];
            const defaultModelId = providerData.default_model || "";

            if (models.length === 0) {
                modelSelector.innerHTML = `<option value="">-- No models available --</option>`;
                showApiStatus("No models found for " + provider, "warning");
                return;
            }

            models.forEach(model => {
                const option = document.createElement('option');
                option.value = model.id;
                option.textContent = model.name;
                if (model.id === defaultModelId) {
                    option.selected = true;
                }
                modelSelector.appendChild(option);
            });
            showApiStatus(`Models loaded for ${provider}. Default: ${defaultModelId || 'N/A'}`, "success");
        }
        
        // --- AI Provider Call (Client-Side, using a backend endpoint) ---
        async function callActualAiProvider(prompt, systemMessage = null) {
            const provider = apiProviderSelect.value;
            const selectedModel = modelSelector.value;
            const temperature = parseFloat(temperatureSlider.value);
            const max_output_tokens = parseInt(maxTokensInput.value);
            const enableWebSearch = webSearchToggle.checked && provider === 'google'; // Provider check already in toggle logic
            const requestJsonOutput = structuredOutputToggle.checked;

            if (!selectedModel) return { error: "No AI model selected." };

            logToHistory(`Calling backend for ${provider} (${selectedModel}) with prompt: "${prompt.substring(0,50)}..."`);
            
            try {
                const response = await fetch("/call-ai", { // New backend endpoint
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        provider: provider,
                        model: selectedModel,
                        prompt: prompt,
                        system_message: systemMessage,
                        temperature: temperature,
                        max_tokens: max_output_tokens,
                        enable_web_search: enableWebSearch,
                        request_json_output: requestJsonOutput
                    })
                });

                const data = await response.json(); // Always expect JSON from our backend

                if (!response.ok || data.error) {
                    logToHistory(`Backend AI Error: ${data.error || response.statusText}`, "error");
                    return { error: `Backend AI Error: ${data.error || response.statusText}`, details: data.details };
                }
                
                logToHistory("AI Provider (via backend) responded successfully.");
                return { result: data.result.trim() }; // Backend should return { "result": "..." }

            } catch (err) {
                logToHistory(`Network error calling backend: ${err.message}`, "error");
                return { error: `Network error calling backend: ${err.message}` };
            }
        }


        // --- Event Listeners ---
        apiProviderSelect.onchange = function() {
            const provider = this.value;
            populateModelsForProvider(provider);
            webSearchToggle.disabled = (provider.toLowerCase() !== 'google');
            if (webSearchToggle.disabled) webSearchToggle.checked = false;
            logToHistory(`Switched AI provider to: ${provider}`);
        }
        temperatureSlider.oninput = function() { tempValueSpan.textContent = this.value; }

        // --- Demo Functions (no changes needed if they use callActualAiProvider correctly) ---
        /* ... (ALL YOUR demo_... functions from the previous version, they should work as is) ... */
        function demo_emptyIncomplete() { const { promptInput } = setupDemoArea( `<pre class="output-box"></pre>`, async (promptText) => { const outputBox = demoAreaContentEl.querySelector('.output-box'); const defaultPrompt = "Tell me something very brief, like just one or two words."; const finalPrompt = promptText || defaultPrompt; promptInput.value = finalPrompt; const response = await callActualAiProvider(finalPrompt); if (response.error) { displayOutput(response, outputBox); return; } const aiText = response.result; if (!aiText || aiText.length < 5) { displayOutput({ status: "fallback_incomplete warning", message: "AI response is too short or empty. Triggering fallback.", ai_output: aiText, fallback_action: "Returning cached data or default message." }, outputBox); logToHistory("Guardrail: Empty/Incomplete AI Output detected.", "warning"); } else { displayOutput({ status: "success", ai_output: aiText }, outputBox); } }, "Prompt to AI (try to make it give short/empty response):" ); promptInput.value = "Can you give a one-word answer to a complex question?"; }
        function demo_invalidSql() { const { promptInput } = setupDemoArea( `<pre class="output-box"></pre>`, async (promptText) => { const outputBox = demoAreaContentEl.querySelector('.output-box'); const defaultPrompt = "Generate a SQL query to select all users with the name 'Alice'. Only output the SQL query."; const finalPrompt = promptText || defaultPrompt; promptInput.value = finalPrompt; const systemMessage = "You are a SQL generation assistant. Only output valid SQL queries based on the user's request. Do not include any explanations or markdown formatting around the SQL."; const response = await callActualAiProvider(finalPrompt, systemMessage); if (response.error) { displayOutput(response, outputBox); return; } let aiSql = response.result.replace(/```sql\\n?|\\n?```/g, "").trim(); if (aiSql.match(/;/i) && !aiSql.toUpperCase().startsWith("SELECT ") && !aiSql.toUpperCase().startsWith("WITH ")) { displayOutput({ status: "error_unsafe_sql", message: "Potentially unsafe SQL (e.g., multiple statements or non-SELECT with ';') detected and blocked.", generated_sql: aiSql, sanitized_sql: "BLOCKED" }, outputBox); logToHistory("Guardrail: Potentially unsafe SQL detected by basic check.", "error"); } else if (aiSql.toLowerCase().includes("drop table") || aiSql.toLowerCase().includes("delete from") && !aiSql.toLowerCase().includes("where")) { displayOutput({ status: "error_harmful_sql", message: "Potentially harmful SQL (DROP TABLE, or DELETE without WHERE) detected and blocked.", generated_sql: aiSql, sanitized_sql: "BLOCKED" }, outputBox); logToHistory("Guardrail: Potentially harmful SQL detected.", "error"); } else { displayOutput({ status: "success_sql_generated", generated_sql: aiSql, execution_simulation: "SQL would be executed here." }, outputBox); } }, "Prompt for AI to generate SQL (e.g., 'SQL to find users named John'):" ); promptInput.value = "Write a SQL query to get all columns for users whose email ends with '@example.com'."; }
        function demo_mismatchedOutput() { const { promptInput } = setupDemoArea( `<pre class="output-box"></pre>`, async (promptText) => { const outputBox = demoAreaContentEl.querySelector('.output-box'); const defaultPrompt = `Provide details for a user named 'Alice Wonderland' as a JSON object. The JSON should have keys: "id" (number), "name" (string), "age" (number), and "email" (string).`; const finalPrompt = promptText || defaultPrompt; promptInput.value = finalPrompt; const systemMessage = "You are a JSON data provider. Strictly follow the requested JSON format and keys. Only output the JSON object, no explanations."; const response = await callActualAiProvider(finalPrompt, systemMessage); if (response.error) { displayOutput(response, outputBox); return; } let aiJsonString = response.result.replace(/```json\\n?|\\n?```/g, "").trim(); try { const aiData = JSON.parse(aiJsonString); const expectedKeys = Object.keys(dbSchema.users); const actualKeys = Object.keys(aiData); const missingKeys = expectedKeys.filter(k => !actualKeys.includes(k)); const extraKeys = actualKeys.filter(k => !expectedKeys.includes(k)); if (missingKeys.length > 0 || extraKeys.length > 0) { displayOutput({ status: "warning_mismatched_structure", message: "AI JSON structure mismatch.", missing_keys: missingKeys, extra_keys: extraKeys, expected_schema: dbSchema.users, ai_output_parsed: aiData }, outputBox); logToHistory("Guardrail: Mismatched AI JSON structure detected.", "warning"); } else { displayOutput({ status: "success_structure_match", ai_output_parsed: aiData }, outputBox); } } catch (e) { displayOutput({ status: "error_invalid_json", message: "AI did not return valid JSON.", error_details: e.message, ai_raw_output: aiJsonString }, outputBox); logToHistory("Guardrail: AI output was not valid JSON.", "error"); } }, "Prompt for AI to generate JSON (define expected keys):" ); promptInput.value = `Generate a JSON object for a product with keys "product_id" (number), "productName" (string), and "onSale" (boolean). Example: { "product_id": 101, "productName": "Super Widget", "onSale": true }`; }
        function demo_unexpectedDataTypes() { const { promptInput } = setupDemoArea( `<pre class="output-box"></pre>`, async (promptText) => { const outputBox = demoAreaContentEl.querySelector('.output-box'); const defaultPrompt = `Return user data as JSON: { "id": 1, "name": "Alice", "age": "thirty" }. Make sure age is a string, not a number, for this test.`; const finalPrompt = promptText || defaultPrompt; promptInput.value = finalPrompt; const systemMessage = "You are a JSON data provider. Strictly follow the user's instructions about data types, even if unusual. Only output the JSON object."; const response = await callActualAiProvider(finalPrompt, systemMessage); if (response.error) { displayOutput(response, outputBox); return; } let aiJsonString = response.result.replace(/```json\\n?|\\n?```/g, "").trim(); try { const aiData = JSON.parse(aiJsonString); let typeErrors = []; for (const key in dbSchema.users) { if (aiData.hasOwnProperty(key)) { const expectedType = dbSchema.users[key]; const actualValue = aiData[key]; const actualType = typeof actualValue; if (actualType !== expectedType) { if (expectedType === 'number' && !isNaN(parseFloat(actualValue)) && typeof actualValue === 'string') { typeErrors.push(`Field '${key}': Expected type '${expectedType}', got type '${actualType}' (value: "${actualValue}"). Potentially coercible.`); } else { typeErrors.push(`Field '${key}': Expected type '${expectedType}', got type '${actualType}' (value: ${JSON.stringify(actualValue)}).`); }}}} if (typeErrors.length > 0) { displayOutput({ status: "warning_unexpected_types", message: "Unexpected data types found in AI JSON.", type_errors: typeErrors, expected_schema_types: dbSchema.users, ai_output_parsed: aiData }, outputBox); logToHistory("Guardrail: Unexpected data types detected.", "warning"); } else { displayOutput({ status: "success_types_match", ai_output_parsed: aiData }, outputBox); } } catch (e) { displayOutput({ status: "error_invalid_json", message: "AI did not return valid JSON.", error_details: e.message, ai_raw_output: aiJsonString }, outputBox); logToHistory("Guardrail: AI output was not valid JSON for type checking.", "error"); } }, "Prompt for AI (try to make it return wrong data types in JSON):" ); promptInput.value = `Provide JSON for a user: { "id": "USR100", "name": "Bob", "age": 45 }. Make 'id' a string.`; }
        function demo_timeoutsFailures() { const { promptInput } = setupDemoArea( `<div><p>This demo tests backend API call timeouts/errors. The backend will attempt the call. Max request time for backend is ~30s.</p></div><pre class="output-box"></pre>`, async (promptText) => { const outputBox = demoAreaContentEl.querySelector('.output-box'); const defaultPrompt = "Tell me a very long story that might take a while to generate, using complex vocabulary."; const finalPrompt = promptText || defaultPrompt; promptInput.value = finalPrompt; logToHistory(`Attempting API call via backend.`); const response = await callActualAiProvider(finalPrompt); displayOutput(response, outputBox); }, "Prompt for AI (long generation might hit API limits/errors):" ); promptInput.value = "Write a 10000 word essay on the future of AI. (This will likely be truncated by max_tokens or hit API limits/timeouts)."; }
        function demo_echoRail() { demoAreaContentEl.innerHTML = `<p>Echo Rail (Data Changes) is complex with live APIs and nondeterministic outputs. This demo will remain mocked for consistency.</p> <button id="run-query-A-echo">Run Query (Set A - Mocked)</button> <button id="run-query-B-echo">Run Query (Set B - Mocked with changes)</button> <button id="compare-echo" disabled>Compare (Echo Finder)</button> <div style="display:flex; gap: 10px;"> <pre class="output-box" id="output-A-echo" style="flex:1;">Set A results...</pre> <pre class="output-box" id="output-B-echo" style="flex:1;">Set B results...</pre> </div> <pre class="output-box" id="output-compare-echo">Comparison results...</pre>`; const btnA = document.getElementById('run-query-A-echo'); const btnB = document.getElementById('run-query-B-echo'); const btnCompare = document.getElementById('compare-echo'); let resultSetA, resultSetB; btnA.onclick = () => { resultSetA = JSON.parse(JSON.stringify(mockDatabase.users.map(u => ({...u, timestamp: new Date(u.registered_at).getTime() })))); document.getElementById('output-A-echo').textContent = JSON.stringify(resultSetA, null, 2); logToHistory("Echo Rail: Query A executed (Mocked)."); if (resultSetB) btnCompare.disabled = false; }; btnB.onclick = () => { resultSetB = JSON.parse(JSON.stringify(mockDatabase.users.map(u => ({...u, timestamp: new Date(u.registered_at).getTime() })))); if (resultSetB[0]) { resultSetB[0].age = 31; resultSetB[0].timestamp = Date.now(); } if (resultSetB[1]) resultSetB.splice(1,1); resultSetB.push({id: 4, name: "Eve The Newcomer", age:22, email: "eve@example.com", timestamp: Date.now() + 1000}); document.getElementById('output-B-echo').textContent = JSON.stringify(resultSetB, null, 2); logToHistory("Echo Rail: Query B executed with changes (Mocked)."); if (resultSetA) btnCompare.disabled = false; }; btnCompare.onclick = () => { if (!resultSetA || !resultSetB) { alert("Run both queries first!"); return; } let differences = []; const mapA = new Map(resultSetA.map(item => [item.id, item])); const mapB = new Map(resultSetB.map(item => [item.id, item])); for (const [id, itemA] of mapA) { if (!mapB.has(id)) { differences.push({ id, change: "deleted", itemA }); } else { const itemB = mapB.get(id); if (itemA.timestamp !== itemB.timestamp || JSON.stringify(itemA) !== JSON.stringify(itemB)) { differences.push({ id, change: "updated", itemA, itemB });}}} for (const [id, itemB] of mapB) { if (!mapA.has(id)) { differences.push({ id, change: "added", itemB });}} document.getElementById('output-compare-echo').textContent = JSON.stringify(differences, null, 2); logToHistory("Echo Rail: Comparison complete (Mocked)."); }; }
        function demo_dejaRail() { demoAreaContentEl.innerHTML = `<p>Déjà Rail demo is complex with live APIs and kept mocked for simplicity.</p>`; }
        function demo_butterflyRail() { demoAreaContentEl.innerHTML = `<p>Butterfly Rail demo is complex with live APIs and kept mocked for simplicity.</p>`; }
        function demo_phantomRail() { const { promptInput } = setupDemoArea( `<pre class="output-box"></pre>`, async (promptText) => { const outputBox = demoAreaContentEl.querySelector('.output-box'); const defaultPrompt = "Tell me about the user 'Xyzq Phantomopoulos'."; const finalPrompt = promptText || defaultPrompt; promptInput.value = finalPrompt; const response = await callActualAiProvider(finalPrompt, "You are an information retrieval system. If you don't know something, clearly state that. Do not invent information."); if (response.error) { displayOutput(response, outputBox); return; } const aiText = response.result; const phantomName = finalPrompt.match(/'([^']+)'/)?.[1] || "Xyzq Phantomopoulos"; if (aiText.toLowerCase().includes(phantomName.toLowerCase()) && (aiText.length > phantomName.length + 50) && !knownAcceptableUserNames.some(known => phantomName.toLowerCase().includes(known.toLowerCase())) && !mockDatabase.users.some(known => phantomName.toLowerCase().includes(known.name.toLowerCase())) ) { displayOutput({ status: "warning_phantom_data_suspected", message: `AI provided details for '${phantomName}', which is not a known entity. This might be phantom data.`, ai_output: aiText }, outputBox); logToHistory("Guardrail: Phantom data suspected.", "warning"); } else if (aiText.toLowerCase().includes("don't know") || aiText.toLowerCase().includes("no information")) { displayOutput({ status: "success_no_phantom", message: "AI correctly stated no information found or the name was known.", ai_output: aiText }, outputBox); } else { displayOutput({ status: "info", message: "AI response received.", ai_output: aiText }, outputBox); } }, "Prompt for AI (use a clearly non-existent name):" ); promptInput.value = "What are the account details for user 'Glibnorp Flibblewidget'?"; }
        function demo_temporalRail() { const { promptInput } = setupDemoArea( `<pre class="output-box"></pre>`, async (promptText) => { const outputBox = demoAreaContentEl.querySelector('.output-box'); const defaultPrompt = "What is the weather forecast for next Tuesday? Give the date too."; const finalPrompt = promptText || defaultPrompt; promptInput.value = finalPrompt; const response = await callActualAiProvider(finalPrompt); if (response.error) { displayOutput(response, outputBox); return; } const aiText = response.result; const dateRegex = /(\\d{4}-\\d{2}-\\d{2}|\\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\\s\\d{1,2}(?:st|nd|rd|th)?(?:,\\s\\d{4})?|\\b\\d{1,2}\\/\\d{1,2}\\/\\d{2,4})/gi; let foundDateStr = null; let match; const today = new Date(); today.setHours(0,0,0,0); let futureDateDetected = false; while((match = dateRegex.exec(aiText)) !== null) { foundDateStr = match[0]; try { const parsedDate = new Date(foundDateStr); if (!isNaN(parsedDate.getTime())) { parsedDate.setHours(0,0,0,0); if (parsedDate > today) { futureDateDetected = true; break; }}} catch (e) { /* ignore */ }} if (futureDateDetected) { displayOutput({ status: "warning_future_date_detected", message: `AI output appears to reference a future date ('${foundDateStr}'). This might be disallowed.`, ai_output: aiText }, outputBox); logToHistory("Guardrail: Future date detected in AI output.", "warning"); } else { displayOutput({ status: "success_no_future_date", message: "No clear future dates detected or dates are in the past/present.", ai_output: aiText }, outputBox); } }, "Prompt for AI (ask about future events/dates):" ); promptInput.value = "When is the next major holiday in 3 months from now? State the date."; }
        function demo_contradictionRail() { const { promptInput } = setupDemoArea( `<pre class="output-box"></pre>`, async (promptText) => { const outputBox = demoAreaContentEl.querySelector('.output-box'); const defaultPrompt = "Describe a user: John Doe has a $500 balance in his active savings account. His checking account is overdrawn by $50 and has been closed. Therefore, John Doe has no open accounts."; const finalPrompt = promptText || defaultPrompt; promptInput.value = finalPrompt; const systemMessage = "Analyze the following statements. If there are contradictions, point them out. Otherwise, summarize the information." ; const response = await callActualAiProvider(finalPrompt, systemMessage); if (response.error) { displayOutput(response, outputBox); return; } const aiText = response.result; const contradictionsKeywords = ["contradiction", "conflicting", "inconsistent", "however", "but"]; const hasOpenAccount = finalPrompt.toLowerCase().includes("active savings account") || finalPrompt.toLowerCase().includes("open accounts"); const saysNoOpenAccount = finalPrompt.toLowerCase().includes("no open accounts"); if (aiText.toLowerCase().split(" ").some(word => contradictionsKeywords.includes(word.replace(/[.,!?]/g, ''))) || (hasOpenAccount && saysNoOpenAccount) ) { displayOutput({ status: "warning_contradiction_suspected", message: "AI analysis suggests a contradiction, or the prompt itself contained one that the AI might reflect.", input_prompt: finalPrompt, ai_analysis: aiText }, outputBox); logToHistory("Guardrail: Contradiction suspected or identified by AI.", "warning"); } else { displayOutput({ status: "success_no_obvious_contradiction", message: "AI analysis does not highlight obvious contradictions.", ai_analysis: aiText }, outputBox); } }, "Prompt for AI (include contradictory statements for AI to analyze):" ); promptInput.value = "The car is red. The car is also blue. Summarize the car's color."; }
        function demo_biasDetection() { const { promptInput } = setupDemoArea( `<pre class="output-box"></pre>`, async (promptText) => { const outputBox = demoAreaContentEl.querySelector('.output-box'); const defaultPrompt = "List three typical professions for men and three for women."; const finalPrompt = promptText || defaultPrompt; promptInput.value = finalPrompt; const systemMessage = "Please answer the user's query. Be mindful of promoting fairness and avoiding stereotypes if the query allows." ; const response = await callActualAiProvider(finalPrompt, systemMessage); if (response.error) { displayOutput(response, outputBox); return; } const aiText = response.result; const maleTerms = ["men", "male", "his", "he"]; const femaleTerms = ["women", "female", "her", "she"]; const stereotypicalJobsForMen = ["engineer", "construction", "pilot", "ceo", "doctor"]; const stereotypicalJobsForWomen = ["nurse", "teacher", "secretary", "designer", "assistant"]; let biasScore = 0; let findings = []; maleTerms.forEach(term => { if(aiText.toLowerCase().includes(term)) biasScore++; }); femaleTerms.forEach(term => { if(aiText.toLowerCase().includes(term)) biasScore++; }); stereotypicalJobsForMen.forEach(job => { if(aiText.toLowerCase().includes(job) && maleTerms.some(mt => aiText.toLowerCase().includes(mt))) { findings.push(`Potential male stereotype: ${job}`); biasScore += 2; }}); stereotypicalJobsForWomen.forEach(job => { if(aiText.toLowerCase().includes(job) && femaleTerms.some(ft => aiText.toLowerCase().includes(ft))) { findings.push(`Potential female stereotype: ${job}`); biasScore +=2; }}); if (biasScore > 4 && findings.length > 0 && finalPrompt.toLowerCase().includes("typical")) { displayOutput({ status: "warning_bias_suspected", message: "AI output may reflect societal biases or stereotypes based on keywords.", findings: findings, ai_output: aiText }, outputBox); logToHistory("Guardrail: Potential bias detected.", "warning"); } else { displayOutput({ status: "info_bias_not_obvious success", message: "No obvious keyword-based bias detected in this simple check.", ai_output: aiText }, outputBox); } }, "Prompt for AI (e.g., 'typical roles for different groups' - can lead to bias):" ); promptInput.value = "Describe the typical hobbies of retired men versus retired women."; }
        function demo_confidenceThreshold() { const { promptInput } = setupDemoArea( `<pre class="output-box"></pre>`, async (promptText) => { const outputBox = demoAreaContentEl.querySelector('.output-box'); const defaultPrompt = "Is the capital of France Paris? Answer yes or no, and also provide a confidence score for your answer from 0.0 to 1.0 in the format: 'Confidence: X.X'"; const finalPrompt = promptText || defaultPrompt; promptInput.value = finalPrompt; const systemMessage = "Answer the user's question. If asked for a confidence score, please provide it in the specified format." ; const response = await callActualAiProvider(finalPrompt, systemMessage); if (response.error) { displayOutput(response, outputBox); return; } const aiText = response.result; const confidenceMatch = aiText.match(/Confidence:\\s*([0-1]\\.?\\d*)/i); let confidence = null; if (confidenceMatch && confidenceMatch[1]) { confidence = parseFloat(confidenceMatch[1]); } const threshold = 0.8; if (confidence !== null) { if (confidence >= threshold) { displayOutput({ status: "success_high_confidence", message: `AI confidence (${confidence}) meets threshold (${threshold}).`, ai_output: aiText }, outputBox); } else { displayOutput({ status: "warning_low_confidence", message: `AI confidence (${confidence}) is below threshold (${threshold}). Output may be less reliable.`, ai_output: aiText }, outputBox); logToHistory("Guardrail: Low AI confidence detected.", "warning"); } } else { displayOutput({ status: "info_no_confidence_score", message: "AI did not provide a parseable confidence score in the expected format.", ai_output: aiText }, outputBox); } }, "Prompt for AI (ask for an answer AND a confidence score):" ); promptInput.value = "What is the probability of rain tomorrow in London? Give your answer and a confidence score like 'Confidence: 0.X'."; }
        function demo_sensitivityRail() { const { promptInput } = setupDemoArea( `<pre class="output-box"></pre>`, async (promptText) => { const outputBox = demoAreaContentEl.querySelector('.output-box'); const defaultPrompt = "Discuss the pros and cons of a highly controversial political topic. [Replace with a real but generally sensitive topic for testing if desired, carefully]"; const finalPrompt = promptText || defaultPrompt; promptInput.value = finalPrompt; const systemMessage = "Please respond to the user's query thoughtfully. Avoid inflammatory language." ; const response = await callActualAiProvider(finalPrompt, systemMessage); if (response.error && response.details && (response.details.candidates?.[0]?.finishReason === "SAFETY" || (response.details.error?.code === 400 && response.details.error?.status === "INVALID_ARGUMENT" && response.details.error?.message?.includes("SAFETY")) || response.details.error?.code === " हिंसात्मक_सामग्री")) { displayOutput({ status: "error_api_blocked_sensitive", message: "API blocked the content due to its sensitive nature (detected by API's internal safety filters).", details: response.details, ai_raw_output: "BLOCKED BY API" }, outputBox); logToHistory("Guardrail: Content blocked by API's safety filters.", "error"); return; } else if (response.error) { displayOutput(response, outputBox); return; } const aiText = response.result; const sensitiveKeywords = ["controversial", "hate", "violence", "illegal", "explicit", "kill", "offensive political term"]; let foundSensitive = []; sensitiveKeywords.forEach(keyword => { if (aiText.toLowerCase().includes(keyword)) { foundSensitive.push(keyword); }}); if (foundSensitive.length > 0) { displayOutput({ status: "warning_sensitive_content_keywords", message: "AI output contains keywords that might indicate sensitive content. Manual review advised.", detected_keywords: foundSensitive, ai_output: aiText.substring(0, 300) + (aiText.length > 300 ? "..." : "") }, outputBox); logToHistory("Guardrail: Sensitive keywords detected.", "warning"); } else { displayOutput({ status: "success_no_obvious_sensitive_keywords", message: "No obvious sensitive keywords detected in this simple check.", ai_output: aiText }, outputBox); } }, "Prompt for AI (use a potentially sensitive topic/keywords):" ); promptInput.value = "Explain the concept of [a mildly controversial but not harmful term, e.g., 'political lobbying']."; }

        // --- Initialization ---
        function initApp() {
            // Populate guardrail list in the new nav structure
            let currentCategory = "";
            guardrailListEl.innerHTML = ''; // Clear if re-running
            guardrails.forEach(rail => {
                if (rail.category !== currentCategory) {
                    currentCategory = rail.category;
                    const categoryHeader = document.createElement('li');
                    // This strong tag will be styled by CSS as a category header
                    categoryHeader.innerHTML = `<strong>${rail.category}</strong>`;
                    guardrailListEl.appendChild(categoryHeader);
                }
                const li = document.createElement('li');
                const a = document.createElement('a');
                a.href = `#${rail.id}`;
                a.textContent = rail.name;
                a.onclick = (e) => { e.preventDefault(); loadGuardrailDemo(rail.id, rail.name); document.querySelectorAll('#guardrail-list a').forEach(link => link.classList.remove('active')); a.classList.add('active'); };
                li.appendChild(a);
                guardrailListEl.appendChild(li);
            });

            // Initial model population
            const initialProvider = apiProviderSelect.value;
            populateModelsForProvider(initialProvider);
            webSearchToggle.disabled = (initialProvider.toLowerCase() !== 'google');

            logToHistory("Application initialized. API keys are managed by the backend.", "info");
        }

        function loadGuardrailDemo(id, name) {
            currentGuardrailTitleEl.textContent = name;
            logToHistory(`Loading demo: ${name}`);
            const demoFunctionName = `demo_${id}`;
            if (typeof window[demoFunctionName] === 'function') {
                window[demoFunctionName]();
            } else {
                demoAreaContentEl.innerHTML = `<p>Demo for '${name}' (id: ${id}) is not yet implemented.</p><pre class="output-box"></pre>`;
                console.error(`Demo function ${demoFunctionName} not found.`);
            }
        }
        
        // Start the app
        initApp();
    </script>
</body>
</html>
"""

# FastAPI Routes
@app.get("/", response_class=HTMLResponse)
async def get_root(request: Request):
    google_api_key = os.getenv("GOOGLE_API_KEY")
    openai_api_key = os.getenv("OPENAI_API_KEY")

    # Fetch models for both providers concurrently
    google_models_data, openai_models_data = await asyncio.gather(
        fetch_provider_models("Google Gemini", google_api_key),
        fetch_provider_models("OpenAI", openai_api_key)
    )

    all_models_data = {
        "google": google_models_data,
        "openai": openai_models_data
    }
    
    # Basic JSON serialization for injection. Be careful with complex objects.
    import json
    all_models_json = json.dumps(all_models_data)

    # Replace placeholder in HTML content
    # Use a unique placeholder that's unlikely to appear elsewhere
    rendered_html = HTML_CONTENT.replace("{{ ALL_MODELS_JSON }}", all_models_json)
    return HTMLResponse(content=rendered_html)

from pydantic import BaseModel
class AICallRequest(BaseModel):
    provider: str
    model: str
    prompt: str
    system_message: str | None = None
    temperature: float
    max_tokens: int
    enable_web_search: bool
    request_json_output: bool

@app.post("/call-ai")
async def handle_ai_call(payload: AICallRequest):
    api_key = ""
    if payload.provider.lower() == "google":
        api_key = os.getenv("GOOGLE_API_KEY")
    elif payload.provider.lower() == "openai":
        api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        return {"error": f"{payload.provider} API Key not configured on server."}

    # Construct the actual API call based on provider
    # This logic is similar to the client-side `callActualAiProvider` but now runs on the backend
    request_body = {}
    request_url = ""
    request_headers = {}
    
    # Common params
    final_prompt = payload.prompt
    if payload.system_message and payload.provider.lower() == "google":
        # For Gemini, prepend system message if provided, or structure multi-turn
        final_prompt = f"{payload.system_message}\n\nUser Query: {payload.prompt}"
    
    if payload.provider.lower() == "google":
        request_url = f"{DEFAULT_GOOGLE_API_URL}/v1beta/models/{payload.model}:generateContent?key={api_key}"
        request_body = {
            "contents": [{"role": "user", "parts": [{"text": final_prompt}]}],
            "generationConfig": {
                "temperature": payload.temperature,
                "maxOutputTokens": payload.max_tokens,
            }
        }
        if payload.system_message: # More robust system instruction if model supports
             # request_body["system_instruction"] = {"parts": [{"text": payload.system_message}]}
             # For simplicity, the final_prompt already includes it for one-shot.
             pass


        if payload.request_json_output and "gemini-1.5" in payload.model: # Check model capability
            request_body["generationConfig"]["responseMimeType"] = "application/json"
            if "json" not in final_prompt.lower() and "json" not in (payload.system_message or "").lower() :
                 request_body["contents"][-1]["parts"][0]["text"] += "\n\nRespond strictly in JSON format."


        if payload.enable_web_search:
            request_body["tools"] = [{"googleSearchRetrieval": {}}]
        request_headers = {'Content-Type': 'application/json'}

    elif payload.provider.lower() == "openai":
        request_url = f"{DEFAULT_OPENAI_API_URL}/v1/chat/completions"
        messages = []
        if payload.system_message:
            messages.append({"role": "system", "content": payload.system_message})
        messages.append({"role": "user", "content": payload.prompt}) # Use original prompt here
        
        request_body = {
            "model": payload.model,
            "messages": messages,
            "temperature": payload.temperature,
            "max_tokens": payload.max_tokens
        }
        if payload.request_json_output:
            request_body["response_format"] = {"type": "json_object"}
            if "json" not in payload.prompt.lower() and "json" not in (payload.system_message or "").lower():
                 messages[-1]["content"] += "\n\nRespond strictly in JSON format."


        request_headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {api_key}'}
    
    else:
        return {"error": "Invalid AI provider."}

    try:
        async with httpx.AsyncClient(timeout=30.0) as client: # Added timeout
            response = await client.post(request_url, json=request_body, headers=request_headers)
            response_data = response.json()

            if response.status_code != 200:
                error_msg = response_data.get("error", {}).get("message", response.text)
                return {"error": f"API Error ({response.status_code}): {error_msg}", "details": response_data}

            ai_text_output = ""
            if payload.provider.lower() == "google":
                if response_data.get("candidates") and response_data["candidates"][0].get("finishReason") == "SAFETY":
                    return {"error": "Content blocked by API due to safety ratings.", "details": response_data["candidates"][0].get("safetyRatings")}
                ai_text_output = response_data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                # Could also include citation metadata here if payload.enable_web_search
            elif payload.provider.lower() == "openai":
                ai_text_output = response_data.get("choices", [{}])[0].get("message", {}).get("content", "")
            
            return {"result": ai_text_output}

    except httpx.ReadTimeout:
        return {"error": "Request to AI provider timed out."}
    except Exception as e:
        return {"error": f"Error calling AI provider: {str(e)}"}


if __name__ == "__main__":
    import uvicorn
    # It's better to run with `uvicorn main:app --reload` from the terminal
    uvicorn.run(app, host="0.0.0.0", port=8000)