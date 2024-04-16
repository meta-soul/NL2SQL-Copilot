import os
import re
import time
from copy import deepcopy
from fastapi import APIRouter
from fastapi import FastAPI, HTTPException, Request, status, BackgroundTasks
from fastapi.responses import JSONResponse

from context import context
from api.auth import check_token
from api.model import SchemaLinkingBody
from api.response import generate_schema_linking_response
from utils import torch_gc


import torch
from torch.utils.data import DataLoader
from ..utils import ColumnAndTableClassifierDataset,prepare_batch_inputs_and_labels,normal

import requests

router = APIRouter()


@router.post("/v1/schema_linking")
async def schema_linking(body: SchemaLinkingBody, request: Request, background_tasks: BackgroundTasks):
    background_tasks.add_task(torch_gc)
    start_time = time.time()
    if not context.service_args["public"]:
        check_token(request.headers, context.auth_tokens)

    if not context.schema_linking_model:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Schema Linking model model not load!")

    if body.model not in context.schema_linking_model:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Schema Linking model not found!")

    model_point = context.schema_linking_model[body.model]
    model = model_point.model


    tokenizer = model_point.tokenizer

    question = body.question
    db = body.db
    schema_linking_db = normal(question=question,db=db)
    total_table_pred_probs, total_column_pred_probs= get_schema_linking_result(schema_linking_db,model,tokenizer)

    # record predicted probability
    truncated_data_info = []
    # 表数量
    table_num = len(schema_linking_db["schema_items"])
    # 获得每个表的概率
    if table_num == len(total_table_pred_probs):
        table_pred_probs = total_table_pred_probs
    else:
        table_pred_probs = total_table_pred_probs + [-1 for _ in range(
            table_num - len(total_table_pred_probs))]
    truncated_table_ids = []
    already_truncated_table_ids = set()
    column_pred_probs = []
    # 因为序列长度有限 导致预测的表数量和数据中表数量不一致
    # 得到被截断的表id和column概率
    for table_id in range(table_num):
        if table_id >= len(total_column_pred_probs):
            truncated_table_ids.append(table_id)
            column_pred_probs.append([-1 for _ in range(len(schema_linking_db["schema_items"][table_id]["column_names"]))])
            continue
        if len(total_column_pred_probs[table_id]) == len(schema_linking_db["schema_items"][table_id]["column_names"]):
            column_pred_probs.append(total_column_pred_probs[table_id])
        else:
            truncated_table_ids.append(table_id)
            truncated_column_num = len(schema_linking_db["schema_items"][table_id]["column_names"]) - len(
                    total_column_pred_probs[table_id])
            column_pred_probs.append(
                    total_column_pred_probs[table_id] + [-1 for _ in range(truncated_column_num)])

    schema_linking_db["column_pred_probs"] = column_pred_probs
    schema_linking_db["table_pred_probs"] = table_pred_probs

    window_num_tables = 5
    for truncated_i in range(len(truncated_table_ids)):
        truncated_tables = truncated_table_ids[truncated_i:truncated_i+window_num_tables]
        truncated_data = deepcopy(schema_linking_db)
        truncated_data["schema_items"] = [truncated_data["schema_items"][table_id] for table_id in
                                       truncated_tables]

        truncated_data["table_pred_probs"] = [truncated_data["table_pred_probs"][table_id] for table_id in
                                              truncated_tables]
        truncated_data["column_pred_probs"] = [truncated_data["column_pred_probs"][table_id] for table_id in
                                               truncated_tables]

        total_table_pred_probs, total_column_pred_probs = get_schema_linking_result(truncated_data,model,tokenizer)

        table_num = len(truncated_data["schema_items"])
        if table_num == len(total_table_pred_probs):
            table_pred_probs = total_table_pred_probs
        else:
            table_pred_probs = total_table_pred_probs + [-1 for _ in range(
                table_num - len(total_table_pred_probs))]

        column_pred_probs = []
        for table_id in range(table_num):
            if table_id >= len(total_column_pred_probs):
                column_pred_probs.append([-1 for _ in range(len(truncated_data["schema_items"][table_id]["column_names"]))])
                continue
            if len(total_column_pred_probs[table_id]) == len(truncated_data["schema_items"][table_id]["column_names"]):
                column_pred_probs.append(total_column_pred_probs[table_id])
            else:
                truncated_column_num = len(truncated_data["schema_items"][table_id]["column_names"]) - len(
                        total_column_pred_probs[table_id])
                column_pred_probs.append(
                        total_column_pred_probs[table_id] + [-1 for _ in range(truncated_column_num)])

        for idx, truncated_table_id in enumerate(truncated_tables):
            schema_linking_db["table_pred_probs"][truncated_table_id] = table_pred_probs[idx]
            schema_linking_db["column_pred_probs"][truncated_table_id] = column_pred_probs[idx]


    #if len(truncated_table_ids) > 0:
    #    truncated_data_info = [0, truncated_table_ids]

    ## 对输入截断的表，列进行预测
    ## additionally, we need to consider and predict discarded tables and columns
    ## 有一种情况无法跳出循环 逻辑对截断部分的概率置为-1 然后将截断部分拼接重新判断 当某表及其列长度大于512时 末尾列总是-1 需要一直判断
    #while len(truncated_data_info) != 0:
    #    truncated_data = deepcopy(schema_linking_db)
    #    # 被截断的db——schema
    #    truncated_data["schema_items"] = [truncated_data["schema_items"][table_id] for table_id in
    #                                   truncated_table_ids]

    #    truncated_data["table_pred_probs"] = [truncated_data["table_pred_probs"][table_id] for table_id in
    #                                          truncated_table_ids]
    #    truncated_data["column_pred_probs"] = [truncated_data["column_pred_probs"][table_id] for table_id in
    #                                           truncated_table_ids]

    #    total_table_pred_probs, total_column_pred_probs = get_schema_linking_result(truncated_data,model,tokenizer)
    #    #already_truncated_table_ids.update(truncated_table_ids)

    #    table_num = len(truncated_data["schema_items"])
    #    if table_num == len(total_table_pred_probs):
    #        table_pred_probs = total_table_pred_probs
    #    else:
    #        table_pred_probs = total_table_pred_probs + [-1 for _ in range(
    #            table_num - len(total_table_pred_probs))]

    #    column_pred_probs = []
    #    for table_id in range(table_num):
    #        if table_id >= len(total_column_pred_probs):
    #            column_pred_probs.append([-1 for _ in range(len(truncated_data["schema_items"][table_id]["column_names"]))])
    #            continue
    #        if len(total_column_pred_probs[table_id]) == len(truncated_data["schema_items"][table_id]["column_names"]):
    #            column_pred_probs.append(total_column_pred_probs[table_id])
    #        else:
    #            truncated_column_num = len(truncated_data["schema_items"][table_id]["column_names"]) - len(
    #                    total_column_pred_probs[table_id])
    #            column_pred_probs.append(
    #                    total_column_pred_probs[table_id] + [-1 for _ in range(truncated_column_num)])

    #    for idx, truncated_table_id in enumerate(truncated_table_ids):
    #        schema_linking_db["table_pred_probs"][truncated_table_id] = table_pred_probs[idx]
    #        schema_linking_db["column_pred_probs"][truncated_table_id] = column_pred_probs[idx]

    #    # check if there are tables and columns in the new dataset that have not yet been predicted
    #    truncated_data_info = []
    #    table_num = len(schema_linking_db["schema_items"])
    #    truncated_table_ids = []
    #    for table_id in range(table_num):
    #        # the current table is not predicted
    #        if schema_linking_db["table_pred_probs"][table_id] == -1:
    #            truncated_table_ids.append(table_id)
    #        # some columns in the current table are not predicted
    #        if schema_linking_db["table_pred_probs"][table_id] != -1 and -1 in schema_linking_db["column_pred_probs"][table_id]:
    #            truncated_table_ids.append(table_id)
    #        if len(truncated_table_ids) > 0:
    #                truncated_data_info.append([0, truncated_table_ids])

    final_schema_link_tables, final_schema_link_columns = [], []
    all_tables, all_columns = [], []

    table_threshold = body.table_threshold if body.table_threshold!=-1 else context.result_args["table_threshold"]
    column_threshold = body.column_threshold if body.column_threshold !=-1 else context.result_args["column_threshold"]
    show_table_nums = body.show_table_nums if body.show_table_nums !=-1 else context.result_args["show_table_nums"]
    show_column_nums = body.show_column_nums if body.show_column_nums !=-1 else context.result_args["show_column_nums"]
    sort_table_and_columns = body.sort if body.sort is not None else context.result_args["sort"]

    for table_pred_prob, column_pred_probs, schema_item in zip(schema_linking_db["table_pred_probs"],
                                                               schema_linking_db["column_pred_probs"],
                                                               schema_linking_db["schema_items"]):
        table_name = schema_item["table_name_original"]
        # remove irrevelant tables
        if re.match(r'^\d+', table_name):
            continue
        # table_name = schema_item["table_name"]
        all_tables.append(table_name)
        schema_link_columns = []

        if table_pred_prob > table_threshold:
            final_schema_link_tables.append((table_name,table_pred_prob))
            for column_name, column_pred_prob in zip(schema_item["column_names"], column_pred_probs):
                all_columns.append((column_name,column_pred_prob))
                if column_pred_prob > column_threshold:
                    schema_link_columns.append((column_name,column_pred_prob))
                    if len(schema_link_columns)==show_column_nums:
                        break
            if sort_table_and_columns:
                schema_link_columns=sorted(schema_link_columns, key=lambda x: x[1], reverse=True)
        final_schema_link_columns.append(schema_link_columns)
        if len(final_schema_link_tables)==show_table_nums:
            break

    if sort_table_and_columns:
        final_schema_link_tables=sorted(final_schema_link_tables, key=lambda x: x[1],reverse=True)

    show_schema_link_tables = [item[0] for item in final_schema_link_tables]
    show_schema_link_columns=[]
    for schema_link_columns in final_schema_link_columns:
        show_schema_link_columns.append([item[0] for item in schema_link_columns])


    data = []
    data.append({
            "object": "schema_linking",
            "index": 0,
            "final_schema_link_tables": show_schema_link_tables,
            "final_schema_link_columns": show_schema_link_columns,
        })

    print(">> Schema Linking Tables", len(schema_linking_db["schema_items"]), "->", len(show_schema_link_tables))
    print(">> Schema Linking Results", [x['table_name'] for x in schema_linking_db["schema_items"]], "->", final_schema_link_tables)
    print(">> Response: {}".format(generate_schema_linking_response(data, model=body.model)))
    print(">> During {}s".format(time.time()-start_time))

    return JSONResponse(status_code=200, content=generate_schema_linking_response(data, model=body.model))


