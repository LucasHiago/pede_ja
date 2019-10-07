# Commands

manage:
	@pipenv run ./manage.py $(wordlist 2,$(words $(MAKECMDGOALS)), $(MAKECMDGOALS))

start:
	@pipenv run ./manage.py runserver

lint:
	@pipenv run flake8
	@echo "${SUCCESS}✔${NC} The code is following the PEP8"

loaddata:
	@pipenv run ./manage.py loaddata register/fixtures/initial_data.yaml

updatabase:
	@docker-compose -f docker/docker-compose.yml up database


# Utils

## Colors
SUCCESS = \033[0;32m
INFO = \033[0;36m
WARNING = \033[0;33m
DANGER = \033[0;31m
NC = \033[0m