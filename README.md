# EM Field Visualizer

This tool allows users to describe an electrostatics or magnetostatics problem by providing the charge density and current density functions and then generates vector plots depicting the electric and magnetic fields created by the charges and currents.

# Components

## Configuration Editor

The editor is a C++ program using [ImGui](https://github.com/ocornut/imgui) (MIT licensed) to provide an interface for easily constructing an electro- or magnetostatics problem. The configuration can be read from or written to disk in JSON format for the visualizer to read using [json by nlohmann](https://github.com/nlohmann/json) (MIT licensed).

## Visualizer

The visualizer is a Python script that reads the configuration from the JSON file and produces vector field plots for the electric and magnetic fields in the described environment. Calculations are performed using Numpy and the plot uses Matplotlib.

You can find a list of available vector plot color maps in the [Matplotlib Documentation](https://matplotlib.org/3.2.1/gallery/color/colormap_reference.html).

# Configuration Format

## Charge and Current Density Functions

Several preset functions are available for defining continuous charge and current densities. They involve comparing a variable with a given value. The available variables for user defined charge and current density functions are as follows:

| Variable Name | Geometric Meaning |
| --- | --- |
| x, y, z | Cartesian coordinates |
| r | Spherical radius |
| rc | Cylindrical radius |
| theta | Azimuthal angle |
| phi | Polar angle |

Note that it is not possible to use a preset function to compare a combination of variables to a given value. In addition, the value against which the variable is compared must be a literal and not a function. More complex density functions can be implemented by the user, although allowing the evaluation of arbitrary code carries a security risk (see section **Custom Functions**).

The Dirac delta function is zero everywhere except when its argument is zero. In the editor, a value can be specified such that the value of the function is zero except when the argument has that value. Due to the imprecision of floating point arithmetic, the delta function is implemented to check for equality within a tolerance of 0.01 and yield the value 1 if this condition is met.

The Heaviside step function is zero when its argument is negative and one for zero and positive arguments. Here, it is implemented as `variable > value`. The inverse Heaviside function is implemented as the opposite: it yields 1 when `variable < value`. No tolerance is given.

### Custom Functions

The visualizer includes a `--safety` flag which allows the user to set the safety level of function evaluation. There are three levels available: at the safest level (default), only preset functions can be used; at the second level, the AST module is used to build a syntax tree and functions involving the given variables and functions from a whitelist can be evaluated; at the most unsafe level, the function is passed directly to `eval` with no safety measures. This allows the user to define any density function, so long as it can be written as a Python expression, but it also introduces a code injection vulnerability into the visualizer.

# License

Project available under GPLv3
