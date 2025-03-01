#!/usr/bin/env python3

from argparse import ArgumentParser, Namespace
from time import monotonic
from json import dumps as jdumps
import requests

def get_args()->Namespace:
    ap = ArgumentParser()
    ap.add_argument("-H", "--host", type=str, default="http://localhost:11434", help="[%(default)s]")
    ap.add_argument('-L', '--list-models', default=False, action='store_true')
    ap.add_argument('-R', '--show-response', default=False, action='store_true')

    
    mxp = ap.add_mutually_exclusive_group()
    mxp.add_argument('-l', '--long-prompt', dest='prompt', action='store_true')
    mxp.add_argument('-s', '--short-prompt', dest='prompt', action='store_false')
    mxp.add_argument('-p', '--prompt', type=str)

    mxm = ap.add_mutually_exclusive_group()
    mxm.add_argument('-m', '--model', type=str, default=None)
    mxm.add_argument('-a', '--all', dest='model', action='store_true')

    rv = ap.parse_args()
    if rv.prompt in [None, False]:
        rv.prompt = 'count from 1 to 100'
    elif rv.prompt is True:
        rv.prompt = 'tell me about the trolley problem'

    return rv

def test_model(args:Namespace, model:str)->None:
    payload = {
            'model': model,
            'prompt': args.prompt,
            'stream': False,
            }
    payload_data = jdumps(payload)
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    print(f"{model} ", end='', flush=True)
    t_start = monotonic()
    resp = requests.post(f'{args.host}/api/generate', data=payload_data, headers=headers)
    req_time = monotonic() - t_start
    resp_data = resp.json()
    resp_data.pop('context', None)

    try:
        ntk = resp_data['eval_count']
        dur = resp_data['eval_duration']
        tps = ntk / dur * 1e9
    except KeyError:
        print(resp_data)
        tps = -1

    print(f"httptime {req_time:.2f}s {tps:.3f} token/sec")
    if args.show_response and tps > 0:
        print(resp_data['response'])

def main()->None:
    args = get_args()

    resp = requests.get(f'{args.host}/v1/models').json()
    models = [x['id'] for x in resp['data']]
    resp = requests.get(f'{args.host}/api/ps').json()
    loaded = [x['name'].replace('"', '') for x in resp['models']]

    if args.list_models:
        print(f"Loaded: {loaded}")
        print(f"Models: {models}")
        exit()

    if args.model is None:
        if loaded:
            args.model = loaded[0]
        else:
            print("No model specified, and no model is loaded")
            exit()


    if args.model is True:
        for model in models:
            test_model(args, model)
    else:
        test_model(args, args.model)

if __name__ == '__main__':
    main()
