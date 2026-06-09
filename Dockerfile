FROM python:3.10

RUN apt-get update && apt-get install -y chromium --no-install-recommends && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . /app

RUN pip install -e .

CMD ["streamlit", "run", "src/meteomat/app.py", "--server.port=7860", "--server.address=0.0.0.0"]
