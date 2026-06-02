import streamlit as st


@st.cache_resource
def _connect_mongodb():
    from pymongo import MongoClient
    from ..config import MONGODB_URI, MONGODB_DATABASE
    try:
        client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=3000)
        client.admin.command("ping")
        return client, client[MONGODB_DATABASE]
    except Exception:
        return None, None


@st.cache_resource
def _connect_redis():
    from redis import Redis
    from ..config import REDIS_HOST, REDIS_PORT
    try:
        client = Redis(host=REDIS_HOST, port=REDIS_PORT, socket_timeout=3)
        client.ping()
        return client
    except Exception:
        return None


def get_mongodb_client():
    return _connect_mongodb()


def get_redis_client():
    return _connect_redis()
