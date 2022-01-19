import logging
import os
import argparse
import sys
from nlpipe.Clients.HTTPClient import HTTPClient


def get_client(server_name, token=None):
    """
    Returns a client (for now only HTTP client)

    :param server_name: address of the server (URL)
    :param token: authentication token
    :return: initialized HTTP client
    """
    if server_name.startswith("http:") or server_name.startswith("https:"):  # if the server is remote
        logging.getLogger('requests').setLevel(logging.WARNING)  # logging
        if not token:
            token = os.environ.get('NLPIPE_TOKEN', None)  # authentication token
        logging.debug("Connecting to REST server at {server_name} using token={}".format(bool(token), **locals()))
        return HTTPClient(server_name, token=token)


if __name__ == '__main__':  # if run as a module

    parser = argparse.ArgumentParser()
    parser.add_argument("server", help="Server hostname or directory location")
    parser.add_argument("tool", help="Tool name")  # NLP processing tool
    parser.add_argument("--verbose", "-v", help="Verbose (debug) output", action="store_true", default=False)
    parser.add_argument("--token", "-t", help="Provide auth token"
                                              "(default reads ./.nlpipe_token or NLPIPE_TOKEN")

    action_parser = parser.add_subparsers(dest='action', title='Actions')  # parser for actions
    action_parser.required = True

    actions = {name: action_parser.add_parser(name)  # add possible actions
               for name in ('doc_status', 'result', 'check', 'process', 'process_inline',
                            'bulk_status', 'bulk_result', 'store_result', 'store_error')}

    for action in 'doc_status', 'result', 'store_result', 'store_error':
        actions[action].add_argument('doc_id', help="Document ID")
    for action in 'bulk_status', 'bulk_result':
        actions[action].add_argument('ids', nargs="+", help="Document IDs")
    for action in 'result', 'process_inline', 'bulk_result':
        actions[action].add_argument("--return_format", help="Optional output format to retrieve")  # return format
    for action in 'process', 'process_inline':
        actions[action].add_argument('doc', help="Document to process (use - to read from stdin")
        actions[action].add_argument('doc_id', nargs="?", help="Optional explicit document ID")
    for action in ('store_result', 'store_error'):
        actions[action].add_argument('result', help="Document to store (use - to read from stdin")

    args = vars(parser.parse_args())  # turn to dict so we can pop and pass the rest as kargs

    logging.basicConfig(level=logging.DEBUG if args.pop('verbose', False) else logging.INFO,
                        format='[%(asctime)s %(name)-12s %(levelname)-5s] %(message)s')

    client = get_client(args.pop('server'), token=args.pop('token', None))  # add HTTP client

    for doc_arg in ('doc', 'result'):
        if args.get(doc_arg) == '-':
            args[doc_arg] = sys.stdin.read()

    action = args.pop('action')  # requested action
    args = {k: v for (k, v) in args.items() if v}
    result = getattr(client, action)(**args)  # run the action via the HTTP client

    if action == "get_task":  # in case a task is given
        doc_id, doc = result
        if doc_id is not None:
            print(doc_id, file=sys.stderr)
            print(doc)
    elif action in ("store_result", "store_error"):
        pass
    else:
        if result is not None:
            print(result)
