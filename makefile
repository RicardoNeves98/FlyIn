VENV = FlyInVenv
IGNORE = .venv __pycache__ .mypy__cache__
FLAGS = (
	--warn-return-any --warn-unused-ignores
	--ignore-missing-imports --disallow-untyped-defs
	--check-untyped-defs
	)

$(VENV):
	python3 -m venv $(VENV)

$(VENV)/.installed: $(VENV)
	$(VENV)/bin/pip install flake mypy
	touch $(VENV)/.installed

install: $(VENV)/.installed

run:
	python3 main.py $(MAP)

debug:
	python3 -m pbd main.py $(MAP)	

clean:
	rm -rf __pycache__ .mypy_cache

lint: $(VENV)/.installed
	.venv/bin/flake8 . --exclude=$(IGNORE) $(FLAGS)
	.venv/bin/mypy . --exclude=$(IGNORE) $(FLAGS)

.PHONY: install, run, debug, clean, lint