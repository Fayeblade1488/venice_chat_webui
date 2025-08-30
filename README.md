<img width="1536" height="1024" alt="40078e2e20570734af54dc517e4b9be10d02e244799548c2e62768777bca4b79" src="https://github.com/user-attachments/assets/1b34fa79-fffb-478b-8a7f-4256d6bfd30e" />

# Open WebUI + LiteLLM (Venice) + Perplexica + SearXNG + Tailscale

**What this is**: a small, private stack. Open WebUI persists chats on-disk. LiteLLM proxies OpenAI-compatible requests to Venice at `https://api.venice.ai/api/v1`. Perplexica provides a Perplexity-like experience using SearXNG for retrieval. Tailscale gives private access from your devices.

## ⚠️ Security Warnings ⚠️

This project is designed to be run in a private, trusted environment. Do not expose this stack to the public internet without careful consideration and additional security measures.

Please read the [WARNING.md](WARNING.md) file for a detailed explanation of the security implications of the default configuration.

## Getting Started

### Prerequisites

- Docker
- Docker Compose
- Tailscale account (optional, but recommended for private access)

### Installation

1.  **Clone the repository:**

    ```bash
    git clone https://github.com/your-username/openwebui-venice-stack.git
    cd openwebui-venice-stack
    ```

2.  **Create the `.env` file:**

    Copy the `.env.example` file to `.env` and fill in the required API keys and tokens.

    ```bash
    cp .env.example .env
    ```

    You will need to set the following variables:

    - `VENICE_API_KEY`: Your Venice API key.
    - `LITELLM_MASTER_KEY`: A master key to protect your LiteLLM instance. You can generate a random string for this.
    - `TS_AUTHKEY`: Your Tailscale auth key (if you are using Tailscale).
    - `WEBUI_ADMIN_PASSWORD`: A strong password for the Open WebUI admin user.

3.  **Start the stack:**

    ```bash
    make up
    ```

    This will pull the latest Docker images and start all the services.

4.  **Check the health of the services:**

    ```bash
    make health
    ```

5.  **Test the stack:**

    ```bash
    make test-all
    ```

### URLs (over Tailscale or localhost)

- Open WebUI:  http://<tailnet-ip>:3001
- Perplexica:  http://<tailnet-ip>:3000
- SearXNG:     http://<tailnet-ip>:8085
- LiteLLM:     http://<tailnet-ip>:4000/v1

## Security

### Network Security

We strongly recommend using Tailscale to keep the entire stack private. By default, the services are only exposed on the host machine. If you need to access the services from other devices, Tailscale is the easiest and most secure way to do it.

### Application Security

- **Open WebUI Authentication**: The `WEBUI_AUTH` is enabled by default. You must set a strong admin password in the `.env` file.
- **LiteLLM Master Key**: The `LITELLM_MASTER_KEY` is required to access the LiteLLM service.
- **Policy Sidecar**: The `policy_sidecar` service provides an additional layer of security by redacting sensitive information from logs and enforcing policies. By default, the `POLICY_ALLOW_HEADER_OVERRIDES` is disabled.

## Configuration

The stack is configured through the `docker-compose.yml` file and the configuration files in the `configs` directory.

### Environment Variables

The following environment variables are used to configure the stack:

- `VENICE_API_KEY`: Your Venice API key.
- `LITELLM_MASTER_KEY`: A master key to protect your LiteLLM instance.
- `TS_AUTHKEY`: Your Tailscale auth key.
- `WEBUI_ADMIN_PASSWORD`: The password for the Open WebUI admin user.
- `POLICY_API_TOKEN`: An optional token to protect the `policy_sidecar` service.
- `POLICY_ALLOW_HEADER_OVERRIDES`: Set to `true` to allow clients to override policy settings via HTTP headers. Defaults to `false`.

### Configuration Files

- `configs/litellm_config.yaml`: Configures the LiteLLM service.
- `configs/perplexica.config.toml`: Configures the Perplexica service.
- `configs/searxng/settings.yml`: Configures the SearXNG service.

## Extending

- Add more profiles under `profiles/` (toggle Venice `venice_parameters` like web search, citations, thinking controls).
- Switch Perplexica’s `MODEL_NAME` in `configs/perplexica.config.toml` to any Venice model you prefer.
- If you need HTTPS/public, use the Caddy service and put access in front of everything.

## Extras (bells & whistles)

See `docker-compose.extras.yml` for monitoring, logs, Watchtower, and RAG API.
