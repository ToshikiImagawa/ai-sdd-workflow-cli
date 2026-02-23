"""HTTP server for HTML visualization."""

import http.server
import socketserver
import threading
import time
import webbrowser
from importlib import resources
from pathlib import Path


class StaticFileHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """HTTP handler that serves static files and in-memory JSON data."""

    def __init__(self, *args, static_dir=None, json_data=None, **kwargs):
        self.static_dir = static_dir
        self.json_data = json_data or {}
        super().__init__(*args, **kwargs)

    def do_GET(self):
        """Handle GET requests. Serve JSON from memory, static files from disk."""
        # Strip leading slash and query/fragment
        path = self.path.split("?", 1)[0].split("#", 1)[0]
        if path.startswith("/"):
            path = path[1:]

        if path in self.json_data:
            body = self.json_data[path]
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        # Fallback to static file serving
        super().do_GET()

    def translate_path(self, path):
        """Translate URL path to file system path (static files only)."""
        path = path.split("?", 1)[0]
        path = path.split("#", 1)[0]

        if path.startswith("/"):
            path = path[1:]

        if path == "":
            path = "index.html"

        return str(self.static_dir / path)


def start_server(json_data: dict[str, bytes], port: int = 8000) -> None:
    """Start local HTTP server and open browser.

    Args:
        json_data: In-memory JSON data to serve (key: URL path, value: JSON bytes)
        port: Port number (default: 8000, auto-increment if busy)
    """
    # Get static directory from package
    try:
        # First try to use __path__ attribute (works with editable installs)
        import sdd_cli.visualizer.static as static_module

        if hasattr(static_module, "__path__"):
            static_dir = Path(next(iter(static_module.__path__)))
        else:
            # Python 3.9+
            static_files = resources.files("sdd_cli.visualizer.static")
            # Convert to Path - handle MultiplexedPath by getting the actual file path
            if hasattr(static_files, "__fspath__"):
                static_dir = Path(static_files.__fspath__())
            else:
                # Fallback: get path from a known file
                static_dir = Path(str(static_files._paths[0]) if hasattr(static_files, "_paths") else str(static_files))
    except (AttributeError, Exception):
        # Python 3.8 fallback or any error
        import pkg_resources  # type: ignore[import-not-found]

        static_dir = Path(pkg_resources.resource_filename("sdd_cli.visualizer.static", ""))

    # Find available port
    max_attempts = 10
    for attempt in range(max_attempts):
        try:
            # Create handler with static dir and in-memory JSON data
            def handler_factory(*args, **kwargs):
                return StaticFileHTTPRequestHandler(*args, static_dir=static_dir, json_data=json_data, **kwargs)

            with socketserver.TCPServer(("", port), handler_factory) as httpd:
                url = f"http://localhost:{port}/"

                print(f"✓ Server started at {url}")
                print(f"  Static files from: {static_dir}")
                print("  Press Ctrl+C to stop the server\n")

                # Open browser after a short delay
                def open_browser(target_url=url):
                    time.sleep(1.0)
                    webbrowser.open(target_url)

                browser_thread = threading.Thread(target=open_browser)
                browser_thread.daemon = True
                browser_thread.start()

                try:
                    # Start server (this blocks until Ctrl+C)
                    httpd.serve_forever()
                except KeyboardInterrupt:
                    print("\n\n✓ Server stopped")
                break

        except OSError as e:
            if "Address already in use" in str(e):
                port += 1
                if attempt < max_attempts - 1:
                    continue
                else:
                    raise RuntimeError(f"Could not find available port after {max_attempts} attempts") from e
            else:
                raise
