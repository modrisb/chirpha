#!/usr/bin/env bash
# sudo docker run -it -v /home/modrisb/contributions/data:/data -p 8080:8080  -e POSTGRES_PASSWORD=secret --entrypoint /bin/bash chirpstack:latest
#sudo docker run -it -v /home/modrisb/contributions/data:/data -v /home/modrisb/contributions/share:/share -p 8080:8080  chirpstack:latest
# pg_dump -h localhost chirpstack -U chirpstack -W > /share/chirp2mqtt/chirp_db0
# su - -c "postgres psql -U chirpstack -W < /data/chirp_db"
set -x

if ! [ -d "/data/redis" ]; then
    mkdir /data/redis
fi

#   redis-server
ps -A | grep -q "redis\-server \*\:"
if [ $? != 0 ]; then
    redis-server /etc/redis.conf &
fi

export LANG="C.UTF-8"
export PGDATA="/data/postgres"
export POSTGRES_PASSWORD="password"
#env

if ! [ -d "/data/postgres" ]; then
    mkdir /data/postgres
fi

#   while [[ "$(su-exec postgres pg_isready)" != *connections ]]
if [[ "$(su-exec postgres pg_isready)" != *accepting* ]]; then
    docker-entrypoint.sh postgres &
fi

INITIALIZED="/data/chirpstack_tables_initialized"

while [[ "$(su-exec postgres pg_isready)" != *accepting* ]]
do
    sleep 1
done

if [ -f "/share/chirp2mqtt/chirp_db" ]; then
    su-exec postgres psql -c "drop database if exists chirpstack;"
    su-exec postgres psql -c "drop role if exists chirpstack;"
    su-exec postgres psql -c "create role chirpstack with login password 'chirpstack';"
    su-exec postgres psql -c "create database chirpstack with owner chirpstack;"
    su-exec postgres psql -d chirpstack < /share/chirp2mqtt/chirp_db >/dev/null
    #su-exec postgres createdb -h localhost -p 5432 -U xxuserxx -T template0 test
    #su-exec postgres pg_restore -h localhost -p 5432 -U xxuserxx -d test db.dump
    #su-exec postgres createdb -h localhost -U chirpstack -W chirpstack
    #su-exec postgres pg_restore -h localhost -c -d chirpstack -1 /data/chirp.dump
    #pg_restore -h localhost -C -d chirpstack /data/chirp.dump
    if [[ $? -eq 0 ]]; then
        touch $INITIALIZED
        mv /share/chirp2mqtt/chirp_db /share/chirp2mqtt/chirp_db.restored
    fi
fi

if ! [ -f "$INITIALIZED" ]; then
    su-exec postgres psql -c "drop database if exists chirpstack;"
    su-exec postgres psql -c "drop role if exists chirpstack;"
    su-exec postgres psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --no-password --no-psqlrc -f /etc/postgres_chirp.sql
    if [[ $? -eq 0 ]]; then
        touch $INITIALIZED
    fi
fi

for portotest in ":6379" ":5432"
do
    netstat -tulpn 2>/dev/null | grep -q "$portotest"
    while [ $? != 0 ]
    do
        sleep 1
        netstat -tulpn 2>/dev/null | grep -q "$portotest"
    done
done

#chirpstack -c /etc/chirpstack
ps -A | grep -q "chirpstack \-c \/etc\/chirpstack"
if [ $? != 0 ]; then
    if [ -d "/share/chirp2mqtt/etc/chirpstack" ]; then
        cp /share/chirp2mqtt/etc/chirpstack/* /etc/chirpstack
    fi
    chirpstack -c /etc/chirpstack &
fi

for portotest in ":8080"
do
    netstat -tulpn 2>/dev/null | grep -q "$portotest"
    while [ $? != 0 ]
    do
        sleep 1
        netstat -tulpn 2>/dev/null | grep -q "$portotest"
    done
done

#chirpstack-gateway-bridge
ps -A | grep -q "chirpstack\-gateway\-bridge"
if [ $? != 0 ]; then
    if [ -d "/share/chirp2mqtt/etc/chirpstack-gateway-bridge" ]; then
        cp /share/chirp2mqtt/etc/chirpstack-gateway-bridge/* /etc/chirpstack-gateway-bridge
    fi
    chirpstack-gateway-bridge &
fi

#python3 -m usr.app.start
cd /
python3 -m usr.app.start

