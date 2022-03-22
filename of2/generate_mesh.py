import getopt, sys
import numpy as np
from datetime import date
import os, getpass
class Vertex:
	def __init__(self, x, y, z, index):
		self.x = x
		self.y = y
		self.z = z
		self.index = index
	
	def print(self):
		print("\t({} {} {}) // {}".format(self.x, self.y, self.z, self.index))

class Block:
	def __init__(self, vertices, meshing, grading, index):
		self.vertices = [str(vertex) for vertex in vertices]
		self.meshing = [str(mesh) for mesh in meshing]
		self.grading = [str(grade) for grade in grading]
		self.index = index
	
	def print(self):
		print("\t// block {}".format(self.index))
		print("\thex ({}) ({}) simpleGrading ({})".format(" ".join(self.vertices), " ".join(self.meshing), " ".join(self.grading)))

class Arc:
	def __init__(self, begin_idx, end_idx, midpoint):
		self.begin = begin_idx
		self.end = end_idx
		self.midpoint = [str(coord) for coord in midpoint]
	
	def print(self):
		print("\tarc {} {} ({})".format(self.begin, self.end, " ".join(self.midpoint)))
	
class CylinderMesh:
	def __init__(self, Lf, Lw, H, R):
		self.Lf = Lf
		self.Lw = Lw
		self.H = H
		self.R = R
		self.vertices = list()
		self.blocks = list()
		self.arcs = list()
		self.z_offset = 32
		self.init_mesh()
		
	
	def init_mesh(self):
		self.init_vertices()
		self.init_blocks()
		self.boundary_string = """
boundary
(

  inlet
  {
      type patch;
      faces
      (
         (22 54 55 23)
         (23 55 56 24)
         (24 56 57 25)
         (25 57 58 26)
      );
  }

  outlet
  {
      type patch;
      faces
      (
         (18 50 49 17)
         (17 49 48 16)
         (16 48 63 31)
         (31 63 62 30)
      );
  }

  cylinder
  {
      type wall;
      faces
      (
         (0 32 33 1)
         (1 33 34 2)
         (2 34 35 3)
         (3 35 36 4)
         (4 36 37 5)
         (5 37 38 6)
         (6 38 39 7)
         (7 39 32 0)
      );
  }

  top
  {
      type symmetryPlane;
      faces
      (
         (22 54 53 21)
         (21 53 52 20)
         (20 52 51 19)
         (19 51 50 18)
      );
  }

  bottom
  {
      type symmetryPlane;
      faces
      (
         (26 58 59 27)
         (27 59 60 28)
         (28 60 61 29)
         (29 61 62 30)
      );
  }

);
"""

	def init_vertices(self):
		for z_idx in range(2):
			for k in range(32):
				index = len(self.vertices)
				z = z_idx*0.1-0.05
				if k < 8:
					x = 0.5*np.cos(k*np.pi/4)
					y = 0.5*np.sin(k*np.pi/4)
					arc_midpoint = [0.5*np.cos(k*np.pi/4 + np.pi/8), 0.5*np.sin(k*np.pi/4 + np.pi/8), z]
					if k+1 < 8:
						self.arcs.append(Arc(index, index+1, arc_midpoint))
					else:
						self.arcs.append(Arc(index, index-7, arc_midpoint))
				elif k < 16:
					x = (self.R)*np.cos(k*np.pi/4)
					y = (self.R)*np.sin(k*np.pi/4)
					arc_midpoint = [self.R*np.cos(k*np.pi/4 + np.pi/8),self.R*np.sin(k*np.pi/4 + np.pi/8), z]
					if k+1 < 16:
						self.arcs.append(Arc(index, index+1, arc_midpoint))
					else:
						self.arcs.append(Arc(index, index-7, arc_midpoint))
				else:
					if k < 19 or k > 29:
						x = self.Lw
					if k < 23 and k > 17:
						y = self.H
					if k > 21 and k < 27:
						x = -1*self.Lf
					if k > 25 and k < 31:
						y = -1*self.H
					if k == 16 or k == 24:
						y = 0
					if k == 17 or k == 23:
						y = self.vertices[9].y
					if k == 19 or k == 29:
						x = self.vertices[9].x
					if k == 20 or k == 28:
						x = 0
					if k == 21 or k == 27:
						x = self.vertices[13].x
					if k == 25 or k == 31:
						y = self.vertices[13].y
				if abs(x) < 0.00000000001:
					x = 0
				if abs(y) < 0.00000000001:
					y = 0
				self.vertices.append(Vertex(x,y,z,index))

	def init_blocks(self):
		# for circular portion: x1 = radial, x2 = tangential
		n_radial = 10
		n_tangential = 20
		n_z = 1
		n_corner_blocks_y = 30
		n_front_corners_x = 15
		n_wake_corners_x = 30
		# grading
		radial_grading = 2
		tangential_grading = 1
		z_grading = 1
		corners_y_grading = 4
		front_grading_x = 4
		wake_grading_x = 4
		for i in range(20):
			if i < 8: # radial blocks
				if i+1 < 8:
					vertices = [i, i+8, i+9, i+1]
				else:
					vertices = [i, i+8, i+1, i-7]
				num_cells = [n_radial, n_tangential, n_z]
				grading = [radial_grading, tangential_grading, z_grading]
			else: # outer blocks
				# corner blocks
				if i == 9 or i == 18: # wake corners
					num_cells = [n_wake_corners_x, n_corner_blocks_y, n_z]
					grading = [wake_grading_x, corners_y_grading, z_grading]
					if i == 9:
						vertices = [9, 17, 18, 19]
					else: # i == 18
						vertices = [15, 31, 30, 29]
						# Convert to right-handed system
						vertices = [vertex+self.z_offset for vertex in vertices]
				elif i == 12 or i == 15: # front corners
					num_cells = [n_front_corners_x, n_corner_blocks_y, n_z]
					grading = [front_grading_x, corners_y_grading, z_grading]
					if i == 12:
						vertices = [11, 23, 22, 21]
						# Convert to right-handed system
						vertices = [vertex+self.z_offset for vertex in vertices]
					else: # i == 15
						vertices = [13, 25, 26, 27]
				else: # edge non-corner blocks
					grading = [0, tangential_grading, z_grading]
					num_cells = [0, n_tangential, n_z]
					if i == 10 or i == 11 or i== 16 or i == 17: # "Vertical" block
						grading[0] = corners_y_grading
						num_cells[0] = n_corner_blocks_y
						if i == 10:
							vertices = [10, 20, 19, 9]
							# Convert to right-handed system
							vertices = [vertex+self.z_offset for vertex in vertices]
						elif i == 11:
							vertices = [10, 20, 21, 11]
						elif i == 16:
							vertices = [14, 28, 27, 13]
							# Convert to right-handed system
							vertices = [vertex+self.z_offset for vertex in vertices]
						else: # i == 17
							vertices = [14, 28, 29, 15]
					else: # "Horizontal" blocks
						if i == 8 or i == 19: # wake blocks
							grading[0] = wake_grading_x
							num_cells[0] = n_wake_corners_x
							if i == 8:
								vertices = [8, 16, 17, 9]
							else: # i == 19
								vertices = [8, 16, 31, 15]
								# Convert to right-handed system
								vertices = [vertex+self.z_offset for vertex in vertices]
						else:
							grading[0] = front_grading_x
							num_cells[0] = n_front_corners_x
							if i == 13:
								vertices = [12, 24, 23, 11]
								# Convert to right-handed system
								vertices = [vertex+self.z_offset for vertex in vertices]
							else: # i == 14
								vertices = [12, 24, 25, 13]
			# Add second set of vertices
			if vertices[0] < 32:
				vertices.extend([vertex+self.z_offset for vertex in vertices])
			else:
				vertices.extend([vertex-self.z_offset for vertex in vertices])
				
			b = Block(vertices, num_cells, grading, i)
			self.blocks.append(b)
	
	def print(self):
		print("// Mesh generated on ", date.today())
		print("// Mesh generated using the file: {}".format(os.path.abspath(__file__)))
		print("// Generated by the user: {}".format(getpass.getuser()))
		print("\n")
		print("// Parameters:")
		print("// Lf (fore)  = {}".format(str(self.Lf)))
		print("// Lw (wake)  = {}".format(str(self.Lw)))
		print("// R  (outer) = {}".format(str(self.R)))
		print("// H (top/bottom) = {}".format(str(self.H)))
		print(
"""
FoamFile
{
    version  2.0;
    format   ascii;
    class    dictionary;
    object   blockMeshDict;
}

convertToMeters 1.0;

vertices
("""
		)
		for vertex in self.vertices:
			vertex.print()
		print(
"""
);

blocks
(
"""
		)
		for block in self.blocks:
			block.print()
		print(
"""
);
edges
(
"""
		)
		for arc in self.arcs:
			arc.print()
		print(");")
		print(self.boundary_string)


if __name__ == "__main__":
	# Extract command line arguments
	argumentList = sys.argv[1:]
	options = "f:w:H:R:"
	long_options = ["length_front", "length_wake", "height", "outer_radius"]

	try:
		arguments, values = getopt.getopt(argumentList, options, long_options)

	except getopt.error as err:
		print(str(err))
		exit()

	for curArg, curVal in arguments:
		if curArg in ("-f", "--length_front"):
			Lf = float(curVal)
		elif curArg in ("-w", "--length_wake"):
			Lw = float(curVal)
		elif curArg in ("-H", "--height"):
			H = float(curVal)
		elif curArg in ("-R", "--outer_radius"):
			R = float(curVal)
	mesh = CylinderMesh(Lf, Lw, H, R)
	with open('blockMeshDict','w') as f:
		sys.stdout = f
		mesh.print()
