.PHONY: install pipeline dashboard

install:
	pip install -r requirements.txt

pipeline:
	python -m src.pipeline.run_all

dashboard:
	streamlit run src/dashboard/app.py
