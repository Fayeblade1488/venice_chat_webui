SHELL := /bin/bash
COMPOSE := docker compose

.PHONY: up down logs ps restart test-all chat.research chat.strict chat.creative img.simple health

up:
	$(COMPOSE) pull && $(COMPOSE) up -d

down:
	$(COMPOSE) down

logs:
	$(COMPOSE) logs -f --tail=200

ps:
	$(COMPOSE) ps

restart:
	$(COMPOSE) restart

health:
	./scripts/healthcheck.sh http://localhost

# ---- Venice profiles via LiteLLM (OpenAI-compatible) ----
chat.research:
	curl -sS http://localhost:4000/v1/chat/completions \
	  -H "Authorization: Bearer $$LITELLM_MASTER_KEY" \
	  -H "Content-Type: application/json" \
	  --data-binary @profiles/venice-presets.research.json | jq .

chat.strict:
	curl -sS http://localhost:4000/v1/chat/completions \
	  -H "Authorization: Bearer $$LITELLM_MASTER_KEY" \
	  -H "Content-Type: application/json" \
	  --data-binary @profiles/venice-presets.strict.json | jq .

chat.creative:
	curl -sS http://localhost:4000/v1/chat/completions \
	  -H "Authorization: Bearer $$LITELLM_MASTER_KEY" \
	  -H "Content-Type: application/json" \
	  --data-binary @profiles/venice-presets.creative.json | jq .

# Venice OpenAI-compatible images endpoint (/v1/images/generations)
img.simple:
	curl -sS http://localhost:4000/v1/images/generations \
	  -H "Authorization: Bearer $$LITELLM_MASTER_KEY" \
	  -H "Content-Type: application/json" \
	  --data-binary @profiles/image.simple.json | jq .

test-all: chat.research chat.strict chat.creative img.simple
