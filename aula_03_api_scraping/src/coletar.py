import sys

from src.cli import main


if __name__ == "__main__":
    raise SystemExit(main(["coletar", *sys.argv[1:]]))
