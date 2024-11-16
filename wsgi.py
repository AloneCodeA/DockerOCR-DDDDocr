import os
from NewOcr import app

if __name__ == "__main__":
    port = int(os.environ.get("PORT",1337))
    app.run(host="0.0.0.0", port=int(os.getenv('PORT', 1337)), debug=True)
