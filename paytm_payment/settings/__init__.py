__author__ = 'bhupendra'


import os, pwd

# certain keys we want to merge instead of copy
merge_keys = ("INSTALLED_APPS", "MIDDLEWARE_CLASSES")


def deep_update(from_dict, to_dict):
    for (key, value) in from_dict.iteritems():
        if key in to_dict.keys() and isinstance(to_dict[key], dict) and isinstance(value, dict):
            deep_update(value, to_dict[key])
        elif key in merge_keys:
            if not key in to_dict:
                to_dict[key] = ()
            to_dict[key] = to_dict[key] + from_dict[key]
        else:
            to_dict[key] = value


# this should be one of prod, qa, staging, dev. Default to dev for safety.
env = os.environ.get('APP_ENV', 'development')
modules = ('common', 'constants', env)


current = __name__
for module_name in modules:
    try:
        module = getattr(__import__(current, globals(), locals(), [module_name]), module_name)
    except ImportError, e:
        print 'ERROR: Unable to import %s configuration: %s' % (module_name, e)
        raise

    # create a local copy of this module's settings
    module_settings = {}
    for setting in dir(module):
        # all django settings are uppercase, so this ensures we
        # are only processing settings from the dir() call
        if setting == setting.upper():
            module_settings[setting] = getattr(module, setting)

    if not "RABBIT_CONN" in module_settings:
        module_settings["RABBIT_CONN"] = {
            'hostname': 'localhost',
            'userid': 'guest',
            'password': 'guest'
        }
    deep_update(module_settings, locals())

