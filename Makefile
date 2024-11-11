PYPI=https://artifactory.jpl.nasa.gov/artifactory/api/pypi/pypi

test:
	python3 -m pytest tests/

format:
	python3 -m black fspa_scripts/ tests/

setup:
	pip install -r requirements.txt

build:
	rm -rf build dist *.egg-info __pycache__
	python3 setup.py sdist bdist_wheel

upload: repository ?= develop
upload:
	twine upload \
		--verbose \
		--repository-url "$(PYPI)-$(repository)-local" \
		dist/*

clean:
	rm -rf .pytest_cache output.csv build dist *.egg-info __pycache__
	find . | grep -E "(__pycache__|\.pyc$$)" | xargs rm -rf