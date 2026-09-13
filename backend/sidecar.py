import argparse
import os

from waitress import serve

from backend.app import create_app


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Colemak-DH Tutor local API sidecar")
    parser.add_argument("--port", required=True, type=int)
    parser.add_argument("--data-dir", required=True)
    parser.add_argument("--token", default=os.environ.get("COLEMAK_SIDECAR_TOKEN"))
    args = parser.parse_args()
    if not args.token:
        parser.error("--token or COLEMAK_SIDECAR_TOKEN is required")
    if not 1024 <= args.port <= 65535:
        parser.error("--port must be between 1024 and 65535")
    return args


def main() -> None:
    args = parse_args()
    app = create_app(data_dir=args.data_dir, auth_token=args.token)
    serve(app, host="127.0.0.1", port=args.port, threads=4, clear_untrusted_proxy_headers=True)


if __name__ == "__main__":
    main()
