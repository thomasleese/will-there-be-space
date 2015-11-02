FROM node:5

# Create user first.
RUN groupadd -r willtherebespace && useradd -r -g willtherebespace willtherebespace

# Install gosu.
RUN gpg --keyserver pool.sks-keyservers.net --recv-keys B42F6819007F00F88E364FD4036A9C25BF357DD4
RUN curl -o /usr/local/bin/gosu -SL "https://github.com/tianon/gosu/releases/download/1.2/gosu-$(dpkg --print-architecture)" \
    && curl -o /usr/local/bin/gosu.asc -SL "https://github.com/tianon/gosu/releases/download/1.2/gosu-$(dpkg --print-architecture).asc" \
    && gpg --verify /usr/local/bin/gosu.asc \
    && rm /usr/local/bin/gosu.asc \
    && chmod +x /usr/local/bin/gosu

# Install IRC and Redis modules.
RUN mkdir /code
WORKDIR /code
RUN npm install irc redis
COPY bot.js /code/bot.js

WORKDIR /code

# Add entrypoint.
COPY docker-entrypoint.sh /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]

CMD ["node", "bot.js"]
