def get_config(env):
    cfg = None
    if env == 'dev':
        from .dev import cfg
    if env == 'prod':
        from .prod import cfg
    if env == 'test':
        from .test import cfg
    return cfg