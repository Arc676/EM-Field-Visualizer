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
#include <string>

#include "imgui.h"
#include "imgui_impl_glfw.h"
#include "imgui_impl_opengl3.h"

#include <GL/glew.h>
#include <GLFW/glfw3.h>

float plotMargins[] = {5, 5, 5};

bool plotEField = true;
bool plotBField = true;

int planeAxis = 2;
float planeCoordinate = 0;

bool showPlots = false;

bool inferPlotBounds = true;
float plotBounds[2][3] = {
	{0,0,0}, {0,0,0}
};

int resolution = 100;

#endif
