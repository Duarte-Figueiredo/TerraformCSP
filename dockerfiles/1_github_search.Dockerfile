FROM python:3

WORKDIR /usr/src/app

COPY ../requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY .. .

ENV PYTHONPATH=.

CMD [ "python", "github_scraper/github_search.py" ]
