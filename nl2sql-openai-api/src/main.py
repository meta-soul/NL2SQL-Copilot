#!/usr/bin/env python
# coding=utf-8
import argparse
import os
import sys

import toml
import uvicorn

from utils import path_prefix_norm


def main():
    parser = argparse.ArgumentParser(
        description='NL2SQL service powered by LLM openai api service.')
    parser.add_argument('--config', type=str, help='Path to the config file',
                        default='conf/config.toml')
    parser.add_argument('--host', type=str, help='Service host.', default='')
    parser.add_argument('--port', type=lambda x: "" if not x else int(x), help='Service port.', default=None)
    parser.add_argument('--tunnel', type=str, help='Remote tunnel for public visit, default not set',
                        default="")
    args = parser.parse_args()

    with open(args.config) as f:
        config = toml.load(f)
    print("> Load config and arguments...")
    print(f"Config file: {args.config}")

    print("> NL2SQL service...")
    from context import context, OpenaiService
    context.host = config['nl2sql']['service']['host']
    context.port = config['nl2sql']['service']['port']
    context.route_prefix = path_prefix_norm(config['nl2sql']['service']['route_prefix'])
    context.services = []
    for name, values in config['openai']['service'].items():
        service = OpenaiService(name, values['type'], values['base_url'], values['timeout'],
                                path_prefix_norm(values['route_prefix']), values['conf'])
        context.services.append(service)
        print(
            f">> name={name}, type={values['type']}, route={context.route_prefix + values['route_prefix']}, model api={values['base_url']}")

    # from app import app
    print(f"> Start NL2SQL server on {args.host or context.host}:{args.port or context.port}...")
    uvicorn.run("app:app", 
        host=args.host or context.host, 
        port=args.port or context.port
    )

    if args.tunnel and args.tunnel in config.get('tunnel', {}):
        print(">> Enable remote tunneling...")
        if args.tunnel == "ngrok":
            print(">>> Start ngrok tunneling...")
            from pyngrok import ngrok, conf
            conf.get_default().region = config['tunnel']['ngrok']['region']
            if config['tunnel']['ngrok']['token']:
                ngrok.set_auth_token(config['tunnel']['ngrok']['token'])
            subdomain = config['tunnel']['ngrok']['subdomain'] or None
            http_tunnel = ngrok.connect(args.port, subdomain=subdomain)
            print(f">>> Public URL: {http_tunnel.public_url}")
        elif args.tunnel == "cloudflare":
            print(">>> Start cloudflare tunnel..")
            from cloudflared import run
            command = config['tunnel']['cloudflare']['cloudflared_path'] \
                      or "cloudflared"
            run(command, config['tunnel']['cloudflare']['name'], args.port)
        else:
            print(">>> Unknown tunneling!")


if __name__ == '__main__':
    main()
