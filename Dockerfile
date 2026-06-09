FROM python:3.10

WORKDIR /app
COPY . /app

RUN pip install -e .

CMD ["streamlit", "run", "src/meteomat/app.py", "--server.port=7860", "--server.address=0.0.0.0"]
