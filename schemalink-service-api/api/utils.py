import torch
import torch.nn as nn
from torch.utils.data import Dataset

from transformers import AutoConfig, RobertaModel, XLMRobertaModel


def normal(question: str, db):
    schema_linking_db = dict()
    database = db["database"]
    tables = db["tables"]


    schema_linking_db["database"] = database
    schema_linking_db["schema_items"] = []
    schema_linking_db["no_lower_schema_items"] = []
    schema_linking_db["pk"] = []
    schema_linking_db["no_lower_pk"] = []
    schema_linking_db["fk"] = []
    schema_linking_db["no_lower_fk"] = []

    for idx,  table in enumerate(tables):
        table_name = table["table"]
        columns = table["columns"]

        column_names_no_lower_list = []
        column_names_list = []
        column_types_list = []

        for column in columns:
            column_name = column["column"]
            column_names_no_lower_list.append(column_name)
            column_names_list.append(column_name.lower())
            column_types_list.append(column["type"])

            primary_key = column["primary_key"] if "primary_key" in column.keys() else []
            if primary_key:
                schema_linking_db["no_lower_pk"].append(
                    {
                        "table_name_original": table_name,
                        "column_name_original": column_name
                    }
                )

                schema_linking_db["pk"].append(
                    {
                        "table_name_original": table_name.lower(),
                        "column_name_original": column_name.lower()
                    }
                )
            foreign_keys = column["reference_key"] if "reference_key" in column.keys() else []

            if foreign_keys!="":
                # record foreign keys
                fk_source_table_name_original = table_name
                fk_source_column_name_original = column_name

                fk_target_table_name_original = foreign_keys.split(".")[0]
                fk_target_column_name_original = foreign_keys.split(".")[1]

                schema_linking_db["no_lower_fk"].append(
                        {
                            "source_table_name_original": fk_source_table_name_original,
                            "source_column_name_original": fk_source_column_name_original,
                            "target_table_name_original": fk_target_table_name_original,
                            "target_column_name_original": fk_target_column_name_original,
                        }
                    )

                schema_linking_db["fk"].append(
                        {
                            "source_table_name_original": fk_source_table_name_original.lower(),
                            "source_column_name_original": fk_source_column_name_original.lower(),
                            "target_table_name_original": fk_target_table_name_original.lower(),
                            "target_column_name_original": fk_target_column_name_original.lower(),
                        }
                    )

        schema_linking_db["no_lower_schema_items"].append({
            "table_name": table_name,
            "table_name_original": table_name,
            "column_names": column_names_no_lower_list,
            "column_names_original": column_names_no_lower_list,
            "column_types": column_types_list
        })

        schema_linking_db["schema_items"].append({
            "table_name": table_name.lower(),
            "table_name_original": table_name.lower(),
            "column_names": column_names_list,
            "column_names_original": column_names_list,
            "column_types": column_types_list
        })

    schema_linking_db["question"] = question.replace("\u2018", "'").replace("\u2019", "'").replace("\u201c",
                                                                                                   "'").replace(
        "\u201d", "'").strip()

    return  schema_linking_db

