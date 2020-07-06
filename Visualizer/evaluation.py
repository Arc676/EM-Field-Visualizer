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

import ast
import operator
import numpy as np

numpy_functions = dict(
	sin=np.sin,
	cos=np.cos,
	tan=np.tan,
	abs=np.abs,
	norm=np.linalg.norm
)

numpy_variables = dict(
	pi=np.pi,
	e=np.e
)

# Evaluation by Aleksi Torhamo
# https://stackoverflow.com/a/30134081/2773311

ast_operations = {
	ast.Add: operator.add,
	ast.Sub: operator.sub,
	ast.Mult: operator.mul,
	ast.Div: operator.truediv,
	ast.FloorDiv: operator.floordiv,
	ast.Pow: operator.pow,
}

def _safe_eval(node, variables, functions):
        if isinstance(node, ast.Num):
                return node.n
        elif isinstance(node, ast.Name):
                return variables[node.id] # KeyError -> Unsafe variable
        elif isinstance(node, ast.BinOp):
                op = ast_operations[node.op.__class__] # KeyError -> Unsafe operation
                left = _safe_eval(node.left, variables, functions)
                right = _safe_eval(node.right, variables, functions)
                if isinstance(node.op, ast.Pow):
                        assert right < 100
                return op(left, right)
        elif isinstance(node, ast.Call):
                assert not node.keywords
                assert isinstance(node.func, ast.Name), 'Unsafe function derivation'
                func = functions[node.func.id] # KeyError -> Unsafe function
                args = [_safe_eval(arg, variables, functions) for arg in node.args]
                return func(*args)

        assert False, 'Unsafe operation'

def safe_eval(expr, variables={}, functions={}):
        node = ast.parse(expr, '<string>', 'eval').body
        return _safe_eval(node, variables, functions)
