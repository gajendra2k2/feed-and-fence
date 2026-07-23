# Prefer the project venv if it exists, then python3, then python — so every
# target works whether or not the user has `source .venv/bin/activate`d.
PYTHON ?= $(shell \
	if [ -x .venv/bin/python ]; then echo .venv/bin/python; \
	elif command -v python3 >/dev/null 2>&1; then echo python3; \
	else echo python; fi)

.PHONY: install up down logs producer producer-fraud server agent agent-replay audit approve test clean

install:
	$(PYTHON) -m pip install -e '.[dev]'

up:
	docker compose up -d
	@echo "Waiting for Kafka..."
	@until docker compose exec -T kafka /opt/kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 --list >/dev/null 2>&1; do sleep 1; done
	@echo "Kafka ready."

down:
	docker compose down -v --remove-orphans
	-docker rm -f governed-agents-kafka 2>/dev/null || true
	rm -rf state/

logs:
	docker compose logs -f kafka

producer:
	$(PYTHON) -m governed_agents.producer

producer-fraud:
	$(PYTHON) -m governed_agents.producer --scenario fraud

server:
	$(PYTHON) -m governed_agents.server.app

agent:
	$(PYTHON) -m governed_agents.client.agent

agent-replay:
	$(PYTHON) -m governed_agents.client.replay $(FILE)

audit:
	$(PYTHON) scripts/audit_viewer.py

approve:
	@if [ -z "$(ID)" ]; then echo "Usage: make approve ID=<approval_id>"; exit 1; fi
	$(PYTHON) scripts/approve.py $(ID)

test:
	$(PYTHON) -m pytest -q tests/

# Note: deliberately does NOT remove transcripts/ — that would nuke
# canonical.json which is shipped in-repo as the talk-day replay artifact.
clean:
	rm -rf state/ __pycache__ src/governed_agents/__pycache__ src/governed_agents/server/__pycache__ src/governed_agents/client/__pycache__
