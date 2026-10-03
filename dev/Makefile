# Phase 0 development commands (P0-13).
# Proposed canonical bootstrap command, from the repository root:  make -C dev up

ENV_FILE    := ../.env
COMPOSE     := docker compose --env-file $(ENV_FILE) -f docker-compose.yml

.PHONY: up down reset logs ps psql env

## Create ../.env from the template if it does not exist yet (dummy dev values only).
env:
	@test -f $(ENV_FILE) || { cp ../.env.example $(ENV_FILE); echo "Created .env from .env.example"; }

## Start the stack and wait until every service is healthy.
up: env
	$(COMPOSE) up -d --wait

## Stop the stack, keeping the database volume.
down:
	$(COMPOSE) down

## Stop the stack and delete the database volume (re-runs db/init on next start).
reset:
	$(COMPOSE) down -v

logs:
	$(COMPOSE) logs -f

ps:
	$(COMPOSE) ps

## Open a psql shell in the database container.
psql:
	$(COMPOSE) exec db psql -U $$(grep '^POSTGRES_USER=' $(ENV_FILE) | cut -d= -f2) -d $$(grep '^POSTGRES_DB=' $(ENV_FILE) | cut -d= -f2)
