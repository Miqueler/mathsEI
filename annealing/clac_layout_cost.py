import ast
import math


def load_probability_dictionary_from_txt(file_path):
    #Loads a dictionary saved as a Python-literal string, e.g. {'a': 0.1, 'b': 0.2, ...}
    with open(file_path, "r", encoding="utf-8") as file_handle:
        file_contents = file_handle.read()
    loaded_object = ast.literal_eval(file_contents)
    if not isinstance(loaded_object, dict):
        raise ValueError(f"The file does not contain a dictionary: {file_path}")
    return loaded_object


def normalize_probability_dictionary(probability_dictionary):
    """
    Ensures values sum to 1.0 (works even if input is counts).
    """
    total_mass = float(sum(probability_dictionary.values()))
    if total_mass <= 0.0:
        raise ValueError("Total probability mass is zero; cannot normalize.")
    return {key: float(value) / total_mass for key, value in probability_dictionary.items()}


def compute_home_point(letter_coordinates):
    """
    Chooses a 'home' reference point as the average (mean) of all key coordinates.
    This is simple and layout-agnostic.
    """
    x_values = [coord[0] for coord in letter_coordinates.values()]
    y_values = [coord[1] for coord in letter_coordinates.values()]
    return (sum(x_values) / len(x_values), sum(y_values) / len(y_values))


def fitts_time(distance, width, a_value, b_value):
    #Calculate the fitts time for the given values
    return a_value + b_value * math.log2(distance/width + 1)


def build_fitts_cost_matrix_for_layout(letter_coordinates: dict, key_width=1.0, intercept_a=0.0, slope_b=1.0):
    """
    Precomputes movement time between every pair of letters in the layout.

    letter_coordinates: dict like {'a': (x,y), 'b': (x,y), ...} all lowercase
    Returns:
      letter_to_index: dict letter -> index
      movement_time_by_index: 2D list [i][j] = fitts_time(letter_i -> letter_j)
    """
    letters_in_layout = list(letter_coordinates.keys())
    letter_to_index = {letter: index for index, letter in enumerate(letters_in_layout)}

    x_by_index = [letter_coordinates[letter][0] for letter in letters_in_layout]
    y_by_index = [letter_coordinates[letter][1] for letter in letters_in_layout]

    number_of_letters = len(letters_in_layout)
    movement_time_by_index = [[0.0] * number_of_letters for _ in range(number_of_letters)]

    for from_index in range(number_of_letters):
        x_from = x_by_index[from_index]
        y_from = y_by_index[from_index]
        for to_index in range(number_of_letters):
            dx = x_from - x_by_index[to_index]
            dy = y_from - y_by_index[to_index]
            distance = math.hypot(dx, dy)
            movement_time_by_index[from_index][to_index] = fitts_time(
                distance=distance,
                width=key_width,
                a_value=intercept_a,
                b_value=slope_b
            )

    #returns the indexes to the letters as a dictionary and then the matrix of the fitts time it takes to get to the other letter, [i][j] i is the from letter and j is the to letter
    return letter_to_index, movement_time_by_index


