import time
import sys
import subprocess
import logging
from typing import Iterable
from multiprocessing import Process
from pydoc import locate
from nlpipe.Clients import client
from nlpipe.Tools.toolsInterface import Tool as Client
from nlpipe.Tools.toolsInterface import get_tool


class Worker(Process):
    """
    Base class for NLP workers.
    Workers check the server periodically for a NLP task, and if it is assigned to them (based on the tool), they
    request the document, process the documents, and post the results back on the server.
    """

    sleep_timeout = 5  # check the tasks every 5 seconds

    def __init__(self, client, tool, quit=False):
        """
        :param client: a Client object to connect to the NLP Server (e.g., HTTP Client)
        :param tool: The module to perform work on
        :param quit: if True, quit if no jobs are found; if False, poll server every second.
        """
        super().__init__()
        self.client = client
        self.tool = tool
        self.quit = quit

    def run(self):
        while True:
            doc_id, doc = self.client.get_task(self.tool.name)
            if doc_id is None:
                if self.quit:
                    logging.info("No jobs for {self.tool.name}, quitting!".format(**locals()))
                    break
                time.sleep(self.sleep_timeout)
                continue
            logging.info("Received task {self.tool.name}/{doc_id} ({n} bytes)".format(n=len(doc), **locals()))
            try:
                result = self.tool.process(doc)
                self.client.store_result(self.tool.name, doc_id, result)
                logging.debug("Successfully completed task {self.tool.name}/{doc_id} ({n} bytes)"
                              .format(n=len(result), **locals()))
            except Exception as e:
                logging.exception("Exception on parsing {self.module.name}/{id}"
                                  .format(**locals()))
                try:
                    self.client.store_error(self.tool.name, id, str(e))
                except:
                    logging.exception("Exception on storing error for {self.module.name}/{id}"
                                      .format(**locals()))


def _import(name):
    result = locate(name)
    if result is None:
        raise ValueError("Cannot import {name!r}".format(**locals()))
    return result


def run_workers(client: Client, tools: Iterable[str], nprocesses: int = 1, quit: bool = False) -> Iterable[Worker]:
    """
    Run the given workers as separate processes
    :param client: a nlpipe.Clients.ClientInterface object
    :param tools: names of the tools (tools name or fully qualified class name)
    :param nprocesses: Number of processes per tool
    :param quit: If True, workers stop when no jobs are present; if False, they poll the server every second.
    """
    # import built-in workers
    # import nlpipe.modules
    # create and start workers
    result = []  # don't yield, result can be ignored silently
    for tool_class in tools:
        if "." in tool_class:
            tool = _import(tool_class)()
        else:
            tool = get_tool(tool_class)
        for i in range(1, nprocesses + 1):
            logging.debug("[{i}/{nprocesses}] Starting worker {tool}".format(**locals()))
            Worker(client=client, tool=tool, quit=quit).start()
        result.append(tool)

    logging.info("Workers active and waiting for input")
    return result


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("server", help="Server hostname or directory location")
    parser.add_argument("tools", nargs="+", help="Class names of tool(s) to run")
    parser.add_argument("--verbose", "-v", help="Verbose (debug) output", action="store_true", default=False)
    parser.add_argument("--processes", "-p", help="Number of processes per worker", type=int, default=1)
    parser.add_argument("--quit", "-q", help="Quit if no jobs are available", action="store_true", default=False)
    parser.add_argument("--token", "-t", help="Provide auth token"
                                              "(default reads ./.nlpipe_token or NLPIPE_TOKEN")

    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO,
                        format='[%(asctime)s %(name)-12s %(levelname)-5s] %(message)s')

    client = client.get_client(args.server, token=args.token)
    run_workers(client, args.tools, nprocesses=args.processes, quit=args.quit)