def get_schema_linking_result(schema_linking_db: dict,model,tokenizer):

    dataset = ColumnAndTableClassifierDataset(
        dataset=schema_linking_db,
        use_contents=False,
        add_fk_info=True
    )

    dataloder = DataLoader(
        dataset,
        batch_size=1,
        shuffle=False,
        collate_fn=lambda x: x
    )
    model.eval()
    returned_table_pred_probs, returned_column_pred_probs = [], []
    for batch in dataloder:
        encoder_input_ids, encoder_input_attention_mask, \
        batch_aligned_question_ids, \
        batch_aligned_column_info_ids, batch_aligned_table_name_ids, \
        batch_column_number_in_each_table = prepare_batch_inputs_and_labels(
            batch, tokenizer)

        with torch.no_grad():
            model_outputs = model(
                encoder_input_ids,
                encoder_input_attention_mask,
                batch_aligned_question_ids,
                batch_aligned_column_info_ids,
                batch_aligned_table_name_ids,
                batch_column_number_in_each_table
            )

        for batch_id, table_logits in enumerate(model_outputs["batch_table_name_cls_logits"]):
            table_pred_probs = torch.nn.functional.softmax(table_logits, dim=1)
            returned_table_pred_probs.append(table_pred_probs[:, 1].cpu().tolist())

        for batch_id, column_logits in enumerate(model_outputs["batch_column_info_cls_logits"]):
            column_number_in_each_table = batch_column_number_in_each_table[batch_id]
            column_pred_probs = torch.nn.functional.softmax(column_logits, dim=1)
            returned_column_pred_probs.append([column_pred_probs[:, 1].cpu().tolist()[
                                               sum(column_number_in_each_table[:table_id]):sum(
                                                   column_number_in_each_table[:table_id + 1])] \
                                               for table_id in range(len(column_number_in_each_table))])
        return returned_table_pred_probs[0], returned_column_pred_probs[0]

