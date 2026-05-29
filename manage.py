#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    """Run administrative tasks."""
    # Ensure project root is on sys.path so apps (e.g. participantmgmt) can be imported
    project_root = os.path.dirname(os.path.abspath(__file__))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pravaah.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    # If running the development server, open the landing page in a browser.
    if 'runserver' in sys.argv:
        try:
            import webbrowser
            import threading

            # Determine addr:port if provided, otherwise default to 127.0.0.1:8000
            addr = '127.0.0.1:8000'
            idx = sys.argv.index('runserver')
            if len(sys.argv) > idx + 1 and not sys.argv[idx + 1].startswith('-'):
                addr = sys.argv[idx + 1]

            host, sep, port = addr.partition(':')
            browse_host = '127.0.0.1' if host in ('0.0.0.0', '') else host
            port = port or '8000'
            url = f'http://{browse_host}:{port}/'

            # Delay opening slightly to give the server time to start
            threading.Timer(1.0, lambda: webbrowser.open(url)).start()
        except Exception:
            pass

    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
