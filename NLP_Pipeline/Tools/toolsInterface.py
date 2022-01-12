from typing import Iterable


class UnknownModuleError(ValueError):
    pass


class Tool(object):
    """Abstract base class for NLPipe modules"""
    name = None

    def check_status(self):
        """Check the status of this module and return an error if not available (e.g. service or tool not found)"""
        raise NotImplementedError()

    def process(self, text):
        """Process the given text and return the result"""
        raise NotImplementedError()

    def convert(self, id, result, format):
        """Convert the given result to the given format (e.g. 'xml'), if possible or raise an exception if not"""
        raise ValueError("Module {self.name} results cannot be converted to {format}".format(**locals()))

    @classmethod
    def register(cls):
        """Register this module in the nlpipe.module.known_modules"""
        register_tool(cls)


def register_tool(tool: Tool):
    """Register this module in the nlpipe.module.known_modules"""
    if tool.name in known_tools:
        raise ValueError("Module with name {module.name} already registered: {}"
                         .format(known_tools[tool.name], **locals()))
    known_tools[tool.name] = tool


def get_tool(name: str) -> Tool:
    """Get a module instance corresponding to the given module name"""
    try:
        module_class = known_tools[name]
    except KeyError:
        raise UnknownModuleError("Unknown module: {name}. Known modules: {}"
                         .format(list(known_tools.keys()), **locals()))
    return module_class()


def get_known_tools() -> Iterable[Tool]:
    """Get all known modules"""
    for name in known_tools:
        yield get_tool(name)


known_tools = {}
