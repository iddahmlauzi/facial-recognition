import os
from importlib import import_module

from quart import Quart


def create_app(*args, **kwargs):

    # create and configure the app
    app = Quart(__name__, instance_relative_config=True)
    config_mapping = {
        "SECRET_KEY": "239DR)23@293msgkfG#kffgnj",
        "MAX_CONTENT_LENGTH": 10*1000*1000
    }

    # if is_test:
    #     # Required for "url_for" utility to work properly
    #     config_mapping["SERVER_NAME"] = "localhost"

    app.config.from_mapping(**config_mapping)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # Register URL/Websocket Blueprints
    register_blueprints_from_modules(app, "routing")  
    return app

def register_blueprints_from_modules(app: Quart, *src_modules):

    blueprints = []
    for module_str in src_modules:

        # Extract all blueprints defined in the given module.
        # assume they all end in "_blueprint"
        m_instance = import_module(module_str)
        for attr in dir(m_instance):
            if attr.endswith("_blueprint"):
                blueprints.append(getattr(m_instance, attr))

    for b in blueprints:
        app.register_blueprint(b)