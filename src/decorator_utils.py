import functools
import time
import sys
import threading
from datetime import datetime

def process_printer(process_name: str):
    """
    A decorator that:
      - Prints a blinking "started..." line in a background thread
      - Stops when the function finishes or fails
      - Overwrites the spinner line with success/failure.
    """
    def decorator_process(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = datetime.now()

            # We'll use an Event to signal the spinner thread to stop.
            stop_spinner = threading.Event()

            # This will cycle through: ".", "..", "...", ""
            # and then repeat.
            cycle = [" . ", " . . ", " . . . ", ""]

            def spinner():
                i = 0
                while not stop_spinner.is_set():
                    # Move cursor to start of line, clear it, and print the spinner
                    sys.stdout.write(
                        f"\r\033[K\033[33m●\033[0m Process \"{process_name}\" started{cycle[i]}"
                    )
                    sys.stdout.flush()
                    i = (i + 1) % len(cycle)
                    time.sleep(0.5)  # Update speed of blinking here

            # Start the spinner thread (daemon = True so it won't block program exit)
            t = threading.Thread(target=spinner, daemon=True)
            t.start()

            # Run the wrapped function
            try:
                result = func(*args, **kwargs)
                duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)

                # Stop the spinner
                stop_spinner.set()
                t.join()  # Wait for thread to finish cleanup

                # Overwrite the spinner line with success message
                sys.stdout.write(
                    f"\r\033[K\033[32m✔\033[0m Process \"{process_name}\" successful "
                    f"after {duration_ms} ms.\n"
                )
                sys.stdout.flush()

                return result

            except Exception as e:
                duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)

                # Stop the spinner
                stop_spinner.set()
                t.join()

                # Overwrite the spinner line with error message
                sys.stdout.write(
                    f"\r\033[K❌ Process \"{process_name}\" failed with error: "
                    f"\"{e}\" after {duration_ms} ms.\n"
                )
                sys.stdout.flush()

                # Re-raise the exception so the caller can handle it
                raise
        return wrapper
    return decorator_process
