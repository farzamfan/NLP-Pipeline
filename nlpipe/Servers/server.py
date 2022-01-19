import os
import sys
import logging
import argparse
import tempfile
from flask import Flask
from flask_cors import CORS
from nlpipe.TaskManagers.DatabaseTaskManager import initialize_if_needed
from nlpipe.Servers.helpers import get_token
from nlpipe.Servers.Storage.FileSystemStorage import FileSystemStorage
from nlpipe.Tools.toolsInterface import known_tools
from nlpipe.Workers.worker import run_workers

from nlpipe.Servers.ServerTypes.RESTServer import app_restServer

app = Flask('NLP-Pipeline', template_folder=os.path.dirname(__file__))  # creating the Flask app
CORS(app)  # cross domain access
app.register_blueprint(app_restServer)  # adding the REST server as a blueprint


if __name__ == '__main__':  # main thread starting, mostly reading the arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("directory", nargs="?",
                        help="Location of NLPipe storage directory (default: $nlpipe_DIR or tempdir)")
    parser.add_argument("--workers", "-w", nargs="*", help="Run specified or all known worker modules")
    parser.add_argument("--port", "-p", type=int, default=5001,
                        help="Port number to listen to (default: $nlpipe_PORT or 5001)")
    parser.add_argument("--host", "-H", help="Host address to listen on (default: $nlpipe_HOST or localhost)")
    parser.add_argument("--debug", "-d", help="Set debug mode (implies -v)", action="store_true")
    parser.add_argument("--verbose", "-v", help="Verbose (debug) output", action="store_true")
    parser.add_argument("--disable-authentication", "-A", help="Disable authentication. Only use on firewalled servers",
                        action="store_true")
    parser.add_argument("--print-token", "-T", help="Print authentication token and exit", action="store_true")
    args = parser.parse_args()  # read the arguments from the commandline

    # set up logging
    logging.basicConfig(level=logging.DEBUG if (args.debug or args.verbose) else logging.INFO,
                        format='[%(asctime)s %(name)-12s %(levelname)-5s] %(message)s')

    host = args.host or os.environ.get("nlpipe_HOST", "localhost")
    port = args.port or os.environ.get("nlpipe_PORT", 5001)

    if args.print_token:  # just print the authentication token and exit
        print("Authentication token:\n{}".format(get_token().decode("ascii")))
        sys.exit()

    if not args.directory:  # directory for saving documents
        if "nlpipe_DIR" in os.environ:
            args.directory = os.environ["nlpipe_DIR"]
        else:
            tempdir = tempfile.TemporaryDirectory(prefix="nlpipe_")
            args.directory = tempdir.name

    logging.debug("Serving from {args.directory}".format(**locals()))
    app_restServer.docStorageModule = FileSystemStorage(args.directory)  # add FileSystemStorage to the REST Server

    if args.workers is not None:
        tool_names = args.workers or [m.name for m in known_tools()]
        logging.debug("Starting workers: {module_names}".format(**locals()))
        run_workers(app_restServer, tool_names)  # run the workers

    app_restServer.use_auth = not args.disable_authentication
    if not app_restServer.use_auth:
        logging.warning("** Authentication disabled! **")

    initialize_if_needed()  # set up the queuing and tracking database

    app.run(port=port, host=host, debug=args.debug)  # run the Flask app
