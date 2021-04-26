# Pull official base image
FROM python:3-alpine

# Set work directory

WORKDIR /usr/src/foaipmh
RUN mkdir static

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1


# Install dependencies
RUN apk update && \
    apk add build-base gcc musl-dev && \
    apk add postgresql-dev && \
    apk add libxml2-dev libxslt-dev
#RUN pip install --upgrade pip setuptools
RUN pip install --upgrade pip==21.0.1
COPY ./requirements.txt .
RUN pip install -r requirements.txt

COPY ./entrypoint.prod.sh .

# Copy project
COPY ./foaipmh .
COPY ./oai_pmh .
COPY ./manage.py .
COPY ./local.py .

# Run entrypoint.sh
ENTRYPOINT ["/usr/src/foaipmh/entrypoint.prod.sh"]
