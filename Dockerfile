FROM python:3.9-slim

ENV ACCEPT_EULA=Y

# 1) System deps + build tools
RUN apt-get update -y \
 && apt-get install -y --no-install-recommends \
      curl \
      gcc \
      g++ \
      gnupg \
      unixodbc-dev \
 && rm -rf /var/lib/apt/lists/*

# 2) Microsoft ODBC repo + install msodbcsql18
RUN curl https://packages.microsoft.com/config/debian/11/prod.list \
    > /etc/apt/sources.list.d/mssql-release.list \
 && curl https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor \
    > /etc/apt/trusted.gpg.d/microsoft.gpg \
 && apt-get update \
 && ACCEPT_EULA=Y apt-get install -y --no-install-recommends \
      msodbcsql18 \
      unixodbc-dev \
 && rm -rf /var/lib/apt/lists/*


# 3) Python deps
WORKDIR /app
COPY requirements.txt .
RUN pip install --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

# 4) Copy app & expose port
COPY . .
EXPOSE 5000

# 5) Run under Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:create_app()"]
