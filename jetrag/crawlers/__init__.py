import importlib

def get_crawler_class(name):
    return getattr(importlib.import_module('crawlers.'+name), name.title())
