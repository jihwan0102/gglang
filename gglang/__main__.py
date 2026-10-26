import sys

from gglang.runtime import GGError, GGya


def main():
    if len(sys.argv) != 2:
        print("사용법: python -m gglang 파일.ggya", file=sys.stderr)
        sys.exit(2)
    with open(sys.argv[1], encoding="utf-8") as f:
        code = f.read()
    try:
        GGya().run(code)
    except GGError as e:
        sys.stdout.flush()
        print(f"아 예? 엄 줴줴이야~ {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
