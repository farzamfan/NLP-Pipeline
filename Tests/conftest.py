import json
import pytest

import NLP_Pipeline.Servers.server


@pytest.fixture()
def app():
    return NLP_Pipeline.Servers.server.app
