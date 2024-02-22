test:
	python3 -m pytest tests/

format:
	python3 -m black fspa_scripts/ tests/

build:
	rm -rf build dist *.egg-info __pycache__
	python3 setup.py sdist bdist_wheel

setup:
	pip install -r requirements.txt

clean:
	rm -rf .pytest_cache output.csv build dist *.egg-info __pycache__
	find . | grep -E "(__pycache__|\.pyc$$)" | xargs rm -rf