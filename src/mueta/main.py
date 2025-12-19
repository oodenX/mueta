from mueta.core import setup_logging, settings
from mueta.cli import app
from loguru import logger

def main():
    setup_logging(debug=settings.debug)
    app()

if __name__ == "__main__":
    main()
