#!/usr/bin/env python3
# Copyright (C) 2020-1 Arc676/Alessandro Vinciguerra <alesvinciguerra@gmail.com>

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation (version 3).

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

import numpy as np
from scipy.integrate import tplquad, dblquad, quad
import matplotlib.pyplot as plt
import argparse
import json

import evaluation as safe_eval
import presets

# Command line parameters
output_files = {"e-field": None, "b-field": None}
eval_safety = 0

def complete_config(config):
	"""Generates a configuration dictionary with all the necessary parameters for
	visualization by adding default values or inferring values when none are
	provided.

	Args:
		config: Provided configuration data

	Returns:
		Configuration data, supplemented with missing values if needed
	"""
	# Default plot margins
	if "plot-margins" not in config:
		config["plot-margins"] = [5, 5, 5]
	# Plot both fields by default
	for field in ["b-field", "e-field"]:
		if field not in config:
			config[field] = {"plot": True}
		elif "plot" not in config[field]:
			config[field]["plot"] = True
	# Plot fields in XY plane by default (Z is the 3rd axis, 2 by zero-indexing)
	if "plane" not in config:
		config["plane"] = {"axis": 2, "coordinate": 0}
	# By default, don't show the fields interactively after plotting
	if "show" not in config:
		config["show"] = False
	# Determine the boundaries of the plot
	if "plot-bounds" not in config:
		if "charges" in config:
			charges = np.array(config["charges"])
			coords_min = np.min(charges[:,1:], axis=0)
			coords_max = np.max(charges[:,1:], axis=0)
		try:
			config["plot-bounds"] = {"min": coords_min, "max": coords_max}
		except NameError:
			raise Exception("Failed to infer plot bounds")
	# Default resolution
	if "resolution" not in config:
		config["resolution"] = 100
	# Streamplot colormap
	if "colormap" not in config:
		config["colormap"] = "cool"
	return config

def construct_function(safety, function):
	if safety == 0:
		raise Exception("Cannot construct function at safety level 0")
	elif safety == 1:
		pass
	else:
		def func(x, y, z):
			r = presets.get_variable("r")(x, y, z)
			rc = presets.get_variable("rc")(x, y, z)
			theta = presets.get_variable("theta")(x, y, z)
			phi = presets.get_variable("phi")(x, y, z)
			return eval(function)

