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
        return text.upper()

    def convert(self, id, result, format):
        if format == "json":
            return json.dumps({"id": id, "status": "OK", "result": result})
        super().convert(result, format)


TestUpper.register()
