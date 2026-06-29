FROM python:3.11-slim
WORKDIR /app
COPY web/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8080
USER 1000
# CMD ["python", "web/run.py"]
CMD ["python", "-m", "web.run"]