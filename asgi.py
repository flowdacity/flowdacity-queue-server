# Copyright (c) 2025 Flowdacity Team. See LICENSE.txt for details.
# ASGI application entrypoint for Flowdacity Queue (FQ) Server

import os
from fq_server import setup_server

# read config path from env variable, use default if not set
fq_config_path = os.environ.get("FQ_CONFIG")
if fq_config_path is None:
    print(
        "Warning: FQ_CONFIG environment variable not set. Using default config path './default.conf'."
    )
    fq_config_path = "./default.conf"
fq_config_path = os.path.abspath(fq_config_path)

server = setup_server(fq_config_path)

# ASGI app exposed for Uvicorn/Hypercorn
app = server.app
