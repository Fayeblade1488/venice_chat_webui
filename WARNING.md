# ⚠️ Security Warnings ⚠️

This project is designed to be run in a private, trusted environment. Do not expose this stack to the public internet without careful consideration and additional security measures.

## Default Configuration

The default configuration of this stack has the following security implications:

*   **`WEBUI_AUTH` is disabled by default in `openwebui`.** This means that anyone with access to the `openwebui` URL can access the service. For any production-like environment, you **must** enable authentication and set a strong admin password.

*   **`POLICY_ALLOW_HEADER_OVERRIDES` is enabled by default in the `policy_sidecar`.** This allows clients to override important policy settings, such as the model and web search capabilities. For any production-like environment, you should disable this feature.

*   **`searxng` has safe search disabled.** This means that search results may include adult content. While this is likely acceptable for a private stack, you should be aware of it.

## Recommendations

We strongly recommend that you:

1.  **Enable `WEBUI_AUTH`** in the `docker-compose.yml` file and set a strong admin password.
2.  **Disable `POLICY_ALLOW_HEADER_OVERRIDES`** in the `docker-compose.yml` file for production environments.
3.  **Use Tailscale** to keep the entire stack private.
4.  **Review the configuration** of all services before deploying in a production environment.
