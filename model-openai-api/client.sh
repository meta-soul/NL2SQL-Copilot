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

prompt_x=$(cat <<-END
### Task
Generate a SQL query to answer [QUESTION]在云南省的所有城市里找出一家名为海盗船自助餐的餐厅。[/QUESTION]

### Database Schema
The query will run on a database with the following schema:
CREATE TABLE "business" (
"bid" int,
"business_id" text,
"name" text,
"full_address" text,
"city" text,
"latitude" text,
"longitude" text,
"review_count" int,
"is_open" int,
"rating" real,
"state" text,
primary key("bid")
);
CREATE TABLE "category" (
"id" int,
"business_id" text,
"category_name" text,
primary key("id"),
foreign key("business_id") references business("business_id")
);
CREATE TABLE "user" (
"uid" int,
"user_id" text,
"name" text,
primary key("uid")
);
CREATE TABLE "checkin" (
"cid" int,
"business_id" text,
"count" int,
"day" text,
primary key("cid"),
foreign key("business_id") references business("business_id")
);

CREATE TABLE "neighbourhood" (
"id" int,
"business_id" text,
"neighbourhood_name" text,
primary key("id"),
foreign key("business_id") references business("business_id")
);

CREATE TABLE "review" (
"rid" int,
"business_id" text,
"user_id" text,
"rating" real,
"text" text,
"year" int,
"month" text,
primary key("rid"),
foreign key("business_id") references business("business_id"),
foreign key("user_id") references user("user_id")
);
CREATE TABLE "tip" (
"tip_id" int,
"business_id" text,
"text" text,
"user_id" text,
"likes" int,
"year" int,
"month" text,
primary key("tip_id")
foreign key("business_id") references business("business_id"),
foreign key("user_id") references user("user_id")

);


### Answer
Given the database schema, here is the SQL query that [QUESTION]在云南省的所有城市里找出一家名为海盗船自助餐的餐厅。[/QUESTION]
[SQL]
END
)

echo "/v1/chat/completions"
time curl ${API_BASE}/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $API_KEY" \
  -d '{
    "model": '\"${MODEL_NAME}\"',
    "temperature": 0.2,
    "messages": [
        {
            "role": "user",
            "content": "### Task\nGenerate a SQL query to answer [QUESTION]在云南省的所有城市里找出一家名为海盗船自助餐的餐厅。[/QUESTION]\n\n### Database Schema\nThe query will run on a database with the following schema:\nCREATE TABLE \"business\" (\n\"bid\" int,\n\"business_id\" text,\n\"name\" text,\n\"full_address\" text,\n\"city\" text,\n\"latitude\" text,\n\"longitude\" text,\n\"review_count\" int,\n\"is_open\" int,\n\"rating\" real,\n\"state\" text,\nprimary key(\"bid\")\n);\nCREATE TABLE \"category\" (\n\"id\" int,\n\"business_id\" text,\n\"category_name\" text,\nprimary key(\"id\"),\nforeign key(\"business_id\") references business(\"business_id\")\n);\nCREATE TABLE \"user\" (\n\"uid\" int,\n\"user_id\" text,\n\"name\" text,\nprimary key(\"uid\")\n);\nCREATE TABLE \"checkin\" (\n\"cid\" int,\n\"business_id\" text,\n\"count\" int,\n\"day\" text,\nprimary key(\"cid\"),\nforeign key(\"business_id\") references business(\"business_id\")\n);\n\nCREATE TABLE \"neighbourhood\" (\n\"id\" int,\n\"business_id\" text,\n\"neighbourhood_name\" text,\nprimary key(\"id\"),\nforeign key(\"business_id\") references business(\"business_id\")\n);\n\nCREATE TABLE \"review\" (\n\"rid\" int,\n\"business_id\" text,\n\"user_id\" text,\n\"rating\" real,\n\"text\" text,\n\"year\" int,\n\"month\" text,\nprimary key(\"rid\"),\nforeign key(\"business_id\") references business(\"business_id\"),\nforeign key(\"user_id\") references user(\"user_id\")\n);\nCREATE TABLE \"tip\" (\n\"tip_id\" int,\n\"business_id\" text,\n\"text\" text,\n\"user_id\" text,\n\"likes\" int,\n\"year\" int,\n\"month\" text,\nprimary key(\"tip_id\")\nforeign key(\"business_id\") references business(\"business_id\"),\nforeign key(\"user_id\") references user(\"user_id\")\n\n);\n\n\n### Answer\nGiven the database schema, here is the SQL query that [QUESTION]在云南省的所有城市里找出一家名为海盗船自助餐的餐厅。[/QUESTION]\n[SQL]\n"
        }
    ]
}'
echo -e "\n"

