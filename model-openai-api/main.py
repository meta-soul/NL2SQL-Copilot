#!/usr/bin/env python
# coding=utf-8
import argparse
import os
import sys

import toml
import uvicorn

from app import app
from models import init_chatglm, init_seq2seq, init_embeddings_model, download_model
from context import context, ModelFootpoint


def main():
    parser = argparse.ArgumentParser(
        description='Start LLM and Embeddings models as a service.')

    parser.add_argument('--config', type=str, help='Path to the config file',
                        default='conf/config.toml')
    parser.add_argument('--llm_model', type=str, help='Choosed LLM models, multiple models split by ,',
                        default='chatglm-6b-int4')
    parser.add_argument('--emb_model', type=str,
                        help='Choosed embeddings model, multiple models split by ,',
                        default='')
    parser.add_argument('--device', type=str,
                        help='Device to run the service, gpu/cpu/mps',
                        default='gpu')
    parser.add_argument('--gpus', type=int, help='Use how many gpus, default 1',
                        default=1)
    parser.add_argument('--host', type=str, help='Service host',
                        default="")
    parser.add_argument('--port', type=int, help='Port number to run the service',
                        default=None)

    args = parser.parse_args()

    print("> Load config and arguments...")
    print(f"Language Models: {args.llm_model}")
    print(f"Embedding Models: {args.emb_model}")
    print(f"Device: {args.device}")
    print(f"GPUs: {args.gpus}")
    print(f"Port: {args.port}")
    print(f"Config file: {args.config}")

    with open(args.config) as f:
        config = toml.load(f)
        print(f"Config: \n{config}")
    
    context.host = config['service']['host']
    context.port = config['service']['port']
    context.cache_dir = config['service']['cache_dir']
    os.makedirs(context.cache_dir, exist_ok=True)

    # Add auth access tokens
    context.auth_tokens = config['auth']['tokens']
    assert len(context.auth_tokens) > 0, "Auth tokens are empty!"

    # Load LLM models
    if args.llm_model.strip():
        llm_models = [m.strip() for m in args.llm_model.split(',') if m.strip()]
        for llm_model in llm_models:
            print(f"> Load LLM model {llm_model}")

            if llm_model not in config['models']['llm']:
                print(f">> [Warning] LLM model {llm_model} not found in config file!")
                continue

            tokenizer, model = None, None
            llm = config['models']['llm'][llm_model]
            if llm['path'].startswith("https://") or llm['path'].startswith("http://"):
                local_path = download_model(llm_model, llm['path'], context.cache_dir)
                if not local_path:
                    print(f">> [Warning] LLM model {llm_model} download via url failed!!")
                    continue
                else:
                    print(f">> Download LLM model {llm_model} into {local_path}")
                    llm['path'] = local_path

            if llm['type'] == 'chatglm':
                print(f">> Use chatglm llm model {llm['path']}")
                tokenizer, model = init_chatglm(
                    llm['path'], args.device, args.gpus, 
                    cache_dir=context.cache_dir, **llm.get('kwargs', {}))
            elif llm['type'] == 'seq2seq':
                print(f">> Use seq2seq llm model {llm['path']}")
                tokenizer, model = init_seq2seq(
                    llm['path'], args.device, args.gpus, 
                    cache_dir=context.cache_dir, **llm.get('kwargs', {}))
            else:
                print(f">> [Warning] Unsupported LLM model type {llm['type']}")
                continue

            context.llm_models[llm['name']] = ModelFootpoint(llm['name'], llm['type'],
                model, tokenizer, llm.get('tags', []), llm.get('gen_kwargs', {}))
            print(f">> Load DONE!")


    # Load embedding models
    if args.emb_model:
        emb_models = [m.strip() for m in args.emb_model.split(',') if m.strip()]
        for emb_model in emb_models:
            print(f"> Start Embeddings model {emb_model}")

            if emb_model not in config['models']['embeddings']:
                print(f">> [Warning] Embeddings model {emb_model} not found in config file")
                continue

            embeddings_model = None
            embeddings = config['models']['embeddings'][emb_model]
            if embeddings['type'] == 'default':
                print(f">> Use default embeddings model {embeddings['path']}")
                embeddings_model = init_embeddings_model(
                    embeddings['path'], args.device, **embeddings.get('kwargs', {}))
            else:
                print(f">> [Warning] Unsupported Embeddings model type {embeddings['type']}")
                continue

            context.emb_models[embeddings['name']] = ModelFootpoint(embeddings['name'],
                embeddings['type'], embeddings_model, None, embeddings.get('tags', []))


    # Start server and tunneling
    print(f"> Start API server on port[{args.port or context.port}]...")
    uvicorn.run(app, 
        host=args.host or context.host, 
        port=args.port or context.port
    )


if __name__ == '__main__':
    main()
