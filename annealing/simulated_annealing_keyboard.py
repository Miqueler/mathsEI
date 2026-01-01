import json
import math 
import random
import os
from clac_layout_cost import *
from progress_logger import ProgressLogger


def generate_random_layout(letters: list, positions: list):
    random_layout = {}
    random.shuffle(letters)
    for i in range(len(letters)):
        random_layout.update({letters[i]:positions[i]})
    return random_layout


def swap_two_letters(layout: dict):
    # Work on a copy so we don't mutate the input layout in-place
    new_layout = dict(layout)
    letter_1, letter_2 = random.sample(list(new_layout.keys()), 2)
    new_layout[letter_1], new_layout[letter_2] = new_layout[letter_2], new_layout[letter_1]
    return new_layout


def accetpt_neighbour(current_cost: float, neighbour_cost: float, temperature: float):
    cost_difference = neighbour_cost - current_cost

    if cost_difference <= 0:
        return True
    if temperature <= 0: 
        return False
    acceptance_probability = math.exp(-cost_difference / temperature)
    return random.random() < acceptance_probability


def write_best_layout_snapshot(layout: dict, best_cost: float, path: str):
    # Store as JSON so the dashboard can read it live.
    payload = {
        "best_cost": best_cost,
        "layout": {k: [v[0], v[1]] for k, v in layout.items()}
    }
    with open(path, "w") as f:
        json.dump(payload, f)


def simmulated_annealing_optimize_layout(initial_layout: dict,
                                        letter_probs: dict,
                                        digraph_probs: dict,
                                        initial_temperature: float,
                                        final_temperature: float,
                                        cooling_rate: float,
                                        iterations_per_temperature: int,
                                        logger: ProgressLogger
                                        ):
    
    current_layout = dict(initial_layout)
    current_cost = calculate_keyboard_cost(current_layout, digraph_probs, letter_probs)
    best_cost = current_cost
    best_layout = dict(initial_layout)

    current_temperature = initial_temperature

    cost_history = []
    temperature_history = []
    total_moves = 0
    accepted_moves = 0
    snapshot_path = "annealing/progress_logs/current_best_layout.json"
    while current_temperature > final_temperature:
        for i in range(iterations_per_temperature):
            neighbour_layout = swap_two_letters(current_layout)
            neighbour_cost = calculate_keyboard_cost(neighbour_layout, digraph_probs, letter_probs)

            accept = accetpt_neighbour(current_cost, neighbour_cost, current_temperature)
            if accept:
                current_layout = neighbour_layout
                current_cost = neighbour_cost

                if current_cost < best_cost:
                    best_cost = current_cost
                    best_layout = current_layout
                    write_best_layout_snapshot(best_layout, best_cost, snapshot_path)

            #Just for logging
            total_moves += 1
            if accept:
                accepted_moves += 1

            cost_history.append(current_cost)
            temperature_history.append(current_temperature)
            
            if total_moves % 1000 == 0:
                acceptance_rate = accepted_moves / total_moves if total_moves else 0.0
                print(f"acceptance_rate={acceptance_rate:.3f}  T={current_temperature:.3f}  current={current_cost:.3f}  best={best_cost:.3f}")
            digraph_cost = None
            single_letter_cost = None
            if logger.should_log():
                digraph_cost, single_letter_cost, _ = calculate_keyboard_cost_components(
                    current_layout,
                    digraph_probs,
                    letter_probs
                )
            accepted_moves, total_moves = logger.log(
                current_temperature,
                current_cost,
                best_cost,
                accepted_moves,
                total_moves,
                digraph_cost=digraph_cost,
                single_letter_cost=single_letter_cost
            )
            if total_moves == 0:
                write_best_layout_snapshot(best_layout, best_cost, snapshot_path)

        current_temperature *= cooling_rate
    logger.close()
    return {
        "best_layout": best_layout,
        "best_cost": best_cost,
        "cost_history": cost_history,
        "temperature_history": temperature_history
    }

letters = list("abcdefghijklmnopqrstuvwxyzñ")
positions =[(1.5, 0),(2.5, 0),(3.5, 0),(4.5, 0),(5.5, 0),(6.5, 0),(7.5, 0),(8.5, 0),(9.5, 0),(10.5, 0),
            (1.75, 1),(2.75, 1),(3.75, 1),(4.75, 1),(5.75, 1),(6.75, 1),(7.75, 1),(8.75, 1),(9.75, 1),(10.75, 1),
            (2.25, 2),(3.25, 2),(4.25, 2),(5.25, 2),(6.25, 2),(7.25, 2),(8.25, 2)]

initial_layout = generate_random_layout(letters, positions)
letter_probs = load_probability_dictionary_from_txt("annealing/files/single_char_prob.txt")
digraph_probs = load_probability_dictionary_from_txt("annealing/files/digraphs_prob.txt")


file_counter = 1
while os.path.exists(f"annealing/result_log/results{file_counter}.txt"):
    file_counter += 1


logger = ProgressLogger(
    filename=f"annealing/progress_logs/annealing_progress{file_counter}.csv",
    log_every=1000
)

best_layout, best_cost, cost_history, temperature_history = simmulated_annealing_optimize_layout(initial_layout,
                                                                                                letter_probs,
                                                                                                digraph_probs,
                                                                                                initial_temperature = .1, 
                                                                                                final_temperature = 1e-4,
                                                                                                cooling_rate = 0.999, 
                                                                                                iterations_per_temperature = 1000, 
                                                                                                logger=logger).values()



results = open(f"annealing/result_log/results{file_counter}.txt", "x")
results.write(f"{best_layout}\n{best_cost}\n{cost_history}\n{temperature_history}")
print("Finalized")
