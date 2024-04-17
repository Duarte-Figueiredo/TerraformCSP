FROM python:3

WORKDIR /usr/src/app

COPY ../../requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY ../../one_off_scripts ./one_off_scripts
COPY ../../terraform_analyzer ./terraform_analyzer

ENV PYTHONPATH=.

CMD [ "python", "one_off_scripts/repo_tf_fetcher.py" ]