def calculate_keyboard_cost(
    letter_coordinates,
    digraph_probabilities,
    single_letter_probabilities,
    key_width=1.0,
    intercept_a=0.0,
    slope_b=1.0,
    digraph_weight=1.0,
    single_letter_weight=0.1,
    normalize_inputs=True,
):
    """
    Total cost:
      digraph_weight * Σ P(ij) * FittsTime(i -> j)
    + single_letter_weight * Σ P(i) * Distance(pos(i), home_point)

    - Digraphs are 2-char strings like "de".
    - Letters are lowercase.
    """
    if normalize_inputs:
        digraph_probabilities = normalize_probability_dictionary(digraph_probabilities)
        single_letter_probabilities = normalize_probability_dictionary(single_letter_probabilities)

    # --- Step 1: Precompute Fitts times for this layout ---
    letter_to_index, fitts_time_by_index = build_fitts_cost_matrix_for_layout(
        letter_coordinates=letter_coordinates,
        key_width=key_width,
        intercept_a=intercept_a,
        slope_b=slope_b,
    )

    # --- Step 2: Digraph cost ---
    digraph_cost = 0.0
    for digraph, digraph_probability in digraph_probabilities.items():
        from_letter = digraph[0]
        to_letter = digraph[1]

        from_index = letter_to_index[from_letter]
        to_index = letter_to_index[to_letter]

        movement_time = fitts_time_by_index[from_index][to_index]
        digraph_cost += float(digraph_probability) * movement_time

    # --- Step 3: Single-letter cost ---
    home_x, home_y = compute_home_point(letter_coordinates)

    single_letter_cost = 0.0
    for letter, letter_probability in single_letter_probabilities.items():
        letter_x, letter_y = letter_coordinates[letter]
        distance_to_home = math.hypot(letter_x - home_x, letter_y - home_y)

        single_letter_cost += float(letter_probability) * distance_to_home

    total_cost = digraph_weight * digraph_cost + single_letter_weight * single_letter_cost
    return total_cost


def calculate_keyboard_cost_components(
    letter_coordinates,
    digraph_probabilities,
    single_letter_probabilities,
    key_width=1.0,
    intercept_a=0.0,
    slope_b=1.0,
    digraph_weight=1.0,
    single_letter_weight=0.1,
    normalize_inputs=True,
):
    if normalize_inputs:
        digraph_probabilities = normalize_probability_dictionary(digraph_probabilities)
        single_letter_probabilities = normalize_probability_dictionary(single_letter_probabilities)

    letter_to_index, fitts_time_by_index = build_fitts_cost_matrix_for_layout(
        letter_coordinates=letter_coordinates,
        key_width=key_width,
        intercept_a=intercept_a,
        slope_b=slope_b,
    )

    digraph_cost = 0.0
    for digraph, digraph_probability in digraph_probabilities.items():
        from_letter = digraph[0]
        to_letter = digraph[1]
        from_index = letter_to_index[from_letter]
        to_index = letter_to_index[to_letter]
        movement_time = fitts_time_by_index[from_index][to_index]
        digraph_cost += float(digraph_probability) * movement_time

    home_x, home_y = compute_home_point(letter_coordinates)

    single_letter_cost = 0.0
    for letter, letter_probability in single_letter_probabilities.items():
        letter_x, letter_y = letter_coordinates[letter]
        distance_to_home = math.hypot(letter_x - home_x, letter_y - home_y)
        single_letter_cost += float(letter_probability) * distance_to_home

    total_cost = digraph_weight * digraph_cost + single_letter_weight * single_letter_cost
    return digraph_cost, single_letter_cost, total_cost



#qwerty_pos = {
#    'q': (1.5, 0), 'w': (2.5, 0), 'e': (3.5, 0), 'r': (4.5, 0),
#    't': (5.5, 0), 'y': (6.5, 0), 'u': (7.5, 0), 'i': (8.5, 0),
#    'o': (9.5, 0), 'p': (10.5, 0),
#
#    'a': (1.75, 1), 's': (2.75, 1), 'd': (3.75, 1),
#    'f': (4.75, 1), 'g': (5.75, 1), 'h': (6.75, 1),
#    'j': (7.75, 1), 'k': (8.75, 1), 'l': (9.75, 1),
#    'ñ': (10.75, 1),
#
#    'z': (2.25, 2), 'x': (3.25, 2), 'c': (4.25, 2),
#    'v': (5.25, 2), 'b': (6.25, 2), 'n': (7.25, 2),
#    'm': (8.25, 2),
#}
#
#digraph_probs = load_probability_dictionary_from_txt("files/digraphs_prob.txt")
#char_probs = load_probability_dictionary_from_txt("files/single_char_prob.txt")
#
#keyboard_cost = calculate_keyboard_cost(qwerty_pos, digraph_probs, char_probs)
#print(keyboard_cost)
