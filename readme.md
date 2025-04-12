## Documentation for `main.py`

This file, `main.py`, implements an energy consumption simulation and visualization tool. It uses AI agents to modify energy consumption data and Pygame to visualize the data with animations.

### Imports

*   `utils.agent.flowtask`: Used to interact with AI agents for data modification.
*   `utils.gen_cons.gen_data`: Used to generate initial energy consumption data.
*   `asyncio`: Used for asynchronous operations, especially when interacting with AI agents.
*   `json`: Used for handling JSON data, which is the format for energy consumption data.
*   `pygame`: Used for creating the visual interface and displaying the simulation.
*   `sys`: Used for system-specific parameters and functions.
*   `traceback`: Used for printing or retrieving traceback information.
*   `threading`: Used for running the data generation in a separate thread to prevent blocking the UI.
*   `queue`: Used for passing data between threads.
*   `math`: Used for mathematical operations, especially for animations.
*   `time`: Used for time-related functions, such as tracking animation duration.
*   `random`: Used for introducing randomness (jitter) into the simulation (optional).

### Classes

#### `ConsumptionModifier`

This class is responsible for modifying the energy consumption data using an AI model.

*   `__init__(self, agent_name, ai_model)`: Initializes the `ConsumptionModifier` with an agent name and an AI model.
    *   `agent_name`: The name of the AI agent.
    *   `ai_model`: The AI model to be used for data modification.
*   `async modify_consumption(self, current_data_dict, modification_rules)`: Asynchronously modifies the energy consumption data based on the provided rules.
    *   `current_data_dict`: A dictionary containing the current energy consumption data.
    *   `modification_rules`: Rules for modifying the energy consumption values.
    *   It sends a prompt to the AI agent, receives the modified data, and returns it as a dictionary.
    *   Includes error handling for invalid data formats and JSON decoding errors.

#### `Energy_manager`

This class manages the generation and modification of energy consumption data.

*   `__init__(self, global_name)`: Initializes the `Energy_manager` with a global name and creates a `ConsumptionModifier` instance.
    *   `global_name`: The name of the energy manager.
    *   It also defines the modification rules to be used by the `ConsumptionModifier`.
*   `async generate_and_modify_data(self)`: Generates initial data, modifies it using the `ConsumptionModifier`, and returns both the initial and modified data.
    *   It uses `gen_data()` to generate the initial data.
    *   It then uses the `ConsumptionModifier` to modify the data based on the defined rules.
    *   Includes error handling for data generation, JSON parsing, and data modification.
    *   Returns a tuple containing the initial and modified JSON data.

### Functions

*   `_run_regeneration_async(manager, result_queue)`: This function runs the data regeneration process asynchronously in a separate thread.
    *   `manager`: An instance of the `Energy_manager` class.
    *   `result_queue`: A queue to store the results of the data regeneration.
    *   It creates a new event loop, runs the `generate_and_modify_data` method of the `Energy_manager`, and puts the result in the queue.
    *   Includes error handling to catch any exceptions during the regeneration process.
*   `lerp(a, b, t)`: Performs linear interpolation between two values `a` and `b` using a factor `t`.
    *   `a`: The starting value.
    *   `b`: The ending value.
    *   `t`: The interpolation factor (0.0 to 1.0).
    *   It handles cases where `a` or `b` might be `None` or non-numeric.
*   `visualize_data_pygame(initial_data_tuple, manager)`: Visualizes the energy consumption data using Pygame.
    *   `initial_data_tuple`: A tuple containing the initial and modified energy consumption data.
    *   `manager`: An instance of the `Energy_manager` class.
    *   It initializes Pygame, sets up the screen, fonts, and colors.
    *   It then enters a main loop that handles events, updates the display, and draws the energy consumption data.
    *   The visualization includes animated transitions between data updates using linear interpolation (`lerp`).
    *   It also includes a button to trigger data regeneration and displays status messages and error messages.

### Main Execution (`if __name__ == "__main__":`)

*   Initializes the `Energy_manager`.
*   Generates the initial energy consumption scenario in a separate thread.
*   Retrieves the generated data from the queue.
*   If the data is successfully generated, it starts the Pygame visualization.
*   Handles potential errors during data generation and visualization.

### Pygame Visualization Details

*   The `visualize_data_pygame` function uses circles to represent houses, with the color of the circle indicating the energy consumption level.
*   The size and brightness of the circles pulse to add visual interest.
*   Linear interpolation is used to create smooth transitions between data updates.
*   The visualization displays both the initial and modified energy consumption values for each house.
*   A button is provided to regenerate the data and update the visualization.
*   Status messages and error messages are displayed to provide feedback to the user.

### Additional Notes

*   The code includes extensive error handling and logging to help diagnose issues.
*   The use of threading allows the UI to remain responsive while data is being generated.
*   The AI agent interaction is asynchronous to prevent blocking the main thread.
*   The Pygame visualization is designed to be visually appealing and informative.