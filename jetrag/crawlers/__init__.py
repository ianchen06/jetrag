import importlib

def get_crawler_klass(name):
    return getattr(importlib.import_module('crawlers.'+name), name.title())
