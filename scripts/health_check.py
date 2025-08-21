"""Standalone script that prints a basic health payload."""
from __future__ import annotations

import json
from streamlit_extension.endpoints import HealthCheckEndpoint


def main() -> None:
    endpoint = HealthCheckEndpoint()
    print(json.dumps(endpoint.basic_health()))


if __name__ == "__main__":
    main()