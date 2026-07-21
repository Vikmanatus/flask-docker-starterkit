"""Entry point for both `flask run` (dev) and gunicorn (production).

`load_dotenv()` runs before `create_app()`, which is all that matters: the
config objects read the environment when they are instantiated, not when this
module is imported, so import order is not load-bearing here.
"""

from dotenv import load_dotenv

from flask_starterkit.main.config import create_app
from flask_starterkit.main.debug import attach_pycharm_debugger

load_dotenv()

# Before create_app(), so breakpoints inside the application factory still bind
# on a hot reload. No-ops unless $PYCHARM_DEBUG is set (see debug.py).
attach_pycharm_debugger()

app = create_app()

if __name__ == "__main__":
    app.run()
