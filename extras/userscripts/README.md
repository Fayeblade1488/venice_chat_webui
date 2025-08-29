# Userscript: Open WebUI — Venice Panel

This userscript injects a floating panel into **Open WebUI** that lets you toggle Venice-specific parameters:
- Web search: off/auto/on
- Citations
- Include search results in stream
- Strip thinking
- Disable thinking
- Include Venice system prompt
- Optional model override

It intercepts outgoing **/v1/chat/completions** requests in the browser and adds the `venice_parameters` block (and model override if set).

## Install
1. Install **Tampermonkey** (or similar) in your browser.
2. Open the script file and click *Raw* to install, or copy its contents into a new userscript.
   - File: `extras/userscripts/openwebui-venice-panel.user.js`
3. Make sure your Open WebUI is reachable at one of the matched hosts, e.g. `http://llm-vps:3001` or `http://localhost:3001`.

## Use
- A small “Venice” button appears in the bottom-right of Open WebUI. Click it to open the panel.
- Settings are stored in `localStorage` per browser/device.
- Requests from Open WebUI to your LiteLLM proxy will include the chosen Venice flags automatically.
