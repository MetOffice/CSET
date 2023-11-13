#! /usr/bin/env python3

"""Starts a redis server, signalling to the workflow when it is up."""

import logging
import os
import socket
import subprocess
import threading
import time
from pathlib import Path

import redis

logging.basicConfig(level=logging.WARNING)


def blocking_ping_redis(timeout: float = 300.0) -> bool:
    """Ping the redis server until we get a lively response.

    Blocks for a maximum of timeout seconds. Returns True if it makes contact,
    and False otherwise.
    """
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with open(
                f"{os.getenv('CYLC_WORKFLOW_SHARE_DIR')}/redis_uri", encoding="utf-8"
            ) as fp:
                uri = fp.read().strip()
                if len(uri) > 1:
                    logging.debug(f"Accessing database at {uri}")
                    break
                else:
                    # File is empty. Probably still being written to.
                    raise FileNotFoundError
        except FileNotFoundError:
            logging.info("Waiting for URI file")
            time.sleep(1)
    while time.time() < deadline:
        try:
            if redis.Redis().from_url(uri).ping():
                subprocess.run(
                    (
                        "cylc",
                        "message",
                        "--",
                        f"{os.getenv('CYLC_WORKFLOW_ID')}",
                        f"{os.getenv('CYLC_TASK_JOB')}",
                        "Database ready",
                    ),
                    check=True,
                )
                return True
        except redis.ConnectionError:
            logging.info("Waiting for database to come online")
            time.sleep(1)
    logging.error("Timeout exceeded in database liveliness check")
    return False


def start_redis_server() -> None:
    """Start the redis server, blocking until it is shut down externally."""
    redis_config = f"{os.getcwd()}/redis.conf"
    redis_uri_file = Path(f'{os.getenv("CYLC_WORKFLOW_SHARE_DIR")}/redis_uri')
    os.chdir(redis_uri_file.parent)
    logging.debug(f"URI file at {redis_uri_file}")
    try:
        port = 6379
        # Try 50 ports before giving up. This should probably be more than enough as
        # it corresponds to the number of redis servers running on a single machine.
        while port < 6430:
            started = time.time()
            uri = f"redis://{socket.getfqdn()}:{port}/0"
            logging.info(f"Starting database at {uri}")
            with open(redis_uri_file, "wt", encoding="utf-8") as f:
                f.write(uri)
            try:
                subprocess.run(
                    ("redis-server", redis_config, f"--port {port}"), check=True
                )
                logging.debug("Database shutdown cleanly")
                break
            except subprocess.CalledProcessError as err:
                if time.time() - started < 10.0:
                    # Failing after more than 10 seconds is probably not port
                    # related. Otherwise try another port.
                    logging.debug(err)
                    logging.warning(
                        f"Database startup failed on port {port}. Retrying on next port"
                    )
                    port += 1
                else:
                    raise err
    finally:
        redis_uri_file.unlink(missing_ok=True)


if __name__ == "__main__":
    threading.Thread(target=blocking_ping_redis).start()
    start_redis_server()
