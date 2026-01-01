import csv
import os
import time

class ProgressLogger:
    def __init__(self, filename, log_every=1000):
        self.filename = filename
        self.log_every = log_every
        self.start_time = time.time()
        self.iteration = 0

        file_exists = os.path.isfile(filename)
        self.file = open(filename, "a", newline="")
        self.writer = csv.writer(self.file)

        if not file_exists:
            self.writer.writerow([
                "iteration",
                "elapsed_seconds",
                "temperature",
                "current_cost",
                "best_cost",
                "accepted"
            ])
            self.file.flush()

    def log(self, temperature, current_cost, best_cost, accepted):
        self.iteration += 1

        if self.iteration % self.log_every != 0:
            return

        elapsed = time.time() - self.start_time

        self.writer.writerow([
            self.iteration,
            round(elapsed, 2),
            temperature,
            current_cost,
            best_cost,
            int(accepted)
        ])
        self.file.flush()

    def close(self):
        self.file.close()