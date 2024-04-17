import sys
sys.path.append('./')

import toml
from nl2sql.service import create_service

content_v1 = """Question: 部门中有多少人年龄大于56岁？ <sep> Tables: department: Department_ID , Name , Creation , Ranking , Budget_in_Billions , Num_Employees ; head: head_ID , name , born_state , age ; management: department_ID , head_ID , temporary_acting <sep>"""

content_v2 = """根据以下 table properties 和 Question, 将自然语言转换成SQL查询. 备注: 无. version: v3
POSTGRESQL SQL database: superhero, with their properties:

 CREATE TABLE alignment (
 id integer 0 PRI not null  COMMENT 列名：阵营id；注释：阵营id,
 alignment character varying 0  null  COMMENT 列名：阵营类型；注释：超级英雄的阵营\n常识：\n阵营是指角色的道德和伦理立场，可以用来描述超级英雄的整体态度或行为。 超级英雄的一些常见阵营类型包括：\n善良的阵营：这些超级英雄通常善良、无私，致力于保护他人和维护正义。 良好阵营的例子包括超人、神奇女侠和蜘蛛侠。\n中立的阵营：这些超级英雄可能并不总是优先考虑更大的善良，但他们也不一定是邪恶的。 他们可能会出于自己的利益行事或根据自己的道德准则做出决定。 中立阵营的例子包括绿巨人和死侍。\n邪恶的阵营：这些超级英雄通常是自私的、控制欲强的，并且愿意为了追求自己的目标而伤害他人。 邪恶阵营的例子包括莱克斯·卢瑟和小丑。,
 CONSTRAINT alignment_pkey PRIMARY KEY (id)
 );



COMMENT ON TABLE alignment IS '表名：阵营；注释：超级英雄的阵营，是指角色的道德和伦理立场，可以用来描述超级英雄的整体态度或行为。'

COMMENT ON COLUMN alignment.id IS '列名：阵营id；注释：阵营id',
COMMENT ON COLUMN alignment.alignment IS '列名：阵营类型；注释：超级英雄的阵营\n常识：\n阵营是指角色的道德和伦理立场，可以用来描述超级英雄的整体态度或行为。 超级英雄的一些常见阵营类型包括：\n善良的阵营：这些超级英雄通常善良、无私，致力于保护他人和维护正义。 良好阵营的例子包括超人、神奇女侠和蜘蛛侠。\n中立的阵营：这些超级英雄可能并不总是优先考虑更大的善良，但他们也不一定是邪恶的。 他们可能会出于自己的利益行事或根据自己的道德准则做出决定。 中立阵营的例子包括绿巨人和死侍。\n邪恶的阵营：这些超级英雄通常是自私的、控制欲强的，并且愿意为了追求自己的目标而伤害他人。 邪恶阵营的例子包括莱克斯·卢瑟和小丑。'

 CREATE TABLE attribute (
 id integer 0 PRI not null  COMMENT 列名：id；注释：属性id,
 attribute_name character varying 0  null  COMMENT 列名：属性；注释：超级英雄的属性\n常识：\n超级英雄的属性是定义他们是谁以及他们有能力的特征或品质。 这可以是一种身体特征，例如超人的力量或飞行能力，也可以是一种个人特征，例如非凡的智力或非凡的勇敢。\n常见的属性有：智力、力量、速度、耐用性、力量、战斗等。,
 CONSTRAINT attribute_pkey PRIMARY KEY (id)
 );



COMMENT ON TABLE attribute IS '表名：属性；注释：超级英雄的属性是定义他们是谁以及他们有能力的特征或品质'

COMMENT ON COLUMN attribute.id IS '列名：id；注释：属性id',
COMMENT ON COLUMN attribute.attribute_name IS '列名：属性；注释：超级英雄的属性\n常识：\n超级英雄的属性是定义他们是谁以及他们有能力的特征或品质。 这可以是一种身体特征，例如超人的力量或飞行能力，也可以是一种个人特征，例如非凡的智力或非凡的勇敢。\n常见的属性有：智力、力量、速度、耐用性、力量、战斗等。'

 CREATE TABLE colour (
 id integer 0 PRI not null  COMMENT 列名：颜色id；注释：颜色id,
 colour character varying 0  null  COMMENT 列名：颜色种类；注释：超级英雄的皮肤/眼睛/头发/等的颜色,
 CONSTRAINT colour_pkey PRIMARY KEY (id)
 );



COMMENT ON TABLE colour IS '表名：颜色；注释：超级英雄的皮肤/眼睛/头发/等的颜色'

COMMENT ON COLUMN colour.id IS '列名：颜色id；注释：颜色id',
COMMENT ON COLUMN colour.colour IS '列名：颜色种类；注释：超级英雄的皮肤/眼睛/头发/等的颜色'

 CREATE TABLE gender (
 id integer 0 PRI not null  COMMENT 列名：性别id；注释：性别id,
 gender character varying 0  null  COMMENT 列名：性别种类；注释：超级英雄的性别，性别种类有：男、女、无,
 CONSTRAINT gender_pkey PRIMARY KEY (id)
 );



COMMENT ON TABLE gender IS '表名：性别；注释：超级英雄的性别'

COMMENT ON COLUMN gender.id IS '列名：性别id；注释：性别id',
COMMENT ON COLUMN gender.gender IS '列名：性别种类；注释：超级英雄的性别，性别种类有：男、女、无'

 CREATE TABLE hero_attribute (
 hero_id integer 0 FRI null  COMMENT 列名：超级英雄id；注释：超级英雄id,
 attribute_id integer 0 FRI null  COMMENT 列名：属性id；注释：属性id,
 attribute_value integer 0  null  COMMENT 列名：属性值；注释：属性值\n常识：\n如果超级英雄在某一特定属性上具有较高的属性值，则意味着与其他超级英雄相比，他们在该领域更加熟练或强大。 例如，如果超级英雄具有较高的力量属性值，他们可能能够举起更重的物体或比其他超级英雄打出力量更大的拳头。,
 CONSTRAINT hero_attribute_hero_id_fkey FOREIGN KEY() REFERENCES superhero(),
 CONSTRAINT hero_attribute_attribute_id_fkey FOREIGN KEY() REFERENCES attribute()
 );



COMMENT ON TABLE hero_attribute IS '表名：超级英雄的属性值；注释：记录超级英雄对应的属性值，包含超级英雄id、属性id以及属性值。'

COMMENT ON COLUMN hero_attribute.hero_id IS '列名：超级英雄id；注释：超级英雄id',
COMMENT ON COLUMN hero_attribute.attribute_id IS '列名：属性id；注释：属性id',
COMMENT ON COLUMN hero_attribute.attribute_value IS '列名：属性值；注释：属性值\n常识：\n如果超级英雄在某一特定属性上具有较高的属性值，则意味着与其他超级英雄相比，他们在该领域更加熟练或强大。 例如，如果超级英雄具有较高的力量属性值，他们可能能够举起更重的物体或比其他超级英雄打出力量更大的拳头。'

 CREATE TABLE hero_power (
 hero_id integer 0 FRI null  COMMENT 列名：超级英雄id；注释：超级英雄id,
 power_id integer 0 FRI null  COMMENT 列名：超能力id；注释：超能力id,
 CONSTRAINT hero_power_hero_id_fkey FOREIGN KEY() REFERENCES superhero(),
 CONSTRAINT hero_power_power_id_fkey FOREIGN KEY() REFERENCES superpower()
 );



COMMENT ON TABLE hero_power IS '表名：超级英雄的超能力；注释：记录超级英雄对应的超能力，包括超级英雄id、超能力id。'

COMMENT ON COLUMN hero_power.hero_id IS '列名：超级英雄id；注释：超级英雄id',
COMMENT ON COLUMN hero_power.power_id IS '列名：超能力id；注释：超能力id'

 CREATE TABLE publisher (
 id integer 0 PRI not null  COMMENT 列名：发行商id；注释：发行商id,
 publisher_name character varying 0  null  COMMENT 列名：发行商；注释：超级英雄发行商/发行公司的名称,
 CONSTRAINT publisher_pkey PRIMARY KEY (id)
 );



COMMENT ON TABLE publisher IS '表名：发行商；注释：超级英雄的发行商'

COMMENT ON COLUMN publisher.id IS '列名：发行商id；注释：发行商id',
COMMENT ON COLUMN publisher.publisher_name IS '列名：发行商；注释：超级英雄发行商/发行公司的名称'

 CREATE TABLE race (
 id integer 0 PRI not null  COMMENT 列名：种族id；注释：种族id,
 race character varying 0  null  COMMENT 列名：种族；注释：超级英雄的种族\n常识：\n在超级英雄的故事背景下，超级英雄的种族是指超级英雄根据这些身体特征所属的特定人群。\n比如种族：Alien、Cyborg、Gungan等。,
 CONSTRAINT race_pkey PRIMARY KEY (id)
 );



COMMENT ON TABLE race IS '表名：种族；注释：超级英雄的种族'

COMMENT ON COLUMN race.id IS '列名：种族id；注释：种族id',
COMMENT ON COLUMN race.race IS '列名：种族；注释：超级英雄的种族\n常识：\n在超级英雄的故事背景下，超级英雄的种族是指超级英雄根据这些身体特征所属的特定人群。\n比如种族：Alien、Cyborg、Gungan等。'


Question: 一共有多少超级英雄"""


payload = {'model': 'gpt-3.5-turbo', 'messages': [{'role': 'user', 'content': content_v2}]}

conf = {}
with open('./conf/config.toml', 'r') as f:
    conf = toml.load(f)

for name, service_args in conf['openai']['service'].items():
    if service_args.get('type') != 'base':
        continue

    service = create_service(name, 'base', service_args['conf'])
    for content in [content_v1, content_v2]:
        print(content)
        payload['messages'][0]['content'] = content
        res = service.pre_process(payload)
        print(res['service_prompt'])
