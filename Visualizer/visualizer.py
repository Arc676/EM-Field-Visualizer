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
import matplotlib.pyplot as plt
import argparse
import json

def complete_config(config):
	# Default plot margins
	if "plot-margins" not in config:
		config["plot-margins"] = {"0": 5, "1": 5, "2": 5}
	# Plot both fields by default
	for field in ["b-field", "e-field"]:
		if "plot" not in config[field]:
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
		config["plot-bounds"] = {"min": coords_min, "max": coords_max}
	# Default resolution
	if "resolution" not in config:
		config["resolution"] = 100
	return config

def visualize_fields(config):
	config = complete_config(config)
	axes = []
	for i in range(3):
		if i == config["plane"]["axis"]:
			axes.append([config["plane"]["coordinate"]])
		else:
			x_min, x_max = config["plot-bounds"]["min"][i], config["plot-bounds"]["max"][i]
			x_min -= config["plot-margins"][str(i)]
			x_max += config["plot-margins"][str(i)]
			axis = np.linspace(x_min, x_max, config["resolution"] * (x_max - x_min))
			axes.append(axis)
	space = np.array(np.meshgrid(*axes))

	axis_names = ["x", "y", "z"]
	plotted_axes = [0,1,2]
	plotted_axes.pop(config["plane"]["axis"])
	ax1, ax2 = plotted_axes
	e_field, b_field = np.zeros_like(space), np.zeros_like(space)

	if "charges" in config:
		charges = np.array(config["charges"])
		plt.figure("E-Field")
		for charge in charges:
			xy = (charge[1 + ax1], charge[1 + ax2])
			plt.plot(*xy, 'ro')
			plt.annotate(f"{charge[0]} C", xy=xy, xytext=(10,5), ha='right', textcoords='offset points')
		def efield_charges(x):
			E = np.zeros_like(x)
			for charge in charges:
				s = (x.T - charge[1:]).T
				E += charge[0] * s / np.linalg.norm(s, axis=0) ** 3
			return E
		e_field += efield_charges(space)

	for field_name, field in zip(["e", "b"], [e_field, b_field]):
		if config[f"{field_name}-field"]["plot"]:
			render_name = f"{field_name.upper()}-Field"
			plt.figure(render_name)
			plt.streamplot(axes[ax1], axes[ax2], field[ax1].T[0].T, field[ax2].T[0].T)
			plt.title(render_name)
			plt.xlabel(axis_names[ax1])
			plt.ylabel(axis_names[ax2])
			plt.savefig(f"{config['name']} {render_name}.png")
			if config["show"]:
				plt.show()

if __name__ == '__main__':
	parser = argparse.ArgumentParser("EM Field Visualizer")
	parser.add_argument("--conf", "-f", nargs=1, type=str, default=[None], help="Configuration file", dest="config")

	args = parser.parse_args()

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
			visualize_fields(config)