echo "/v1/chat/completions"
time curl ${API_BASE}/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $API_KEY" \
  -d '{
    "model": '\"${MODEL_NAME}\"',
    "messages": [{"role": "user", "content": "'"${PROMPT}"'Question: 一共多少学生 <sep> Tables: 142_0: table_name ; 2022_030-5x: xm , sfzhm , 合同开始时间 , 合同结束时间 , 岗位性质 , 公益性岗位名称 , 单位名称 , 所属区划 , 所属街道 , 登记失业地 , rylb , 是否困难人员就业 , 就业状态 , 人员登记备注 , 性别 , 民族 , 学历 , 健康状况 , 户籍地址 , 居住地址 , 联系电话 , 手机号码 , 经办人 , 经办日期 , 经办机构 , 年龄 , 公安死亡注销时间 , ga , 民政殡葬火化时间 , 卫健委医学死亡证明时间 , 5月是否缴纳养老 , 低保信息 , 残疾人信息 , qyzt , 贫困信息 , 失信信息 , 退休信息 , 判断结果 , 是否满36个月 , ybjk , yb ; 2022_030x: xm , sfzhm , 岗位性质 , 岗位类型 , 公益性岗位名称 , 用岗位名称 , 性别 , 民族 , 联系电话 , 学历 , 健康状况 , 户籍地址 , 居住地址 , 合同开始时间 , 合同结束时间 , 岗位性质1 , 岗位类型1 , 公益性岗位名称1 , 用岗单位名称 , 单位名称 , 所属区划 , 所属街道 , 登记失业地 , rylb , 是否困难人员就业 , 就业状态 , 社保银行 , 社保银行卡号 , 人员登记备注 , 用岗单位名称1 , 手机号码 , 经办人 , 经办日期 , 经办机构 ; 2022_030x-6: xm , sfzhm , 岗位性质 , 岗位类型 , 公益性岗位名称 , 用岗位名称 , 性别 , 民族 , 联系电话 , 学历 , 健康状况 , 户籍地址 , 居住地址 , 合同开始时间 , 合同结束时间 , 岗位性质1 , 岗位类型1 , 公益性岗位名称1 , 用岗单位名称 , 单位名称 , 所属区划 , 所属街道 , 登记失业地 , rylb , 是否困难人员就业 , 就业状态 , 社保银行 , 社保银行卡号 , 人员登记备注 , 用岗单位名称1 , 手机号码 , 经办人 , 经办日期 , 经办机构 ; 2022_030x_7: xm , sfzhm , 岗位性质 , 岗位类型 , 公益性岗位名称 , 用岗位名称 , 性别 , 民族 , 联系电话 , 学历 , 健康状况 , 户籍地址 , 居住地址 , 合同开始时间 , 合同结束时间 , 岗位性质1 , 岗位类型1 , 公益性岗位名称1 , 用岗单位名称 , 单位名称 , 所属区划 , 所属街道 , 登记失业地 , rylb , 是否困难人员就业 , 就业状态 , 社保银行 , 社保银行卡号 , 人员登记备注 , 用岗单位名称1 , 手机号码 , 经办人 , 经办日期 , 经办机构 ; 2022_030x_8: xm , sfzhm , 岗位性质 , 岗位类型 , 公益性岗位名称 , 用岗位名称 , 性别 , 民族 , 联系电话 , 学历 , 健康状况 , 户籍地址 , 居住地址 , 合同开始时间 , 合同结束时间 , 岗位性质1 , 岗位类型1 , 公益性岗位名称1 , 用岗单位名称 , 单位名称 , 所属区划 , 所属街道 , 登记失业地 , rylb , 是否困难人员就业 , 就业状态 , 社保银行 , 社保银行卡号 , 人员登记备注 , 用岗单位名称1 , 手机号码 , 经办人 , 经办日期 , 经办机构 ; 2022_kj: xm , sfzhm , xb , lb , nl , hjd , hjxx , cjdj , cjlb , sfpk , sfsw , nanname , nansfzh , nvname , nvsfzh , sfly , hyhy , hjjk1 , thry , cjr , pk , mzbz , gajk , wjw , nansfcj , nvsfcj , nansfpk , nvsfpk , nvsfsw , nansfsw , nansbxx , nvsbxx ; 2022_kj1: xm , sfzhm , xb , lb , nl , hjd , hjxx , cjdj , cjlb , sfpk , sfsw , nanname , nansfzh , nvname , nvsfzh , sfly , hyhy , hjjk1 , thry , cjr , pk , mzbz , gajk , wjw , nansfcj , nvsfcj , nansfpk , nvsfpk , nvsfsw , nansfsw , nansbxx , nvsbxx ; 2023_0: dwmc , 在职人数 , lx ; 2023_00: 证件类型 , sfzhm , xm , 类型 , bz , gajk , ga , mzbz , wjw , name <sep>"}],
    "temperature": 0.001
  }'
echo -e "\n"
