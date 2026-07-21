"""Entry point for both `flask run` (dev) and gunicorn (production).

`load_dotenv()` runs before `create_app()`, which is all that matters: the
config objects read the environment when they are instantiated, not when this
module is imported, so import order is not load-bearing here.
"""

from dotenv import load_dotenv

from flask_starterkit.main.config import create_app

load_dotenv()

app = create_app()

if __name__ == "__main__":
    app.run()
