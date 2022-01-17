import json
import logging
from functools import wraps
from flask import Blueprint, request, make_response, Response, jsonify
from flask.templating import render_template

from nlpipe.Servers.Storage.DatabaseStorage import Task

from nlpipe.Tools.toolsInterface import UnknownModuleError, get_tool, known_tools
from nlpipe.Servers.helpers import STATUS_CODES, ERROR_MIME, do_check_auth, LoginFailed

"""
NLPipe REST Server that manages the direct filesystem access (e.g. on local machine or over NFS)
"""
app_restServer = Blueprint('app_restServer', __name__)


# will throw exception if not valid
def check_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if app_restServer.use_auth:
            try:
                do_check_auth()
            except LoginFailed as e:
                return "Login Failed: {e}\n".format(**locals()), 403
        return f(*args, **kwargs)
    return decorated_function


@app_restServer.route('/checktoken', methods=['HEAD', 'GET'])
@check_auth
def check_token(token):
    return "Authentication {}\n".format("OK" if app_restServer.use_auth else "disabled"), 200


@app_restServer.route('/')
def index():
    fsdir = app_restServer.docStorageModule.result_dir
    mods = sorted(known_tools(), key=lambda mod: mod.name)
    mods = {mod: dict(app_restServer.docStorageModule.statistics(mod.name)) for mod in mods}
    return render_template('index.html', **locals())


@app_restServer.route('/api/tools/<tool>/', methods=['POST'])
@check_auth
def post_task(tool):
    """
    POST a new task to the NLPipe server.
    Post body should contain the text/doc to process.
    You can specify an explicit document id with ?id=<id>
    Response will be an empty HTTP 202 response with Location and ID headers

    :param tool: The name of the tool to process with
    """
    try:
        get_tool(tool)  # check if tool exists
    except UnknownModuleError as e:
        return str(e), 404

    doc = request.get_data().decode('UTF-8')  # get the document
    task_id = Task.insert({'tool': tool, 'docs': doc, 'status': "PENDING"}).execute()  # adding the task to db
    doc_id = app_restServer.docStorageModule.process(tool,
                                                     doc, doc_id=request.args.get("id"),  # in case it is given
                                                     task_id=task_id)  # stores the doc, and if needed generates the id
    resp = Response(doc_id + "\n", status=202)  # create a response object
    resp.headers['Location'] = '/api/tools/{tool}/{doc_id}'.format(**locals())  # endpoint to access doc
    resp.headers['TASK_ID'] = task_id  # add task_id to the response header
    resp.headers['ID'] = doc_id  # add id to the response header
    return resp  # return a response to the use


@app_restServer.route('/api/tools/<tool>/<id>', methods=['HEAD'])
@check_auth
def doc_status(tool, id):
    """
    HEAD gets the status of a document as HTTP Status code.
    Response will also contain a status header.
    :param tool: The module name
    :param id: ID of the document to get status for
    """
    status = app_restServer.docStorageModule.status(tool, id)
    resp = Response(status=STATUS_CODES[status])
    resp.headers['Status'] = status
    return resp


@app_restServer.route('/api/tasks/<task_id>', methods=['HEAD'])
@check_auth
def task_status(task_id):
    """
    HEAD gets the status of a task as HTTP Status code.
    Response will also contain a status header.

    :param task_id: ID of the task to get status for
    """
    status = Task.get(Task.id == task_id).status
    resp = Response(status=STATUS_CODES[status])
    resp.headers['Status'] = status
    return resp


@app_restServer.route('/api/tools/<tool>/<doc_id>', methods=['GET'])
@check_auth
def result(tool, doc_id):
    """
    GET the processed result of a task.
    If processed OK, returns the result as document with HTTP 200
    If processing failed, returns HTTP 500 with a json document containing the exception
    If task is unknown or not yet processed, will return 404

    :param tool: The tool name
    :param doc_id: ID of the task to get result for
    """
    return_format = request.args.get('format', None)
    try:
        res = app_restServer.docStorageModule.result(tool, doc_id, return_format=return_format)
    except FileNotFoundError:
        return 'Error: Unknown document: {tool}/{id}\n'.format(**locals()), 404
    except Exception as e:
        res = {"exception_class": type(e).__name__, "message": str(e)}
        return make_response(jsonify(result), 500)
    return res, 200