class ColumnAndTableClassifierDataset(Dataset):
    def __init__(
            self,
            dataset: dict = None,
            use_contents: bool = True,
            add_fk_info: bool = True,
    ):
        super(ColumnAndTableClassifierDataset, self).__init__()

        self.questions: list[str] = []

        self.all_column_infos: list[list[list[str]]] = []
        # self.all_column_labels: list[list[list[int]]] = []

        self.all_table_names: list[list[str]] = []
        # self.all_table_labels: list[list[int]] = []

        data = dataset
        column_names_in_one_db = []
        column_names_original_in_one_db = []
        extra_column_info_in_one_db = []

        table_names_in_one_db = []
        table_names_original_in_one_db = []

        for table_id in range(len(data["schema_items"])):
            column_names_original_in_one_db.append(data["schema_items"][table_id]["column_names_original"])
            table_names_original_in_one_db.append(data["schema_items"][table_id]["table_name_original"])

            table_names_in_one_db.append(data["schema_items"][table_id]["table_name"])

            column_names_in_one_db.append(data["schema_items"][table_id]["column_names"])

            extra_column_info = ["" for _ in range(len(data["schema_items"][table_id]["column_names"]))]
            if use_contents and "db_contents" in data["schema_items"][table_id].keys():
                contents = data["schema_items"][table_id]["db_contents"] if data["schema_items"][table_id][
                                                                             "db_contents"] != None else []

                for column_id, content in enumerate(contents):
                    if len(content) != 0:
                        extra_column_info[column_id] += " , ".join(content)
            extra_column_info_in_one_db.append(extra_column_info)

        if add_fk_info:
            table_column_id_list = []
            # add a [FK] identifier to foreign keys
            for fk in data["fk"]:
                source_table_name_original = fk["source_table_name_original"]
                source_column_name_original = fk["source_column_name_original"]
                target_table_name_original = fk["target_table_name_original"]
                target_column_name_original = fk["target_column_name_original"]
                # 添加表后可能有表名重复的情况
                if source_table_name_original in table_names_original_in_one_db:
                    source_table_id = table_names_original_in_one_db.index(source_table_name_original)

                    # 如果第一个表不是的话跳过去找
                    if source_column_name_original not in column_names_original_in_one_db[source_table_id]:
                        # 特殊情况  存在source_table_name_original重名时 因为没将所有表加入 表中只有一个table 重名的那个找不到 跳过
                        if source_table_name_original not in table_names_original_in_one_db[source_table_id + 1:]:
                            continue
                        source_table_id = table_names_original_in_one_db[source_table_id + 1:].index(
                            source_table_name_original) + source_table_id + 1

                    source_column_id = column_names_original_in_one_db[source_table_id].index(
                        source_column_name_original)
                    if [source_table_id, source_column_id] not in table_column_id_list:
                        table_column_id_list.append([source_table_id, source_column_id])

                # 添加表后可能有表名重复的情况
                if target_table_name_original in table_names_original_in_one_db:

                    target_table_id = table_names_original_in_one_db.index(target_table_name_original)
                    # 如果第一个表不是的话跳过去找
                    if target_column_name_original not in column_names_original_in_one_db[target_table_id]:
                        if target_table_name_original not in table_names_original_in_one_db[target_table_id + 1:]:
                            continue
                        target_table_id = table_names_original_in_one_db[target_table_id + 1:].index(
                            target_table_name_original) + target_table_id + 1

                    target_column_id = column_names_original_in_one_db[target_table_id].index(
                        target_column_name_original)
                    if [target_table_id, target_column_id] not in table_column_id_list:
                        table_column_id_list.append([target_table_id, target_column_id])

            for table_id, column_id in table_column_id_list:
                if extra_column_info_in_one_db[table_id][column_id] != "":
                    extra_column_info_in_one_db[table_id][column_id] += " , [FK]"
                else:
                    extra_column_info_in_one_db[table_id][column_id] += "[FK]"

        # column_info = column name + extra column info
        column_infos_in_one_db = []
        for table_id in range(len(table_names_in_one_db)):
            column_infos_in_one_table = []
            for column_name, extra_column_info in zip(column_names_in_one_db[table_id],
                                                      extra_column_info_in_one_db[table_id]):
                if len(extra_column_info) != 0:
                    column_infos_in_one_table.append(column_name + " ( " + extra_column_info + " ) ")
                else:
                    column_infos_in_one_table.append(column_name)
            column_infos_in_one_db.append(column_infos_in_one_table)

        self.questions.append(data["question"])

        self.all_table_names.append(table_names_in_one_db)

        self.all_column_infos.append(column_infos_in_one_db)


    def __len__(self):
        return len(self.questions)


    def __getitem__(self, index):
        question = self.questions[index]

        table_names_in_one_db = self.all_table_names[index]

        column_infos_in_one_db = self.all_column_infos[index]

        return question, table_names_in_one_db, column_infos_in_one_db




