#! /usr/bin/env python3

"""Shutdown redis server."""

import os

import redis

with open(f"{os.getenv('CYLC_WORKFLOW_SHARE_DIR')}/redis_uri", encoding="utf-8") as fp:
    redis_uri = fp.read().strip()
    redis.Redis.from_url(redis_uri).shutdown()
