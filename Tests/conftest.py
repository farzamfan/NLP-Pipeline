import json
import pytest

import nlpipe.Servers.server


@pytest.fixture()
def app():
    return nlpipe.Servers.server.app
