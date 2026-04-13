.PHONY: up down logs smoke smoke-osint selfcheck

up:
	docker compose up --build -d

down:
	docker compose down -v

logs:
	docker compose logs -f --tail=200

smoke:
	curl -s http://localhost:8080/health
	curl -s -X POST http://localhost:8080/v1/message \
		-H 'Content-Type: application/json' \
		-d '{"user_id":"lalo","text":"hola abel"}'

smoke-osint:
	curl -s -X POST http://localhost:8080/v1/osint/start \
		-H 'Content-Type: application/json' \
		-d '{"target":"jane.doe@example.com","target_type":"email","purpose":"due_diligence_vendor","consent_or_legal_basis":"contractual_due_diligence","mode":"RECOMMEND_ONLY"}'

selfcheck:
	python scripts/selfcheck.py
