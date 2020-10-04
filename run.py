import os
from app import app
from app.routes.routes import blueprint

app.register_blueprint(blueprint)

production = os.environ.get("PRODUCTION", False)

if __name__ == '__main__':
    if production:
        app.run(debug=True)
    else:
        app.run(host='127.0.0.1', port=8002, debug=True)
