FROM python:3.9-slim

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1


#COPY ./pyproject.toml ./pyproject.toml
COPY ./requirements.txt .
COPY ./README.md .
COPY ./setup.py .
COPY ./GD4H_eau GD4H_eau
COPY ./data/info_AtlaSante.csv data/info_AtlaSante.csv

RUN pip install --upgrade pip setuptools wheel \
    && pip install -e . \
    && pip cache purge \
    && rm -rf /root/.cache/pip

ENV STREAMLIT_SERVER_PORT 3838
EXPOSE $STREAMLIT_SERVER_PORT
ENTRYPOINT ["streamlit", "run"]
CMD [ "GD4H_eau/app.py" ]
