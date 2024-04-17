PORT=$1
CONF=$2

if [ -z "${PORT}" ]; then
    PORT=18080
fi
if [ -z "$CONF" ]; then
    CONF=conf/config.toml
fi

pid_file=start.pid
if [ -s "$pid_file" ]; then
    kill -9 `cat ${pid_file}` > /dev/null 2>&1
    sleep 2
fi

mkdir -p logs
ds=`date +%Y%m%d%H%M%S`
log_file=./logs/start.${ds}.log

export PYTHONPATH=./src

PYTHONUNBUFFERED=x nohup python -u main.py --port "${PORT}" --config ${CONF} > ${log_file} 2>&1 & echo $! > ${pid_file}
