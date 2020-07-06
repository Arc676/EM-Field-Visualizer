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

#include "editor.h"

void glfwErrorCallback(int error, const char* description) {
	fprintf(stderr, "GLFW error %d: %s\n", error, description);
}

void readParameters(const char* filename) {
	nlohmann::json params;
	std::ifstream ifs(filename);
	ifs >> params;
	ifs.close();

	if (params.contains("plot-margins")) {
		std::vector<float> margins = params["plot-margins"].get<std::vector<float>>();
		std::copy_n(margins.begin(), 3, plotMargins.begin());
	}
	if (params.contains("e-field") && params["e-field"].contains("plot")) {
		plotEField = params["e-field"]["plot"];
	}
	if (params.contains("b-field") && params["b-field"].contains("plot")) {
		plotBField = params["b-field"]["plot"];
	}
	if (params.contains("plane")) {
		planeAxis = params["plane"]["axis"];
		planeCoordinate = params["plane"]["coordinate"];
	}
	if (params.contains("show")) {
		showPlots = params["show"];
	}
	if (params.contains("plot-bounds")) {
		std::vector<float> minBounds = params["plot-bounds"]["min"].get<std::vector<float>>();
		std::copy_n(minBounds.begin(), 3, plotBounds.min.begin());
		std::vector<float> maxBounds = params["plot-bounds"]["max"].get<std::vector<float>>();
		std::copy_n(maxBounds.begin(), 3, plotBounds.max.begin());
		inferPlotBounds = false;
	} else {
		inferPlotBounds = true;
	}
	charges.clear();
	if (params.contains("charges")) {
		DVecF jsonCharges = params["charges"].get<DVecF>();
		for (auto it : jsonCharges) {
			Vec4 charge;
			std::copy_n(it.begin(), 4, charge.begin());
			charges.push_back(charge);
		}
	}
	if (params.contains("resolution")) {
		resolution = params["resolution"];
	}
	if (params.contains("colormap")) {
		colormap = params["colormap"];
		if (colormap.length() < 50) {
			std::copy(colormap.begin(), colormap.end(), colormapbuf);
		}
	}
	chargeDensities.clear();
	if (params.contains("charge-densities")) {
		for (auto rho : params["charge-densities"]) {
			ChargeDensityFunc density;
			density.isPreset = rho["preset"];
			if (density.isPreset) {
				density.scale = rho["scale"];
				density.value = rho["value"];
				density.preset = rho["func"];
				std::string var = rho["var"];
				if (var.length() < 5) {
					std::copy(var.begin(), var.end(), density.var);
				} else {
					continue;
				}
			} else {
				std::string func = rho["func"];
				if (func.length() < 100) {
					std::copy(func.begin(), func.end(), density.func);
				} else {
					continue;
				}
			}
			chargeDensities.push_back(density);
		}
	}
}

void writeParameters(const char* filename) {
	colormap = std::string(colormapbuf);
	nlohmann::json params = {
		{"plot-margins", plotMargins},
		{"e-field", {{"plot", plotEField}}},
		{"b-field", {{"plot", plotBField}}},
		{"plane", {
			{"axis", planeAxis},
			{"coordinate", planeCoordinate}}
		},
		{"show", showPlots},
		{"resolution", resolution},
		{"colormap", colormap}
	};
	if (!inferPlotBounds) {
		params["plot-bounds"] = {
			{"min", plotBounds.min},
			{"max", plotBounds.max}
		};
	}
	if (charges.size() > 0) {
		params["charges"] = charges;
	}
	if (chargeDensities.size() > 0) {
		nlohmann::json densities;
		for (auto rho : chargeDensities) {
			nlohmann::json density;
			density["preset"] = rho.isPreset;
			if (rho.isPreset) {
				density["scale"] = rho.scale;
				density["func"] = rho.preset;
				density["var"] = rho.var;
				density["value"] = rho.value;
			} else {
				density["func"] = rho.func;
			}
			densities.push_back(density);
		}
		params["charge-densities"] = densities;
	}
	std::ofstream ofs(filename);
	ofs << params.dump(4);
	ofs.close();
}

