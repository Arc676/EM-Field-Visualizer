# EM Field Visualizer

This tool allows users to describe an electrostatics or magnetostatics problem by providing the charge density and current density functions and then generates vector plots depicting the electric and magnetic fields created by the charges and currents.

# Components

## Configuration Editor

The editor is a C++ program using [ImGui](https://github.com/ocornut/imgui) (MIT licensed) to provide an interface for easily constructing an electro- or magnetostatics problem. The configuration can be read from or written to disk in JSON format for the visualizer to read using [json by nlohmann](https://github.com/nlohmann/json) (MIT licensed).

## Visualizer

The visualizer is a Python script that reads the configuration from the JSON file and produces vector field plots for the electric and magnetic fields in the described environment. Calculations are performed using Numpy and the plot uses Matplotlib.

# License

Project available under GPLv3
