# Copyright (c) 2025 Flowdacity Team. See LICENSE.txt for details.
# ASGI application entrypoint for Flowdacity Queue (FQ) Server

import os
from fq_server import setup_server

# read config path from env variable, fail if not defined
fq_config_path = os.environ.get("FQ_CONFIG")
if fq_config_path is None:
    raise EnvironmentError("FQ_CONFIG environment variable must be defined")
fq_config_path = os.path.abspath(fq_config_path)

server = setup_server(fq_config_path)

# ASGI app exposed for Uvicorn/Hypercorn
app = server.app
