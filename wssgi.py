import OS
from app import app

if __name__ == "__main__":
    port = int(os.environ.get("PORT",1337))
    app.run(host="0.0.0.0", port=port)
