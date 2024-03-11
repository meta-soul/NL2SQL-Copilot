MODEL=$1
PORT=$2
PROMPT=""

if [[ -z "${MODEL}" ]] || [[ -z "${PORT}" ]]; then
    #MODEL="gpt-3.5-turbo"
    echo "Usage: sh client.sh <MODEL> <PORT>"
    exit 0
fi
if [[ "${MODEL}" == *"chatglm"* ]]; then
    PROMPT="将自然语言问题 Question 转换为SQL语句，数据库的表结构由 Tables 提供。仅返回SQL语句，不要进行解释。\n"
fi

API_BASE="http://127.0.0.1:${PORT}"
API_KEY="ak_84ff9c1c-4758-494b-b6fd-2f21f06650c3"
MODEL_NAME="${MODEL}"

echo "/v1/models"
curl ${API_BASE}/v1/models \
  -H "Authorization: Bearer $API_KEY"
echo -e "\n"

echo "/v1/chat/completions"
time curl ${API_BASE}/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $API_KEY" \
  -d '{
    "model": '\"${MODEL_NAME}\"',
    "messages": [{"role": "user", "content": "'"${PROMPT}"'Question: 所有章节的名称和描述是什么？ <sep> Tables: sections: section id , course id , section name , section description , other details <sep>"}]
  }'
echo -e "\n"

# schema same with offline model
echo "/v1/chat/completions"
time curl ${API_BASE}/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $API_KEY" \
  -d '{
    "model": '\"${MODEL_NAME}\"',
    "messages": [{"role": "user", "content": "'"${PROMPT}"'Question: 名人堂一共有多少球员 <sep> Tables: hall_of_fame: player_id, yearid, votedby, ballots, needed, votes, inducted, category, needed_note ; player_award: player_id, award_id, year, league_id, tie, notes ; player_award_vote: award_id, year, league_id, player_id, points_won, points_max, votes_first ; salary: year, team_id, league_id, player_id, salary ; player: player_id, birth_year, birth_month, birth_day, birth_country, birth_state, birth_city, death_year, death_month, death_day, death_country, death_state, death_city, name_first, name_last, name_given, weight ; primary keys: hall_of_fame.player_id, player_award.player_id, player_award_vote.player_id, salary.player_id, player.player_id ; foreign keys: player_award.player_id = hall_of_fame.player_id, player_award_vote.player_id = hall_of_fame.player_id, salary.player_id = hall_of_fame.player_id, player.player_id = hall_of_fame.player_id <sep>"}],
    "temperature": 0.001
  }'
echo -e "\n"

# schema same with offline model (larger temperature)
echo "/v1/chat/completions"
time curl ${API_BASE}/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $API_KEY" \
  -d '{
    "model": '\"${MODEL_NAME}\"',
    "stream": true,
    "messages": [{"role": "user", "content": "'"${PROMPT}"'Question: 名人堂一共多少球员 <sep> Tables: hall_of_fame: player_id , yearid , votedby , ballots , needed , votes , inducted , category , needed_note ; player: player_id , birth_year , birth_month , birth_day , birth_country , birth_state , birth_city , death_year , death_month , death_day , death_country , death_state , death_city , name_first , name_last , name_given , weight ; player_award: player_id , award_id , year , league_id , tie , notes ; player_award_vote: award_id , year , league_id , player_id , points_won , points_max , votes_first ; salary: year , team_id , league_id , player_id , salary ; primary keys: hall_of_fame.player_id , player.player_id , player_award.player_id , player_award_vote.player_id , salary.player_id ; foreign keys: player.player_id = hall_of_fame.player_id , player_award.player_id = hall_of_fame.player_id , player_award_vote.player_id = hall_of_fame.player_id , salary.player_id = hall_of_fame.player_id <sep>"}],
    "temperature": 0.1
  }'
echo -e "\n"
