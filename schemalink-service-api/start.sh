PORT=$1
CONF=$2

if [ -z "${PORT}" ]; then
    #PORT=$(python -c 'import socket; s=socket.socket(); s.bind(("", 0)); print(s.getsockname()[1]); s.close()')
    PORT=18022
fi
if [ -z "$CONF" ]; then
    CONF="conf/config.toml"
fi

lsof -t -i:${PORT} | xargs kill -9 > /dev/null 2>&1
sleep 2

mkdir -p ./logs
ds=`date +%Y%m%d%H%m%S`
pid_file=start.pid
log_file=./logs/start.${ds}.log

#kill -9 `cat ${pid_file}` > /dev/null 2>&1
#sleep 2

export PYTHONPATH=./src

PYTHONUNBUFFERED=x nohup python3 -u src/main.py --config ${CONF} --port ${PORT} > ${log_file} 2>&1 & echo $! > ${pid_file}

pid=$(cat ${pid_file})
echo "PID: ${pid}"
echo "Port: ${PORT}"
echo "Conf: ${CONF}"
