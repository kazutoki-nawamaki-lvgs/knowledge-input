.PHONY: daily

daily:
	python3 scripts/new_daily.py $(if $(DATE),--date "$(DATE)") $(if $(TOPIC),--topic "$(TOPIC)")
