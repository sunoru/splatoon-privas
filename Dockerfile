FROM python:3.7-alpine

RUN sed -i 's/dl-cdn.alpinelinux.org/mirrors.ustc.edu.cn/g' /etc/apk/repositories

RUN apk add --no-cache libzmq
RUN apk add --no-cache --virtual=build-dependencies python3-dev gcc zeromq-dev libc-dev \
    && pip install zerorpc \
    && apk del build-dependencies

COPY . /code

CMD [ "python /code/src/start_rpc.py" ]
