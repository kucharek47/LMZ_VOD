FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && \
    apt-get install -y util-linux mount && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN addgroup --system grupa_app && adduser --system --group uzytkownik_app
RUN chown -R uzytkownik_app:grupa_app /app
USER uzytkownik_app

EXPOSE 13008

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "13008"]