def prepare_batch_inputs_and_labels(batch, tokenizer):
    batch_size = len(batch)
    batch_questions = [data[0] for data in batch]

    batch_table_names = [data[1] for data in batch]

    batch_column_infos = [data[2] for data in batch]

    batch_input_tokens, batch_column_info_ids, batch_table_name_ids, batch_column_number_in_each_table = [], [], [], []
    batch_input_length = []
    for batch_id in range(batch_size):
        input_tokens = [batch_questions[batch_id]]
        table_names_in_one_db = batch_table_names[batch_id]
        column_infos_in_one_db = batch_column_infos[batch_id]
        batch_column_number_in_each_table.append(
            [len(column_infos_in_one_table) for column_infos_in_one_table in column_infos_in_one_db])

        column_info_ids, table_name_ids = [], []

        for table_id, table_name in enumerate(table_names_in_one_db):
            input_tokens.append("|")
            input_tokens.append(table_name)
            table_name_ids.append(len(input_tokens) - 1)
            input_tokens.append(":")

            for column_info in column_infos_in_one_db[table_id]:
                input_tokens.append(column_info)
                column_info_ids.append(len(input_tokens) - 1)
                input_tokens.append(",")

            input_tokens = input_tokens[:-1]

        batch_input_tokens.append(input_tokens)
        batch_column_info_ids.append(column_info_ids)
        batch_table_name_ids.append(table_name_ids)

    tokenized_inputs = tokenizer(
        batch_input_tokens,
        return_tensors="pt",
        is_split_into_words=True,
        padding="max_length",
        max_length=512,
        truncation=True
    )

    batch_aligned_question_ids, batch_aligned_column_info_ids, batch_aligned_table_name_ids = [], [], []

    # align batch_question_ids, batch_column_info_ids, and batch_table_name_ids after tokenizing
    for batch_id in range(batch_size):
        word_ids = tokenized_inputs.word_ids(batch_index=batch_id)

        aligned_question_ids, aligned_table_name_ids, aligned_column_info_ids = [], [], []

        # align question tokens
        for token_id, word_id in enumerate(word_ids):
            if word_id == 0:
                aligned_question_ids.append(token_id)

        # align table names
        for t_id, table_name_id in enumerate(batch_table_name_ids[batch_id]):
            temp_list = []
            for token_id, word_id in enumerate(word_ids):
                if table_name_id == word_id:
                    temp_list.append(token_id)
            # if the tokenizer doesn't discard current table name
            if len(temp_list) != 0:
                aligned_table_name_ids.append(temp_list)
                # aligned_table_labels.append(batch_table_labels[batch_id][t_id])

        # align column names
        for c_id, column_id in enumerate(batch_column_info_ids[batch_id]):
            temp_list = []
            for token_id, word_id in enumerate(word_ids):
                if column_id == word_id:
                    temp_list.append(token_id)

            if len(temp_list) != 0:
                aligned_column_info_ids.append(temp_list)


        batch_aligned_question_ids.append(aligned_question_ids)
        batch_aligned_table_name_ids.append(aligned_table_name_ids)
        batch_aligned_column_info_ids.append(aligned_column_info_ids)


    # update column number in each table (because some tables and columns are discarded)
    for batch_id in range(batch_size):
        if len(batch_column_number_in_each_table[batch_id]) > len(batch_aligned_table_name_ids[batch_id]):
            batch_column_number_in_each_table[batch_id] = batch_column_number_in_each_table[batch_id][
                                                          : len(batch_aligned_table_name_ids[batch_id])]

        if sum(batch_column_number_in_each_table[batch_id]) > len(batch_aligned_column_info_ids[batch_id]):
            truncated_column_number = sum(batch_column_number_in_each_table[batch_id]) - len(
                batch_aligned_column_info_ids[batch_id])
            batch_column_number_in_each_table[batch_id][-1] -= truncated_column_number

    encoder_input_ids = tokenized_inputs["input_ids"]
    encoder_input_attention_mask = tokenized_inputs["attention_mask"]

    if torch.cuda.is_available():
        encoder_input_ids = encoder_input_ids.cuda()
        encoder_input_attention_mask = encoder_input_attention_mask.cuda()

    return encoder_input_ids, encoder_input_attention_mask, \
        batch_aligned_question_ids, \
        batch_aligned_column_info_ids, batch_aligned_table_name_ids, \
        batch_column_number_in_each_table