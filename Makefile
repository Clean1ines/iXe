install-common:
	pip install -e common/

dev: install-common
	pip install -r requirements-dev.txt
