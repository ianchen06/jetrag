import importlib

def get_queue_ctl_klass(broker_name):
    m = importlib.import_module('q.'+broker_name)
    return getattr(m, broker_name.title())

def get_queue_klass(broker_name):
    m = importlib.import_module('q.'+broker_name)
    return getattr(m, broker_name.title()+'Queue')