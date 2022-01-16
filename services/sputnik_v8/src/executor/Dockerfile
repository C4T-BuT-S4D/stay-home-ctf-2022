FROM node:boron

ADD src/package.json /app/package.json
ADD src/package-lock.json /app/package-lock.json

WORKDIR /app
RUN npm install

ADD src/config.env /config.env
ADD run.sh /run.sh

ADD src .

CMD ["/run.sh", "node", "executor/index.js"]