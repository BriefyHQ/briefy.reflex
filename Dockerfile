FROM briefy/python3:1.4.5
MAINTAINER Briefy <developers@briefy.co>

ADD . /app
WORKDIR /app

# Add ssh key for read-only access on Github
RUN mkdir /root/.ssh && chmod 600 /root/.ssh && \
    cp docker/id_rsa /root/.ssh/ && chmod 600 /root/.ssh/id_rsa && \
    echo "    IdentityFile ~/.ssh/id_rsa" >> /etc/ssh/ssh_config && \
    echo "Host github.com\n\tStrictHostKeyChecking no\n" >> /root/.ssh/config

# Add docker_entrypoint file
RUN cp docker/docker_entrypoint.sh / && chmod +x /docker_entrypoint.sh

RUN pip install -r requirements.txt

CMD ["/app/docker/monitor.sh"]

EXPOSE 8000
