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
}

void writeParameters(const char* filename) {
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
				//
			}
			if (ImGui::CollapsingHeader("Plane of interest")) {
				ImGui::Text("Plot fields in which plane?");
				ImGui::RadioButton("XY", &planeAxis, 2);
				ImGui::SameLine();
				ImGui::RadioButton("XZ", &planeAxis, 1);
				ImGui::SameLine();
				ImGui::RadioButton("YZ", &planeAxis, 0);

				ImGui::Text("Coordinate on remaining axis");
				ImGui::SameLine();
				ImGui::InputFloat("##ZCoord", &planeCoordinate);
			}
			if (ImGui::CollapsingHeader("Plot")) {
				ImGui::Checkbox("Plot electric field", &plotEField);
				ImGui::Checkbox("Plot magnetic field", &plotBField);
				ImGui::Checkbox("Show plots after saving", &showPlots);
				ImGui::Text("Plot margins (X, Y, Z)");
				ImGui::InputFloat3("##PlotMargins", plotMargins, "%g", 0);
				ImGui::Checkbox("Infer plot bounds", &inferPlotBounds);
				if (!inferPlotBounds) {
					ImGui::Text("Plot bounds (minimum X, Y, Z)");
					ImGui::InputFloat3("##MinBounds", plotBounds[0], "%g", 0);
					ImGui::Text("Plot bounds (maximum X, Y, Z)");
					ImGui::InputFloat3("##MaxBounds", plotBounds[1], "%g", 0);
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
