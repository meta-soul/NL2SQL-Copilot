models=$1
PORT=$2
CONF=$3
if [ -z "${models}" ]; then
    models=gpt-3.5-turbo
fi

if [ -z "${PORT}" ]; then
    PORT=$(python -c 'import socket; s=socket.socket(); s.bind(("", 0)); print(s.getsockname()[1]); s.close()')
fi

if [ -z "$CONF" ]; then
    CONF="conf/config.toml"
fi

mkdir -p ./logs
ds=`date +%Y%m%d%H%m%S`
pid_file=start.pid
log_file=./logs/start.${ds}.log

#lsof -t -i:${PORT} | xargs kill -9 > /dev/null 2>&1
if [ -s "$pid_file" ]; then
    kill -9 `cat ${pid_file}` > /dev/null 2>&1
    > $pid_file
    sleep 2
fi

export PYTHONPATH=./src

PYTHONUNBUFFERED=x nohup python3 -u src/main.py --config ${CONF} \
  --llm_model="${models}" \
  --port ${PORT} \
  > ${log_file} 2>&1 & echo $! > ${pid_file}

pid=$(cat ${pid_file})
while :
do
    s=`lsof -i:${PORT} | grep "*:${PORT}"`
    if [ -z "${s}" ]; then
        echo "Service is loading..."
        sleep 1
    else
        break
    fi
done

echo "Service is Done!"
echo "PID: ${pid}"
echo "Port: ${PORT}"
echo "Conf: ${CONF}"
echo "Models: ${models}"
