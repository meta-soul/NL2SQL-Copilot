#!/usr/bin/env python
# coding=utf-8
import argparse
import os
import sys

import toml
import uvicorn

from app import app
from models import init_schema_linking_model, download_model
from context import context, ModelFootpoint


def main():
    parser = argparse.ArgumentParser(
        description='Start Schema linking models as a service.')

    parser.add_argument('--config', type=str, help='Path to the config file',
                        default='conf/config.toml')
    parser.add_argument('--device', type=str,
                        help='Device to run the service, gpu/cpu/mps',
                        default='gpu')
    parser.add_argument('--gpus', type=int, help='Use how many gpus, default 1',
                        default=1)
    parser.add_argument('--host', type=str, help='Service host.', default="")
    parser.add_argument('--port', type=int, help='Port number to run the service',
                        default=None)

    args = parser.parse_args()

    print("> Load config and arguments...")
    print(f"Device: {args.device}")
    print(f"Port: {args.port}")
    print(f"Config file: {args.config}")

    with open(args.config) as f:
        config = toml.load(f)
        print(f"Config: \n{config}")

    # Add auth access tokens
    context.auth_tokens = config['auth']['tokens']
    context.service_args = config["service"]["base_args"]
    context.result_args = config["service"]["result_args"]

    # Load schema_linking_model
    for schema_linking_model_name in config['models']['schema-linking'].keys():
        schema_linking_model_args = config['models']['schema-linking'][schema_linking_model_name]

        if schema_linking_model_args["path"].startswith("https://") or schema_linking_model_args["path"].startswith("http://"):
            local_path = download_model(schema_linking_model_name, schema_linking_model_args["path"], 
                context.service_args.get("cache_dir", "./.cache"))
            if not local_path:
                print(f"> [Warning] Load schema_linking_models model {schema_linking_model_name}, download failed!")
                continue
            else:
                print(f"> Load schema_linking_models model {schema_linking_model_name}")
                schema_linking_model_args["path"] = local_path

        tokenizer, model = init_schema_linking_model(schema_linking_model_args["path"],
            args.device, args.gpus, **schema_linking_model_args.get('model_args', {}))

        context.schema_linking_model[schema_linking_model_args['name']] = ModelFootpoint(
            schema_linking_model_args['name'],
            "schema-linking",
            model, 
            tokenizer, 
            schema_linking_model_args.get('tags', [])
        )
        print(f"> Load DONE!"

    # Start server and tunneling
    print(f"> Start API server on port[{args.port}]...")
    host = args.host or context.service_args["host"]
    port = args.port or context.service_args["port"]
    uvicorn.run(app, host=host, port=port)


if __name__ == '__main__':
    main()
