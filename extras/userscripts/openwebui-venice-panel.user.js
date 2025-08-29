
// ==UserScript==
// @name         Open WebUI — Venice Panel
// @namespace    https://your.tailnet/
// @version      1.0.0
// @description  Adds a simple control panel inside Open WebUI to toggle Venice-specific parameters (web search, citations, thinking controls) and injects them into outgoing /v1/chat/completions requests via fetch interception.
// @author       You
// @match        http://localhost:3001/*
// @match        http://127.0.0.1:3001/*
// @match        http://*.tailscale/*
// @match        http://llm-vps:3001/*
// @grant        none
// ==/UserScript==

(function() {
  'use strict';

  const LS_KEY = "venice_panel_settings_v1";

  const defaults = {
    enable_web_search: "off",  // "off" | "auto" | "on"
    enable_web_citations: false,
    include_search_results_in_stream: false,
    strip_thinking_response: true,
    disable_thinking: true,
    include_venice_system_prompt: true,
    model_override: ""
  };

  let state = loadState();

  function loadState() {
    try {
      const raw = localStorage.getItem(LS_KEY);
      if (!raw) return { ...defaults };
      const parsed = JSON.parse(raw);
      return { ...defaults, ...parsed };
    } catch (e) {
      return { ...defaults };
    }
  }

  function saveState() {
    localStorage.setItem(LS_KEY, JSON.stringify(state));
  }

  function createPanel() {
    const wrap = document.createElement("div");
    wrap.id = "venice-panel";
    wrap.style.cssText = `
      position: fixed; right: 14px; bottom: 14px; z-index: 99999;
      font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
      background: rgba(20,20,24,0.95); color: #eaeaea; border: 1px solid #333;
      border-radius: 12px; padding: 12px 14px; width: 320px; box-shadow: 0 8px 20px rgba(0,0,0,0.4);
    `;

    const header = document.createElement("div");
    header.style.cssText = "display:flex; align-items:center; justify-content:space-between; margin-bottom: 8px;";
    header.innerHTML = `<div style="font-weight:600">Venice Panel</div>`;
    const closeBtn = document.createElement("button");
    closeBtn.textContent = "×";
    closeBtn.style.cssText = "background:transparent;color:#aaa;border:none;font-size:18px;cursor:pointer;";
    closeBtn.onclick = () => wrap.remove();
    header.appendChild(closeBtn);

    const row = (label, el) => {
      const r = document.createElement("div");
      r.style.cssText = "display:flex; align-items:center; justify-content:space-between; margin: 6px 0; gap:8px;";
      const l = document.createElement("label");
      l.textContent = label;
      l.style.cssText = "font-size: 13px; color:#ddd;";
      r.appendChild(l);
      r.appendChild(el);
      return r;
    };

    // enable_web_search
    const selSearch = document.createElement("select");
    ["off","auto","on"].forEach(opt => {
      const o = document.createElement("option");
      o.value = opt; o.textContent = opt;
      if (state.enable_web_search === opt) o.selected = true;
      selSearch.appendChild(o);
    });
    selSearch.onchange = () => { state.enable_web_search = selSearch.value; saveState(); };

    // citations
    const cbCite = document.createElement("input");
    cbCite.type = "checkbox"; cbCite.checked = !!state.enable_web_citations;
    cbCite.onchange = () => { state.enable_web_citations = cbCite.checked; saveState(); };

    // include search results in stream
    const cbIncl = document.createElement("input");
    cbIncl.type = "checkbox"; cbIncl.checked = !!state.include_search_results_in_stream;
    cbIncl.onchange = () => { state.include_search_results_in_stream = cbIncl.checked; saveState(); };

    // strip thinking
    const cbStrip = document.createElement("input");
    cbStrip.type = "checkbox"; cbStrip.checked = !!state.strip_thinking_response;
    cbStrip.onchange = () => { state.strip_thinking_response = cbStrip.checked; saveState(); };

    // disable thinking
    const cbDisable = document.createElement("input");
    cbDisable.type = "checkbox"; cbDisable.checked = !!state.disable_thinking;
    cbDisable.onchange = () => { state.disable_thinking = cbDisable.checked; saveState(); };

    // include system prompt
    const cbSys = document.createElement("input");
    cbSys.type = "checkbox"; cbSys.checked = !!state.include_venice_system_prompt;
    cbSys.onchange = () => { state.include_venice_system_prompt = cbSys.checked; saveState(); };

    // model override (optional)
    const modelInput = document.createElement("input");
    modelInput.type = "text";
    modelInput.placeholder = "Optional model override (e.g., qwen3-235b)";
    modelInput.value = state.model_override || "";
    modelInput.style.cssText = "width:180px; background:#111;color:#ddd;border:1px solid #333;border-radius:8px;padding:6px; font-size:12px;";
    modelInput.onchange = () => { state.model_override = modelInput.value.trim(); saveState(); };

    wrap.appendChild(header);
    wrap.appendChild(row("Web search", selSearch));
    wrap.appendChild(row("Citations", cbCite));
    wrap.appendChild(row("Search in stream", cbIncl));
    wrap.appendChild(row("Strip thinking", cbStrip));
    wrap.appendChild(row("Disable thinking", cbDisable));
    wrap.appendChild(row("Include Venice system prompt", cbSys));
    wrap.appendChild(row("Model override", modelInput));

    const hint = document.createElement("div");
    hint.style.cssText = "margin-top:8px; font-size:11px; color:#9aa; line-height:1.3;";
    hint.textContent = "Panel settings apply to outgoing /v1/chat/completions requests. Stored in localStorage.";
    wrap.appendChild(hint);

    document.body.appendChild(wrap);
  }

  function mountPanelWhenReady() {
    if (document.getElementById("venice-panel")) return;
    if (document.body) createPanel();
    else requestAnimationFrame(mountPanelWhenReady);
  }

  // Intercept fetch to inject venice_parameters in OpenAI-compatible chat requests.
  const origFetch = window.fetch;
  window.fetch = async function(input, init) {
    try {
      const url = (typeof input === "string") ? input : input.url;
      const isChat = url && /\/v1\/chat\/completions$/.test(url);
      if (isChat && init && init.method === "POST" && init.body) {
        let body;
        try { body = JSON.parse(init.body); } catch {}
        if (body && typeof body === "object") {
          body.venice_parameters = {
            enable_web_search: state.enable_web_search,
            enable_web_citations: !!state.enable_web_citations,
            include_search_results_in_stream: !!state.include_search_results_in_stream,
            strip_thinking_response: !!state.strip_thinking_response,
            disable_thinking: !!state.disable_thinking,
            include_venice_system_prompt: !!state.include_venice_system_prompt
          };
          if (state.model_override) {
            body.model = state.model_override;
          }
          init.body = JSON.stringify(body);
        }
      }
    } catch (e) {
      console.warn("[Venice Panel] fetch patch error:", e);
    }
    return origFetch.apply(this, arguments);
  };

  // Add a small launcher button in the page corner
  function addLauncher() {
    if (document.getElementById("venice-panel-launcher")) return;
    const btn = document.createElement("button");
    btn.id = "venice-panel-launcher";
    btn.textContent = "Venice";
    btn.style.cssText = `
      position: fixed; right: 14px; bottom: 14px; z-index: 99998;
      padding: 8px 10px; background:#1e232a; color:#eaeaea; border:1px solid #333;
      border-radius: 10px; cursor: pointer; font-size: 12px;
    `;
    btn.onclick = mountPanelWhenReady;
    document.body.appendChild(btn);
  }

  // Try mounting after page load and after SPA navigations
  const init = () => { addLauncher(); };
  window.addEventListener("load", init);
  const mo = new MutationObserver(() => addLauncher());
  mo.observe(document.documentElement, {childList: true, subtree: true});
})();
