import sys

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "selftest"
    if cmd == "parsecheck":
        from .parsecheck import main
        sys.exit(main(sys.argv[2:]))
    from .selftest import main
    sys.exit(main())
