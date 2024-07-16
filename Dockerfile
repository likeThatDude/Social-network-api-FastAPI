FROM python:3.10
RUN apt-get update && rm -rf /var/lib/apt/lists/*
COPY . /app
WORKDIR /app
RUN rm -r client
RUN pip install -r requirements.txt
COPY docker_set_files/app.sh /sh_files/app.sh
RUN chmod +x /sh_files/app.sh
ENTRYPOINT ["/sh_files/app.sh"]
