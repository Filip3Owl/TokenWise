FROM python:3.14-slim

WORKDIR /app

# Install dependencies first (layer is cached unless requirements change)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download NLTK data (no SSL workaround needed on Linux)
RUN python -c "\
import nltk; \
nltk.download('punkt_tab'); \
nltk.download('stopwords'); \
nltk.download('wordnet'); \
nltk.download('omw-1.4'); \
nltk.download('rslp')"

COPY . .

RUN pip install --no-cache-dir -e .

EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
