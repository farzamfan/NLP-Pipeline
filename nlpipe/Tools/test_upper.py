"""
Trivial test module that converts to upper case
"""

from nlpipe.Tools.toolsInterface import Tool
import json


class TestUpper(Tool):
    name = "test_upper"

    def check_status(self):
        pass

    def process(self, text):
        return text.upper()  # converts text to uppercase

    def convert(self, doc_id, result, return_format):
        if return_format == "json":
            return json.dumps({"doc_id": doc_id, "status": "OK", "result": result})
        super().convert(result, return_format)


TestUpper.register()  # register the tool in known_tools
