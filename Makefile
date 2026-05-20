.PHONY: daily saas

daily:
	python3 scripts/new_daily.py $(if $(TOPIC),--topic "$(TOPIC)")

saas:
	python3 scripts/new_saas.py $(if $(TOPIC),--topic "$(TOPIC)")
