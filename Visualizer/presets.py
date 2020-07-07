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

import numpy.linalg as nl

PRESET_DELTA = 0
PRESET_HEAVISIDE = 1
PRESET_REVERSE_HEAVISIDE = 2

def norm(*xi):
	return nl.norm([*xi])

def get_variable(var):
	if var == "x":
		return lambda z, y, x: x
	elif var == "y":
		return lambda z, y, x: y
	elif var == "z":
		return lambda z, y, x: z
	elif var == "r":
		return lambda z, y, x: norm(x, y, z)
	elif var == "rc":
		return lambda z, y, x: norm(x, y)
	elif var == "theta":
		return lambda z, y, x: np.acos(z / norm(x, y, z))
	elif var == "phi":
		return lambda z, y, x: np.acos(x / norm(x, y))

def offset_var(var, offset):
	if offset != 0:
		return lambda z, y, x: var(z + offset[2], y + offset[1], x + offset[0])
	return var

def delta(variable, value, offset, tolerance):
	var = offset_var(get_variable(variable), offset)
	return lambda z, y, x: 100 if nl.norm(var(z, y, x) - value) < tolerance else 0

def heaviside(variable, value, offset, reverse):
	var = offset_var(get_variable(variable), offset)
	if reverse:
		return lambda z, y, x: var(z, y, x) < value
	else:
		return lambda z, y, x: var(z, y, x) > value

def get_preset(density_func):
	scale = density_func.get("scale", 1)
	func = density_func["func"]
	var = density_func["var"]
	val = density_func["value"]
	offset = density_func.get("offset", 0)
	tolerance = density_func.get("tol", 0.15)
	if func == PRESET_DELTA:
		d = delta(var, val, offset, tolerance)
		return lambda z, y, x: scale * d(z, y, x)
	elif func in [PRESET_HEAVISIDE, PRESET_REVERSE_HEAVISIDE]:
		h = heaviside(var, val, offset, func == PRESET_REVERSE_HEAVISIDE)
		return lambda z, y, x: scale * h(z, y, x)
