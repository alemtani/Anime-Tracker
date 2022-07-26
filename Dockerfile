FROM python:slim

RUN useradd animetracker

WORKDIR /home/animetracker

COPY requirements.txt requirements.txt
RUN python -m venv venv
RUN venv/bin/pip install -r requirements.txt
RUN venv/bin/pip install gunicorn

COPY app app
COPY migrations migrations
COPY animetracker.py config.py boot.sh ./
RUN chmod +x boot.sh

ENV FLASK_APP animetracker.py

RUN chown -R animetracker:animetracker ./
USER animetracker

EXPOSE 5000
ENTRYPOINT ["./boot.sh"]