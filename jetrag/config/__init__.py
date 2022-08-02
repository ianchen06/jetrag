def get_config(env):
    cfg = None
    if env == 'dev':
        from .dev import cfg
    if env == 'prod':
        from .prod import cfg
    return cfg