import ast
import json

import torch
import torch.nn as nn
from torch.utils.data import Dataset

from transformers import AutoConfig, RobertaModel, XLMRobertaModel

import requests
class MyClassifier(nn.Module):
    def __init__(
            self,
            model_name_or_path,
            vocab_size,
            mode,
            add_t2c_attn,

    ):
        super(MyClassifier, self).__init__()
        model_class = XLMRobertaModel if "xlm" in model_name_or_path else RobertaModel
        if mode in ["eval", "test"]:
            # load config
            config = AutoConfig.from_pretrained(model_name_or_path)
            # randomly initialize model's parameters according to the config
            self.plm_encoder = model_class(config)
        elif mode == "train":
            self.plm_encoder = model_class.from_pretrained(model_name_or_path)
            self.plm_encoder.resize_token_embeddings(vocab_size)
        else:
            raise ValueError()

        # column cls head
        self.column_info_cls_head_linear1 = nn.Linear(768, 256)
        self.column_info_cls_head_linear2 = nn.Linear(256, 2)

        self.question_info_bilstm = nn.LSTM(
            input_size=768,
            hidden_size=512,
            num_layers=2,
            dropout=0,
            bidirectional=True
        )
        self.question_linear_after_pooling = nn.Linear(1024, 1024)

        # column bi-lstm layer
        self.column_info_bilstm = nn.LSTM(
            input_size=768,
            hidden_size=512,
            num_layers=2,
            dropout=0,
            bidirectional=True
        )

        # linear layer after column bi-lstm layer
        self.column_info_linear_after_pooling = nn.Linear(768, 768)

        # table cls head
        self.table_name_cls_head_linear1 = nn.Linear(768, 256)
        self.table_name_cls_head_linear2 = nn.Linear(256, 2)

        # table bi-lstm pooling layer
        self.table_name_bilstm = nn.LSTM(
            input_size=768,
            hidden_size=512,
            num_layers=2,
            dropout=0,
            bidirectional=True
        )
        # linear layer after table bi-lstm layer
        self.table_name_linear_after_pooling = nn.Linear(768, 768)

        # activation function
        self.leakyrelu = nn.LeakyReLU()
        self.tanh = nn.Tanh()

        # table-column cross-attention layer
        self.add_t2c_attn = add_t2c_attn
        if add_t2c_attn:
            self.table_column_cross_attention_layer = nn.MultiheadAttention(embed_dim=768, num_heads=8)
        else:
            self.table_column_cross_attention_layer = nn.MultiheadAttention(embed_dim=1024, num_heads=8)
        self.table_question_cross_attention_layer = nn.MultiheadAttention(embed_dim=1024, num_heads=8)
        self.column_question_cross_attention_layer = nn.MultiheadAttention(embed_dim=1024, num_heads=8)

        # dropout function, p=0.2 means randomly set 20% neurons to 0
        self.dropout = nn.Dropout(p=0.2)

    def table_column_cross_attention(
            self,
            table_name_embeddings_in_one_db,
            column_info_embeddings_in_one_db,
            column_number_in_each_table
    ):
        table_num = table_name_embeddings_in_one_db.shape[0]
        table_name_embedding_attn_list = []
        for table_id in range(table_num):
            table_name_embedding = table_name_embeddings_in_one_db[[table_id], :]
            column_info_embeddings_in_one_table = column_info_embeddings_in_one_db[
                                                  sum(column_number_in_each_table[:table_id]): sum(
                                                      column_number_in_each_table[:table_id + 1]), :]

            table_name_embedding_attn, _ = self.table_column_cross_attention_layer(
                table_name_embedding,
                column_info_embeddings_in_one_table,
                column_info_embeddings_in_one_table
            )

            table_name_embedding_attn_list.append(table_name_embedding_attn)

        # residual connection
        table_name_embeddings_in_one_db = table_name_embeddings_in_one_db + torch.cat(table_name_embedding_attn_list,
                                                                                      dim=0)
        # row-wise L2 norm
        table_name_embeddings_in_one_db = torch.nn.functional.normalize(table_name_embeddings_in_one_db, p=2.0, dim=1)

        return table_name_embeddings_in_one_db

    def table_column_cls(
            self,
            encoder_input_ids,
            encoder_input_attention_mask,
            batch_aligned_question_ids,
            batch_aligned_column_info_ids,
            batch_aligned_table_name_ids,
            batch_column_number_in_each_table
    ):
        batch_size = encoder_input_ids.shape[0]

        batch_table_name_cls_logits, batch_column_info_cls_logits = [], []
        encoder_output = self.plm_encoder(
            input_ids=encoder_input_ids,
            attention_mask=encoder_input_attention_mask,
            return_dict=True
        )  # encoder_output["last_hidden_state"].shape = (batch_size x seq_length x hidden_size)

        for batch_id in range(batch_size):
            column_number_in_each_table = batch_column_number_in_each_table[batch_id]
            sequence_embeddings = encoder_output["last_hidden_state"][batch_id, :, :]  # (seq_length x hidden_size)
            # obtain the embeddings of tokens in the question
            question_token_embeddings = sequence_embeddings[batch_aligned_question_ids[batch_id], :]

            # obtain table ids for each table
            aligned_table_name_ids = batch_aligned_table_name_ids[batch_id]
            # obtain column ids for each column
            aligned_column_info_ids = batch_aligned_column_info_ids[batch_id]

            table_name_embedding_list, column_info_embedding_list = [], []

            for table_name_ids in aligned_table_name_ids:
                table_name_embeddings = torch.sum(sequence_embeddings[table_name_ids, :], dim=0)
                table_name_embedding_list.append(table_name_embeddings.view(1, 768))
            table_name_embeddings_in_one_db = torch.cat(table_name_embedding_list, dim=0)

            # non-linear mlp layer
            table_name_embeddings_in_one_db = self.leakyrelu(
                self.table_name_linear_after_pooling(table_name_embeddings_in_one_db))

            # obtain column embedding via bi-lstm pooling + a non-linear layer
            for column_info_ids in aligned_column_info_ids:
                column_info_embeddings = torch.sum(sequence_embeddings[column_info_ids, :], dim=0)
                column_info_embedding_list.append(column_info_embeddings.view(1, 768))

            column_info_embeddings_in_one_db = torch.cat(column_info_embedding_list, dim=0)

            # non-linear mlp layer
            column_info_embeddings_in_one_db = self.leakyrelu(
                self.column_info_linear_after_pooling(column_info_embeddings_in_one_db))

            # table-column (tc) cross-attention
            if self.add_t2c_attn:
                table_name_embeddings_in_one_db = self.table_column_cross_attention(
                    table_name_embeddings_in_one_db,
                    column_info_embeddings_in_one_db,
                    column_number_in_each_table
                )

            # calculate table 0-1 logits
            table_name_embeddings_in_one_db = self.table_name_cls_head_linear1(table_name_embeddings_in_one_db)
            table_name_embeddings_in_one_db = self.dropout(self.leakyrelu(table_name_embeddings_in_one_db))
            table_name_cls_logits = self.table_name_cls_head_linear2(table_name_embeddings_in_one_db)

            # calculate column 0-1 logits
            column_info_embeddings_in_one_db = self.column_info_cls_head_linear1(column_info_embeddings_in_one_db)
            column_info_embeddings_in_one_db = self.dropout(self.leakyrelu(column_info_embeddings_in_one_db))
            column_info_cls_logits = self.column_info_cls_head_linear2(column_info_embeddings_in_one_db)

            batch_table_name_cls_logits.append(table_name_cls_logits)
            batch_column_info_cls_logits.append(column_info_cls_logits)

        return batch_table_name_cls_logits, batch_column_info_cls_logits

    def forward(
            self,
            encoder_input_ids,
            encoder_attention_mask,
            batch_aligned_question_ids,
            batch_aligned_column_info_ids,
            batch_aligned_table_name_ids,
            batch_column_number_in_each_table
    ):
        batch_table_name_cls_logits, batch_column_info_cls_logits \
            = self.table_column_cls(
            encoder_input_ids,
            encoder_attention_mask,
            batch_aligned_question_ids,
            batch_aligned_column_info_ids,
            batch_aligned_table_name_ids,
            batch_column_number_in_each_table
        )

        return {
            "batch_table_name_cls_logits": batch_table_name_cls_logits,
            "batch_column_info_cls_logits": batch_column_info_cls_logits
        }

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
        self.all_column_labels: list[list[list[int]]] = []

        self.all_table_names: list[list[str]] = []
        self.all_table_labels: list[list[int]] = []

        data = dataset
        column_names_in_one_db = []
        column_names_original_in_one_db = []
        extra_column_info_in_one_db = []
        column_labels_in_one_db = []

        table_names_in_one_db = []
        table_names_original_in_one_db = []
        table_labels_in_one_db = []

        for table_id in range(len(data["schema_items"])):
            column_names_original_in_one_db.append(data["schema_items"][table_id]["column_names_original"])
            table_names_original_in_one_db.append(data["schema_items"][table_id]["table_name_original"])

            table_names_in_one_db.append(data["schema_items"][table_id]["table_name"])
            # table_labels_in_one_db.append(data["table_labels"][table_id])

            column_names_in_one_db.append(data["schema_items"][table_id]["column_names"])
            # column_labels_in_one_db += data["column_labels"][table_id]

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
        self.all_table_labels.append(table_labels_in_one_db)

        self.all_column_infos.append(column_infos_in_one_db)
        self.all_column_labels.append(column_labels_in_one_db)


    def __len__(self):
        return len(self.questions)


    def __getitem__(self, index):
        question = self.questions[index]

        table_names_in_one_db = self.all_table_names[index]
        table_labels_in_one_db = self.all_table_labels[index]

        column_infos_in_one_db = self.all_column_infos[index]
        column_labels_in_one_db = self.all_column_labels[index]

        return question, table_names_in_one_db, table_labels_in_one_db, column_infos_in_one_db, column_labels_in_one_db