def visualize_fields(config):
	"""Plot electric and magnetic fields for given configuration

	Args:
		config: Environment configuration
	"""
	ax3 = config["plane"]["axis"]
	Z = config["plane"]["coordinate"]
	axes = []
	for i in range(3):
		if i == ax3:
			axes.append([Z])
		else:
			x_min, x_max = config["plot-bounds"]["min"][i], config["plot-bounds"]["max"][i]
			x_min -= config["plot-margins"][i]
			x_max += config["plot-margins"][i]
			axis = np.linspace(x_min, x_max, config["resolution"] * int(x_max - x_min))
			axes.append(axis)
	space = np.array(np.meshgrid(*axes))

	axis_names = ["x", "y", "z"]
	ax1, ax2 = {
		0: (1, 2),
		1: (0, 2),
		2: (0, 1)
	}[ax3]
	e_field, b_field = np.zeros_like(space), np.zeros_like(space)

	if "charges" in config:
		charges = np.array(config["charges"])
		def efield_charges(x):
			E = np.zeros_like(x)
			for charge in charges:
				s = (x.T - charge[1:]).T
				E += charge[0] * s / (np.linalg.norm(s, axis=0) ** 3 + 1e-6)
			return E
		e_field += efield_charges(space)

	list_charge_densities = []
	if "charge-densities" in config:
		densities = config["charge-densities"]
		for density_func in densities:
			if density_func["preset"]:
				rho = presets.get_preset(density_func)
			else:
				rho = construct_function(eval_safety, density_func["func"])
			list_charge_densities.append(rho)
			def integrand(z, y, x, Xz, Xy, Xx, axis):
				X = np.array([Xx, Xy, Xz])
				Y = np.array([x, y, z])
				v = X - Y
				return rho(z, y, x) * v[axis] / (np.linalg.norm(v) ** 3 + 1e-6)
			def integrand2(y, x, Xz, Xy, Xx, axis, z, axis1, axis2, axis3):
				Y = np.empty(3)
				Y[axis1] = x
				Y[axis2] = y
				Y[axis3] = z
				return integrand(Y[2], Y[1], Y[0], Xz, Xy, Xx, axis)
			def integrand1(x, Xz, Xy, Xx, axis, y, z, axis1, axis2, axis3):
				Y = np.empty(3)
				Y[axis1] = x
				Y[axis2] = y
				Y[axis3] = z
				return integrand(Y[2], Y[1], Y[0], Xz, Xy, Xx, axis)
			def grid_integral(f, *bounds, args=(), dim=3):
				if dim == 3:
					return np.vectorize(
						lambda z, y, x: tplquad(
							f, *bounds,
							args=(z, y, x, *args)
						)[0] if rho(z, y, x) == 0 else 0
					)
				elif dim == 2:
					return np.vectorize(
						lambda z, y, x: dblquad(
							f, *bounds,
							args=(z, y, x, *args)
						)[0]
					)
				elif dim == 1:
					return np.vectorize(
						lambda z, y, x: quad(
							f, *bounds,
							args=(z, y, x, *args)
						)[0]
					)
			if density_func["func"] == presets.PRESET_DELTA and \
					density_func["var"] in ["x", "y", "z"]:
				val = density_func["value"]
				axis1, axis2, delAxis = {
					("x", 0): (1,2,0),
					("x", 1): (2,1,0),
					("x", 2): (1,2,0),
					("y", 0): (2,0,1),
					("y", 1): (0,2,1),
					("y", 2): (0,2,1),
					("z", 0): (1,0,2),
					("z", 1): (0,1,2),
					("z", 2): (0,1,2)
				}[(density_func["var"], ax3)]
				ax, ay = axes[axis1][0], axes[axis2][0]
				bx, by = axes[axis1][-1], axes[axis2][-1]
				for axis in range(3):
					if axis == ax3:
						continue
					if delAxis == ax3:
						# Technically this should never come up
						# because the field is parallel to the
						# ignored axis
						e_field[axis] += grid_integral(
							integrand2,
							ax, bx, ay, by,
							args=(axis, val, axis1, axis2, delAxis), dim=2
						)(space[2], space[1], space[0])
					else:
						e_field[axis] += grid_integral(
							integrand1,
							ax, bx,
							args=(axis, val, Z, axis1, delAxis, axis2),
							dim=1
						)(space[2], space[1], space[0])
			else:
				ax, ay, az = axes[0][0], axes[1][0], axes[2][0]
				bx, by, bz = axes[0][-1], axes[1][-1], axes[2][-1]
				if ax == bx:
					ax, bx = ay, by
				elif ay == by:
					ay, by = ax, bx
				elif az == bz:
					az, bz = ax, bx
				for axis in range(3):
					if axis == ax3:
						continue
					e_field[axis] += grid_integral(
						integrand,
						ax, bx, ay, by, az, bz,
						args=(axis,)
					)(space[2], space[1], space[0])

	# Determine overall charge density distribution
	if len(list_charge_densities) > 0:
		overall_charge_density = np.zeros_like(space[0])
	for rho in list_charge_densities:
		overall_charge_density += np.vectorize(rho)(space[2], space[1], space[0])

	if ax3 != 2:
		ax1, ax2 = ax2, ax1
		e_field = np.moveaxis(e_field, 2 - ax3, -1)
		b_field = np.moveaxis(b_field, 2 - ax3, -1)
		overall_charge_density = np.moveaxis(overall_charge_density, 1 - ax3, -1)

	# Generate field plots
	for field_name, field in zip(["e", "b"], [e_field, b_field]):
		config_name = f"{field_name}-field"
		if config[config_name]["plot"]:
			render_name = f"{field_name.upper()}-Field"
			plt.figure(render_name)

			# Plot charges
			if "charges" in config:
				for charge in config["charges"]:
					xy = (charge[1 + ax1], charge[1 + ax2])
					plt.plot(*xy, 'ro', color=("red" if charge[0] > 0 else "blue"))
					plt.annotate(f"{charge[0]} C", xy=xy, xytext=(10,5), ha='right', textcoords='offset points')

			# Plot charge densities
			if len(list_charge_densities) > 0:
				plt.contourf(axes[ax1], axes[ax2], overall_charge_density.T[0].T, cmap=plt.cm.bwr)

			# Plot field
			fx, fy = field[ax1].T[0].T, field[ax2].T[0].T
			color = 2 * np.log(np.hypot(fx, fy) + 1e-6)
			try:
				plt.streamplot(axes[ax1], axes[ax2], fx, fy, color=color, cmap=plt.get_cmap(config["colormap"]))
			except ValueError as e:
				print(f"Failed to plot {render_name}: {e}")

			# Plot labels
			plt.title(f"{render_name} ({axis_names[ax3]} = {Z})")
			plt.xlabel(axis_names[ax1])
			plt.ylabel(axis_names[ax2])

			# Output
			if output_files[config_name] is not None:
				plt.savefig(output_files[config_name])
			else:
				plt.savefig(f"{config['name']} {render_name}.png")
			if config["show"]:
				plt.show()

if __name__ == '__main__':
	parser = argparse.ArgumentParser("EM Field Visualizer")
	parser.add_argument("--conf", "-f", nargs=1, type=str, default=[None], help="Configuration file", dest="config")
	parser.add_argument("--safety", "-s", nargs=1, type=int, default=[0], help="Eval safety level: 0 prevents all evaluation, 1 allows evaluation of functions in a whitelist, 2 allows for evaluation of arbitrary functions; default 0", dest="safety")
	parser.add_argument("--eout", nargs=1, type=str, default=[None], help="Output file for electric field plot", dest="eout")
	parser.add_argument("--bout", nargs=1, type=str, default=[None], help="Output file for magnetic field plot", dest="bout")

	args = parser.parse_args()

	eval_safety = args.safety[0]
	output_files["e-field"] = args.eout[0]
	output_files["b-field"] = args.bout[0]

	config_file = args.config[0]
	if config_file is None:
		print("No configuration file provided. Terminating.")
	else:
		config = None
		try:
			with open(config_file) as data:
				config = json.load(data)
		except Exception as e:
			print(f"Failed to read configuration file.\nError: {e}\nTerminating.")
		else:
			config["name"] = config_file[:config_file.rfind('.')]
			config = complete_config(config)
			visualize_fields(config)
