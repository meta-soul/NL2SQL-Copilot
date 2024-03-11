#!/usr/bin/env python3
import torch


def init_model_args(model_args = None):
    if model_args is None:
        model_args = {}

    model_args['temperature'] = model_args['temperature'] if model_args.get('temperature') != None else 1.0
    model_args['max_tokens'] = model_args['max_tokens'] if model_args.get('max_tokens') != None else 512
    model_args['top_p'] = model_args['top_p'] if model_args.get('top_p') != None else 1.0
    model_args['stop'] = model_args.get('stop', "</s>")
    model_args['start'] = model_args.get('start', "SQL: ")

    if model_args['temperature'] <= 0:
        model_args['temperature'] = 0.001
    if model_args['temperature'] > 1:
        model_args['temperature'] = 1
    if model_args['max_tokens'] > 1024:
        model_args['max_tokens'] = 1024

    return model_args


def do_chat(model, tokenizer, question, history, model_args = None):
    ret = ""
    for char in do_chat_stream(model, tokenizer, question, history, model_args):
        ret += char
    return ret


def do_chat_stream(model, tokenizer, question, history, model_args = None):
    model_args = init_model_args(model_args)

    # TODO: prepend history as prompt
    #for (human, ai) in history:
    #    conv.append_message(conv.roles[0], human)
    #    # NOTE: strip is important to align with the training data.
    #    conv.append_message(conv.roles[1], ai.strip())
    #conv.append_message(conv.roles[0], question)
    #conv.append_message(conv.roles[1], None)
    #prompt = conv.get_prompt()

    generate_stream_func = generate_stream
    prompt = question

    params = {
        "model": model,
        "prompt": prompt,
        "temperature": model_args['temperature'],
        "max_new_tokens": model_args['max_tokens'],
        "top_p": model_args["top_p"],
        "stop": model_args['stop'],
        "stop_ids": model_args.get('stop_ids', [tokenizer.eos_token_id]),
    }

    output_stream = generate_stream_func(model, tokenizer, params, model.running_device,
        context_len=1024, stream_interval=1)

    pre = None
    start_str = model_args.get("start", None)
    for outputs in output_stream:
        # skip tokens until the start
        if start_str is not None:
            if outputs.find(start_str) < 0:
                continue
            elif pre is None:
                pre = outputs.find(start_str) + len(start_str)

        # return the next tokens
        if pre is None:
            yield outputs
        elif len(outputs) > pre:
            yield outputs[pre:]
        pre = len(outputs)


@torch.inference_mode()
def generate_stream(model, tokenizer, params, device, context_len=2048, stream_interval=2):
    prompt = params["prompt"]
    top_p = float(params.get("top_p", 1.0))
    temperature = float(params.get("temperature", 1.0))
    max_new_tokens = int(params.get("max_new_tokens", 256))
    stop_str = params.get("stop", None)
    stop_token_ids = params.get("stop_ids", [tokenizer.eos_token_id])

    input_ids = tokenizer(prompt).input_ids

    output_ids = list(input_ids)
    l_prompt = len(tokenizer.decode(input_ids, skip_special_tokens=False))

    if not model.config.is_encoder_decoder:
        max_src_len = context_len - max_new_tokens - 8
        input_ids = input_ids[-max_src_len:]

    for i in range(max_new_tokens):
        if i == 0:
            if model.config.is_encoder_decoder:
                encoder_outputs = model.encoder(
                    input_ids=torch.as_tensor([input_ids], device=device)
                )
                out = model(
                    torch.as_tensor([input_ids], device=device),
                    decoder_input_ids=torch.as_tensor(
                        [[model.generation_config.decoder_start_token_id]],
                        device=device,
                    ),
                    encoder_outputs=encoder_outputs,
                    use_cache=True,
                )
                logits = out.logits
                past_key_values = out.past_key_values
            else:
                out = model(torch.as_tensor([input_ids], device=device), use_cache=True)
                logits = out.logits
                past_key_values = out.past_key_values
        else:
            if model.config.is_encoder_decoder:
                out = model(
                    input_ids=torch.as_tensor([input_ids], device=device),
                    use_cache=True,
                    encoder_outputs=encoder_outputs,
                    decoder_input_ids=torch.as_tensor([[token]], device=device),
                    past_key_values=past_key_values,
                )
                logits = out.logits
                past_key_values = out.past_key_values
            else:
                out = model(
                    input_ids=torch.as_tensor([[token]], device=device),
                    use_cache=True,
                    past_key_values=past_key_values,
                )
                logits = out.logits
                past_key_values = out.past_key_values

        last_token_logits = logits[0][-1]

        if device == "mps":
            # Switch to CPU by avoiding some bugs in mps backend.
            last_token_logits = last_token_logits.float().to("cpu")

        # TODO: top-p
        #sorted_logits, sorted_indices = torch.sort(last_token_logits, descending=True)
        #cumulative_probs = sorted_logits.softmax(dim=-1).cumsum(dim=-1)
        #indices_to_remove = sorted_indices_to_remove.scatter(1, sorted_indices, sorted_indices_to_remove)
        #scores = scores.masked_fill(indices_to_remove, -float("Inf"))

        token = int(torch.argmax(last_token_logits))
        if temperature > 1e-4:
            probs = torch.softmax(last_token_logits / temperature, dim=-1)
            try:
                # maybe with inf
                token = int(torch.multinomial(probs, num_samples=1))
            except:
                pass

        output_ids.append(token)

        if token in stop_token_ids:
            stopped = True
        else:
            stopped = False

        if i % stream_interval == 0 or i == max_new_tokens - 1 or stopped:
            output = tokenizer.decode(output_ids, skip_special_tokens=False)
            pos = output.rfind(stop_str, l_prompt) if stop_str else -1
            if pos != -1:
                output = output[l_prompt:pos]
                stopped = True
            else:
                output = output[l_prompt:]
            yield output

        if stopped:
            break

    del past_key_values