int main() {
	glfwSetErrorCallback(glfwErrorCallback);
	if (!glfwInit()) {
		return 1;
	}
	#ifdef __APPLE__
	const char* glslVersion = "#version 150";
	glfwWindowHint(GLFW_CONTEXT_VERSION_MAJOR, 3);
	glfwWindowHint(GLFW_CONTEXT_VERSION_MINOR, 2);
	glfwWindowHint(GLFW_OPENGL_PROFILE, GLFW_OPENGL_CORE_PROFILE);

	#else
	const char* glslVersion = "#version 130";
	glfwWindowHint(GLFW_CONTEXT_VERSION_MAJOR, 3);
	glfwWindowHint(GLFW_CONTEXT_VERSION_MINOR, 0);

	#endif

	glfwWindowHint(GLFW_OPENGL_FORWARD_COMPAT, GL_TRUE);

	GLFWwindow* window = glfwCreateWindow(700, 600, "Electro-/Magnetostatics Editor", NULL, NULL);
	if (!window) {
		return 1;
	}
	glfwMakeContextCurrent(window);
	glfwSwapInterval(1);
	if (glewInit() != GLEW_OK) {
		fprintf(stderr, "Failed to initialize OpenGL loader\n");
		return 1;
	}

	IMGUI_CHECKVERSION();
	ImGui::CreateContext();
	ImGui::StyleColorsDark();
	ImGui_ImplGlfw_InitForOpenGL(window, true);
	ImGui_ImplOpenGL3_Init(glslVersion);
	while (!glfwWindowShouldClose(window)) {
		glfwPollEvents();

		ImGui_ImplOpenGL3_NewFrame();
		ImGui_ImplGlfw_NewFrame();
		ImGui::NewFrame();

		ImGui::SetNextWindowPos(ImVec2(0, 0), ImGuiCond_FirstUseEver);
		ImGui::SetNextWindowSize(ImVec2(700, 600), ImGuiCond_FirstUseEver);

		if (ImGui::Begin("Editor")) {
			if (ImGui::CollapsingHeader("Electrostatics")) {
				if (ImGui::Button("Add charge")) {
					std::array<float, 4> charge = {0,0,0,0};
					charges.push_back(charge);
				}
				int i = 0;
				char buf[100];
				for (auto it = charges.begin(); it != charges.end();) {
					sprintf(buf, "##Q%d", i);
					ImGui::Text("Charge (q, x, y, z)");
					ImGui::InputFloat4(buf, it->data(), "%g", 0);
					ImGui::SameLine();
					sprintf(buf, "Delete charge##DelQ%d", i);
					if (ImGui::Button(buf)) {
						charges.erase(it);
					} else {
						it++;
						i++;
					}
				}
				if (ImGui::Button("Add charge density function")) {
					ChargeDensityFunc rho;
					chargeDensities.push_back(rho);
				}
				i = 0;
				for (auto it = chargeDensities.begin(); it != chargeDensities.end();) {
					sprintf(buf, "Use preset function##Rho%d", i);
					ImGui::Checkbox(buf, &(it->isPreset));
					if (it->isPreset) {
						sprintf(buf, "Preset##Rho%d", i);
						ImGui::Combo(buf, &(it->preset), presetFunctions, PRESET_COUNT);
						ImGui::Text("Variable (x, y, z, r, theta, phi, rc)");
						ImGui::SameLine();
						sprintf(buf, "##RhoVar%d", i);
						ImGui::InputText(buf, it->var, 5, 0);
						ImGui::Text("Value");
						ImGui::SameLine();
						sprintf(buf, "##RhoVal%d", i);
						ImGui::InputFloat(buf, &(it->value));
					} else {
						ImGui::Text("rho(x,y,z/r,theta,phi/rc,phi,z) = ");
						sprintf(buf, "##Rho%d", i);
						ImGui::InputText(buf, it->func, 100, 0);
					}
					sprintf(buf, "Delete charge density function##DelRho%d", i);
					if (ImGui::Button(buf)) {
						chargeDensities.erase(it);
					} else {
						it++;
						i++;
					}
				}
			}
			if (ImGui::CollapsingHeader("Plane of interest")) {
				ImGui::Text("Plot fields in which plane?");
				ImGui::RadioButton("XY", &planeAxis, 2);
				ImGui::SameLine();
				ImGui::RadioButton("XZ", &planeAxis, 1);
				ImGui::SameLine();
				ImGui::RadioButton("YZ", &planeAxis, 0);

				ImGui::Text("Coordinate on nonplanar axis");
				ImGui::SameLine();
				ImGui::InputFloat("##ZCoord", &planeCoordinate);
			}
			if (ImGui::CollapsingHeader("Plot")) {
				ImGui::InputText("Color Map", colormapbuf, 50, 0);
				ImGui::Checkbox("Plot electric field", &plotEField);
				ImGui::Checkbox("Plot magnetic field", &plotBField);
				ImGui::Checkbox("Show plots after saving", &showPlots);
				ImGui::Text("Plot margins (X, Y, Z)");
				ImGui::InputFloat3("##PlotMargins", plotMargins.data(), "%g", 0);
				ImGui::Checkbox("Infer plot bounds", &inferPlotBounds);
				if (!inferPlotBounds) {
					ImGui::Text("Plot bounds (minimum X, Y, Z)");
					ImGui::InputFloat3("##MinBounds", plotBounds.min.data(), "%g", 0);
					ImGui::Text("Plot bounds (maximum X, Y, Z)");
					ImGui::InputFloat3("##MaxBounds", plotBounds.max.data(), "%g", 0);
				}
				ImGui::Text("Plot resolution");
				ImGui::SameLine();
				ImGui::InputInt("##Res", &resolution);
			}
			if (ImGui::CollapsingHeader("Disk")) {
				static char filename[255];
				ImGui::Text("Filename");
				ImGui::SameLine();
				ImGui::InputText("##Filename", filename, 255, 0);
				ImGui::SameLine();
				if (ImGui::Button("Load")) {
					readParameters(filename);
				}
				ImGui::SameLine();
				if (ImGui::Button("Save")) {
					writeParameters(filename);
				}
			}
			if (ImGui::Button("Exit")) {
				break;
			}
		}
		ImGui::End();
		ImGui::Render();
		int displayW, displayH;
		glfwGetFramebufferSize(window, &displayW, &displayH);
		glViewport(0, 0, displayW, displayH);
		glClearColor(0, 0, 0, 1);
		glClear(GL_COLOR_BUFFER_BIT);
		ImGui_ImplOpenGL3_RenderDrawData(ImGui::GetDrawData());
		glfwSwapBuffers(window);
	}

	ImGui_ImplOpenGL3_Shutdown();
	ImGui_ImplGlfw_Shutdown();
	ImGui::DestroyContext();
	glfwDestroyWindow(window);
	glfwTerminate();

	return 0;
}
