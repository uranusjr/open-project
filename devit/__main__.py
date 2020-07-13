import os
import sys

if not __package__:
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "..", "..")))

if __name__ == "__main__":
    from devit import main
    sys.exit(main())
