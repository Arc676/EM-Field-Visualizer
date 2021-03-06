// Copyright (C) 2020 Arc676/Alessandro Vinciguerra <alesvinciguerra@gmail.com>

// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation (version 3)

// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
// GNU General Public License for more details.

// You should have received a copy of the GNU General Public License
// along with this program. If not, see <http://www.gnu.org/licenses/>.
// See README and LICENSE for more details.

#ifndef EDITOR_H
#define EDITOR_H

#include <stdio.h>
#include <stdlib.h>

#include <fstream>

#include "imgui.h"
#include "imgui_impl_glfw.h"
#include "imgui_impl_opengl3.h"

#include <GL/glew.h>
#include <GLFW/glfw3.h>

#include "json.hpp"

using Vec3 = std::array<float, 3>;
using Vec4 = std::array<float, 4>;

using DVecF = std::vector<std::vector<float>>;

char ioMessage[255] = "Enter a filename to read or save";

Vec3 plotMargins = {{5, 5, 5}};

bool plotEField = true;
bool plotBField = true;

int planeAxis = 2;
float planeCoordinate = 0;

bool showPlots = false;

bool inferPlotBounds = true;
struct PlotBounds {
	Vec3 min = {{0, 0, 0}};
	Vec3 max = {{0, 0, 0}};
} plotBounds;

int resolution = 100;
char colormapbuf[50] = "cool";
std::string colormap;

std::vector<Vec4> charges;

struct ChargeDensityFunc {
	bool isPreset = true;
	float scale = 1;
	union {
		int preset = 0;
		char func[100];
	};
	char var[5] = "r";
	float value = 1;
	Vec3 offset = {{0, 0, 0}};
};

std::vector<ChargeDensityFunc> chargeDensities;

#define PRESET_COUNT 3
const char* presetFunctions[] = {
	"Delta (var == val)", "Heaviside (var > val)", "Reverse Heaviside (var < val)"
};

#endif
