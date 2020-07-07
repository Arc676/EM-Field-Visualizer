#!/usr/bin/env python3
# Copyright (C) 2020 Arc676/Alessandro Vinciguerra <alesvinciguerra@gmail.com>

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
from scipy.integrate import tplquad
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
	z = config["plane"]["coordinate"]
	axes = []
	for i in range(3):
		if i == ax3:
			axes.append([z])
		else:
			x_min, x_max = config["plot-bounds"]["min"][i], config["plot-bounds"]["max"][i]
			x_min -= config["plot-margins"][i]
			x_max += config["plot-margins"][i]
			axis = np.linspace(x_min, x_max, config["resolution"] * (x_max - x_min))
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
			ax, ay, az = axes[0][0], axes[1][0], axes[2][0]
			bx, by, bz = axes[0][-1], axes[1][-1], axes[2][-1]
			if ax == bx:
				ax, bx = ay, by
			elif ay == by:
				ay, by = ax, bx
			elif az == bz:
				az, bz = ax, bx
			if density_func["preset"]:
				rho = presets.get_preset(density_func)
				if density_func["func"] == presets.PRESET_DELTA and
					density_func["var"] in ["x", "y", "z"]:
					x, t = density_func["value"], density_func.get("tol", 0.15) + 0.1
					a, b = x - t, x + t
					if density_func["var"] == "x":
						ax, bx = a, b
					elif density_func["var"] == "y":
						ay, by = a, b
					else:
						az, bz = a, b
			else:
				rho = construct_function(eval_safety, density_func["func"])
			list_charge_densities.append(rho)
			def integrand(z, y, x, Xx, Xy, Xz, axis):
				X = np.array([Xx, Xy, Xz])
				Y = np.array([x, y, z])
				v = X - Y
				return rho(z, y, x) * v[axis] / (np.linalg.norm(v) ** 3 + 1e-6)
			def grid_integral(f, x0, x1, y0, y1, z0, z1, *args):
				return np.vectorize(
					lambda z, y, x: tplquad(
						f, x0, x1, y0, y1, z0, z1,
						args=(z, y, x) + args,
						epsabs=0.5
					)[0] if rho(z, y, x) == 0 else 0
				)
			for axis in range(3):
				e_field[axis] += grid_integral(
					integrand,
					ax, bx, ay, by, az, bz,
					axis
				)(space[2], space[1], space[0])

	# Determine overall charge density distribution
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
					plt.plot(*xy, 'ro')
					plt.annotate(f"{charge[0]} C", xy=xy, xytext=(10,5), ha='right', textcoords='offset points')

			# Plot charge densities
			plt.contourf(axes[ax1], axes[ax2], overall_charge_density.T[0].T, cmap=plt.cm.Reds)

			# Plot field
			fx, fy = field[ax1].T[0].T, field[ax2].T[0].T
			color = 2 * np.log(np.hypot(fx, fy) + 1e-6)
			try:
				plt.streamplot(axes[ax1], axes[ax2], fx, fy, color=color, cmap=plt.get_cmap(config["colormap"]))
			except ValueError as e:
				print(f"Failed to plot {render_name}: {e}")

			# Plot labels
			plt.title(f"{render_name} ({axis_names[ax3]} = {z})")
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
