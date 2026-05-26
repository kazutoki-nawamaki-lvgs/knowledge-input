.PHONY: daily liberal-arts saas design-system frontend-architecture product-ui-ux product-ui-ux-patterns accessibility

daily:
	python3 scripts/new_daily.py $(if $(TOPIC),--topic "$(TOPIC)")

liberal-arts: daily

saas:
	python3 scripts/new_saas.py $(if $(TOPIC),--topic "$(TOPIC)")

design-system:
	python3 scripts/new_track_note.py --track-dir design-system --topics topics/design_system_topics.csv $(if $(TOPIC),--topic "$(TOPIC)")

frontend-architecture:
	python3 scripts/new_track_note.py --track-dir frontend-architecture --topics topics/frontend_architecture_topics.csv $(if $(TOPIC),--topic "$(TOPIC)")

product-ui-ux:
	python3 scripts/new_track_note.py --track-dir product-ui-ux-patterns --topics topics/product_ui_ux_patterns_topics.csv $(if $(TOPIC),--topic "$(TOPIC)")

product-ui-ux-patterns: product-ui-ux

accessibility:
	python3 scripts/new_track_note.py --track-dir accessibility --topics topics/accessibility_topics.csv $(if $(TOPIC),--topic "$(TOPIC)")
