"""Run the synthetic pipeline and tests with this Python interpreter."""

import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent


def run(*arguments):
    print("Running:", " ".join(arguments), flush=True)
    subprocess.run([sys.executable, *arguments], cwd=PROJECT_ROOT, check=True)


def main():
    for script in (
        "src/generate_demo_data.py",
        "src/validate_data.py",
        "src/forecast_service_volume.py",
        "src/report_assistant.py",
    ):
        run(script)
    run("-m", "unittest", "discover", "-s", "tests", "-v")
    print("Pipeline and tests completed. Start dashboard/app.py with Streamlit.")


if __name__ == "__main__":
    main()