@app_restServer.route('/api/tools/<tool>/', methods=['GET'])
@check_auth
def get_task(tool):
    """
    GET a task to process.
    This is intended to be called by a worker and will set status of the task to STARTED.
    Returns the text to process with HTTP headers ID and Location

    :param tool: tool name
    """
    doc_id, doc = app_restServer.docStorageModule.get_task(tool)  # get the doc_id and the document

    if doc is None:  # document does not exist
        return 'Queue {tool} empty!\n'.format(**locals()), 404

    resp = Response(doc, status=200)  # attach the document (unprocessed at this point) to the response
    resp.headers['Location'] = '/api/tools/{tool}/{doc_id}'.format(**locals())  # endpoint for the document
    resp.headers['ID'] = doc_id  # document id in the database (queuing system)
    return resp


@app_restServer.route('/api/tools/<tool>/<doc_id>', methods=['PUT'])
@check_auth
def put_results(tool, doc_id):
    """
    PUT the results of processing.
    If processing failed, use Content-type: prs.error+text and put the error message or diagnostics
    This is intended to be called by a worker and will set the status of the task to DONE or ERROR.

    :param tool: name of the tool
    :param doc_id: id of the document
    :return:
    """
    doc = request.get_data().decode('UTF-8')
    if request.content_type == ERROR_MIME:
        app_restServer.docStorageModule.store_error(tool, doc_id, doc)
    else:
        app_restServer.docStorageModule.store_result(tool, doc_id, doc)
    return '', 204


# @app_restServer.route('/api/modules/<module>/bulk/status', methods=['POST'])
# @check_auth
# def bulk_status(module):
#     """
#     Bulk method: POST a json list of IDs to get status information from.
#     Returns a json dict of {id: status}
#
#     :param module: The module name
#     """
#     try:
#         ids = request.get_json(force=True)
#         if not ids:
#             raise ValueError("Empty request")
#     except:
#         return "Error: Please provive bulk IDs as a json list\nd ", 400
#     statuses = {id: app_restServer.docStorageModule.status(module, str(id)) for id in ids}
#     return json.dumps(statuses, indent=4), 200
#
#
# @app_restServer.route('/api/modules/<module>/bulk/result', methods=['POST'])
# @check_auth
# def bulk_result(module):
#     """
#     Bulk method: POST a json list of IDs to get results for.
#     Returns a json dict of {id: result}
#
#     :param module: The module name
#     """
#     try:
#         ids = request.get_json(force=True)
#         if not ids:
#             raise ValueError("Empty request")
#     except:
#         return "Error: Please provive bulk IDs as a json list\nd ", 400
#     format = request.args.get('format', None)
#     results = app_restServer.docStorageModule.bulk_result(module, ids, format=format)
#     return jsonify(results)
#
#
# @app_restServer.route('/api/modules/<module>/bulk/process', methods=['POST'])
# @check_auth
# def bulk_process(module):
#     """
#     Bulk method: POST a json list or {id: text} dict containing texts to process
#     Returns a json list of ids
#
#     :param module: The module name
#     """
#     reset_error = request.args.get('reset_error', False) in ('1', 'Y', 'True')
#     reset_pending = request.args.get('reset_pending', False) in ('1', 'Y', 'True')
#     try:
#         docs = request.get_json(force=True)
#         if not docs:
#             raise ValueError("Empty request")
#     except:
#         logging.exception("bulk/process: Error parsing json {}".format(repr(request.data)[:20]))
#         return "Error: Please provive bulk docs as a json list or {id:doc, } dict\n ", 400
#     if isinstance(docs, list):
#         docs, ids = docs, None
#     else:
#         docs, ids = docs.values(), docs.keys()
#     ids = app_restServer.docStorageModule.bulk_process(module, docs, ids=ids,
#                                                        reset_error=reset_error, reset_pending=reset_pending)
#     return jsonify(ids)
