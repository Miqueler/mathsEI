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
                "acceptance_ratio",
                "digraph_cost",
                "single_letter_cost"
            ])
            self.file.flush()

    def should_log(self):
        return (self.iteration + 1) % self.log_every == 0

    def log(self, temperature, current_cost, best_cost, accepted_moves, total_moves, digraph_cost=None, single_letter_cost=None):
        self.iteration += 1

        if self.iteration % self.log_every != 0:
            return accepted_moves, total_moves

        elapsed = time.time() - self.start_time
        acceptance_ratio = accepted_moves / total_moves if total_moves else 0.0
        self.writer.writerow([
            self.iteration,
            round(elapsed, 2),
            temperature,
            current_cost,
            best_cost,
            round(acceptance_ratio, 6),
            digraph_cost,
            single_letter_cost
        ])
        self.file.flush()
        return 0, 0

    def close(self):
        self.file.close()
