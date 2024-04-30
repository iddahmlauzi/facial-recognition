import asyncio
import signal
import os
import argparse
import logging

from PIL import Image
import face_recognition
from hypercorn.asyncio import serve
from hypercorn.config import Config
from quart import Quart, render_template, websocket, request

from backend import create_app
from frontend import WebcamReader

logger = logging.getLogger()

async def _start_frontend(*args, **kwargs):
    return await WebcamReader().read_webcam()

async def _start_backend(shutdown_event:asyncio.Event, *args, **kwargs):
    # We will use this event to gracefully exit our asyncio loop

    config = Config()
    config.bind = ["127.0.0.1:8000"]

    return await serve(create_app(), config, shutdown_trigger=shutdown_event.wait)

def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("mode")
    args = parser.parse_args()

    shutdown_event = asyncio.Event()
    def _signal_handler():
        shutdown_event.set()

    if args.mode == 'backend':
        async_fn = _start_backend(shutdown_event)
    elif args.mode == "frontend":
        async_fn = _start_frontend(shutdown_event)
    else:
        logger.error(
            "Please instantiate this library via 'backend' or 'frontend' mode."
        )
        exit()

    loop = asyncio.get_event_loop()
    loop.add_signal_handler(signal.SIGTERM, _signal_handler)
    loop.run_until_complete(async_fn)


if __name__ == "__main__":
    main()