def prepare_batch_inputs_and_labels(batch, tokenizer):
    batch_size = len(batch)
    batch_questions = [data[0] for data in batch]

    batch_table_names = [data[1] for data in batch]
    batch_table_labels = [data[2] for data in batch]

    batch_column_infos = [data[3] for data in batch]
    batch_column_labels = [data[4] for data in batch]

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

    # notice: the trunction operation will discard some tables and columns that exceed the max length
    # print(" ".join(batch_input_tokens[-1]))
    # print(batch_table_names[-1])
    # print(batch_table_labels[-1])
    # print(batch_column_labels[-1])
    # input()
    tokenized_inputs = tokenizer(
        batch_input_tokens,
        return_tensors="pt",
        is_split_into_words=True,
        padding="max_length",
        max_length=512,
        truncation=True
    )

    batch_aligned_question_ids, batch_aligned_column_info_ids, batch_aligned_table_name_ids = [], [], []
    batch_aligned_table_labels, batch_aligned_column_labels = [], []
    batch_start_labels, batch_end_labels = [], []

    # align batch_question_ids, batch_column_info_ids, and batch_table_name_ids after tokenizing
    for batch_id in range(batch_size):
        word_ids = tokenized_inputs.word_ids(batch_index=batch_id)

        aligned_question_ids, aligned_table_name_ids, aligned_column_info_ids = [], [], []
        aligned_table_labels, aligned_column_labels = [], []

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
            # if the tokenizer doesn't discard current column name
            if len(temp_list) != 0:
                aligned_column_info_ids.append(temp_list)
                # aligned_column_labels.append(batch_column_labels[batch_id][c_id])
        # start_labels, end_labels = [], []
        # p, q = 0, 0
        # index = 0

        # while index < len(tokenized_inputs["input_ids"][batch_id]):
        #     if int(tokenized_inputs["input_ids"][batch_id][index]) == 1:
        #         if batch_id==len(batch_input_length):
        #             batch_input_length.append(index)
        #         start_labels.append(-100)
        #         end_labels.append(-100)
        #         index+=1
        #         continue
        #     p = p if p < len(aligned_table_name_ids) else len(aligned_table_name_ids) - 1
        #     q = q if q < len(aligned_column_info_ids) else len(aligned_column_info_ids) - 1
        #     if index in aligned_table_name_ids[p]:
        #         start_labels.append(aligned_table_labels[p])
        #         start_labels += [0 for i in range(len(aligned_table_name_ids[p]) - 1)]
        #         end_labels += [0 for i in range(len(aligned_table_name_ids[p]) - 1)]
        #         end_labels.append(aligned_table_labels[p])
        #         index += len(aligned_table_name_ids[p])
        #         p += 1
        #     elif index in aligned_column_info_ids[q]:
        #         start_labels.append(aligned_column_labels[q])
        #         start_labels += [0 for i in range(len(aligned_column_info_ids[q]) - 1)]
        #         end_labels += [0 for i in range(len(aligned_column_info_ids[q]) - 1)]
        #         end_labels.append(aligned_column_labels[q])
        #         index += len(aligned_column_info_ids[q])
        #         q += 1
        #     else:
        #         start_labels += [0]
        #         end_labels += [0]
        #         index += 1

        # for label,item in zip(aligned_table_labels,aligned_table_name_ids):
        #     if label==1:
        #         assert start_labels[item[0]] == 1 and end_labels[item[-1]] == 1
        #     else:
        #         assert start_labels[item[0]] == 0 and end_labels[item[-1]] == 0
        #
        # for label,item in zip(aligned_column_labels,aligned_column_info_ids):
        #     if label==1:
        #         assert start_labels[item[0]] == 1 and end_labels[item[-1]] == 1
        #     else:
        #         assert start_labels[item[0]] == 0 and end_labels[item[-1]] == 0

        batch_aligned_question_ids.append(aligned_question_ids)
        batch_aligned_table_name_ids.append(aligned_table_name_ids)
        batch_aligned_column_info_ids.append(aligned_column_info_ids)
        # batch_aligned_table_labels.append(aligned_table_labels)
        # batch_aligned_column_labels.append(aligned_column_labels)

        # batch_start_labels.append(start_labels)
        # batch_end_labels.append(end_labels)

    # update column number in each table (because some tables and columns are discarded)
    # 根据截断后的label 确定 列的数量
    # for batch_id in range(batch_size):
    #     if len(batch_column_number_in_each_table[batch_id]) > len(batch_aligned_table_labels[batch_id]):
    #         batch_column_number_in_each_table[batch_id] = batch_column_number_in_each_table[batch_id][
    #                                                       : len(batch_aligned_table_labels[batch_id])]
    #
    #     if sum(batch_column_number_in_each_table[batch_id]) > len(batch_aligned_column_labels[batch_id]):
    #         truncated_column_number = sum(batch_column_number_in_each_table[batch_id]) - len(
    #             batch_aligned_column_labels[batch_id])
    #         batch_column_number_in_each_table[batch_id][-1] -= truncated_column_number

    encoder_input_ids = tokenized_inputs["input_ids"]
    encoder_input_attention_mask = tokenized_inputs["attention_mask"]
    batch_aligned_column_labels = [torch.LongTensor(column_labels) for column_labels in batch_aligned_column_labels]
    batch_aligned_table_labels = [torch.LongTensor(table_labels) for table_labels in batch_aligned_table_labels]

    batch_start_labels = [torch.LongTensor(column_labels) for column_labels in batch_start_labels]
    batch_end_labels = [torch.LongTensor(table_labels) for table_labels in batch_end_labels]

    # print("\n".join(tokenizer.batch_decode(encoder_input_ids, skip_special_tokens = True)))

    if torch.cuda.is_available():
        encoder_input_ids = encoder_input_ids.cuda()
        encoder_input_attention_mask = encoder_input_attention_mask.cuda()
        batch_aligned_column_labels = [column_labels.cuda() for column_labels in batch_aligned_column_labels]
        batch_aligned_table_labels = [table_labels.cuda() for table_labels in batch_aligned_table_labels]

        batch_start_labels = [column_labels.cuda() for column_labels in batch_start_labels]
        batch_end_labels = [table_labels.cuda() for table_labels in batch_end_labels]

    return encoder_input_ids, encoder_input_attention_mask, \
           batch_aligned_column_labels, batch_aligned_table_labels, \
           batch_aligned_question_ids, batch_aligned_column_info_ids, \
           batch_aligned_table_name_ids, batch_column_number_in_each_table, \
           batch_start_labels, batch_end_labels, batch_input_length

def request_schema_linking_result(question,db):
    print(json.dumps(db.to_dict(), indent=4, ensure_ascii=False))
    res = requests.post(f"http://127.0.0.1:18022/v1/schema_linking",
          headers = {
              "Content-Type": "application/json",
              "Authorization": f"Bearer ak_84ff9c1c-4758-494b-b6fd-2f21f06650c3"
          },
          json={
              "model":"schema-linking-base",
              "question":question,
              "db":db.to_dict()
          }).json()

    return res
