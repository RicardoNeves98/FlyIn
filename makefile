VENV = FlyInEnv
FLAGS = --warn-return-any --warn-unused-ignores \
		--ignore-missing-imports --disallow-untyped-defs \
		--check-untyped-defs

$(VENV):
	python3 -m venv $(VENV)

$(VENV)/.installed: $(VENV)
	$(VENV)/bin/pip install flake8 mypy
	touch $(VENV)/.installed

install: $(VENV)/.installed

run:
	python3 main.py $(MAP)

debug:
	python3 -m pdb main.py $(MAP)	

clean:
	rm -rf __pycache__ .mypy_cache

lint: $(VENV)/.installed
	$(VENV)/bin/flake8 . --exclude=$(VENV),__pycache__,.mypy_cache 
	$(VENV)/bin/mypy . --exclude=$(VENV),__pycache__,.mypy_cache $(FLAGS)

.PHONY: install, run, debug, clean, lint