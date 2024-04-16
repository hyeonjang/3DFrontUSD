import os, json, argparse
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor

os.environ['PXR_PLUGINPATH_NAME'] = os.getcwd() + (os.environ['PXR_PLUGINPATH_NAME'] if os.environ['PXR_PLUGINPATH_NAME'] else '')

import numpy as np
from tqdm import tqdm
from pxr import Usd, UsdGeom, UsdShade
from pxr import Sdf, Kind, Gf, Vt

def to_camel_case(text):
    words = text.replace('-', '').split()
    # Convert the first word to lowercase and the rest to title case
    camel_case_words = [words[0].capitalize()] + [word.capitalize() for word in words[1:]]
    # Join the words together
    camel_case_text = ''.join(camel_case_words)
    return camel_case_text

def encode_uuid_to_path(uuid_str):
    # Mapping for hexadecimal to alphabet
    hex_to_alpha = {
        '0': 'A', '1': 'B', '2': 'C', '3': 'D',
        '4': 'E', '5': 'F', '6': 'G', '7': 'H',
        '8': 'I', '9': 'J',
    }
    # Remove dashes and encode
    return ''.join(hex_to_alpha.get(char, char) for char in uuid_str)

def decode_path_to_uuid(encoded_str):
    # Mapping for alphabet back to hexadecimal
    alpha_to_hex = {
        'A': '0', 'B': '1', 'C': '2', 'D': '3',
        'E': '4', 'F': '5', 'G': '6', 'H': '7',
        'I': '8', 'J': '9', 
    }
    # Decode back, assuming standard UUID length after removing dashes
    decoded = ''.join(alpha_to_hex.get(char, char) for char in encoded_str)
    return decoded

from scipy.spatial.transform import Rotation as R

class FrontToUSD():
    def __init__(self, path, directory, debug=False):
        # mkdir /scene dir
        self.source_directory = directory
        self.target_directory = path.parent

        self.scene_directory = self.source_directory
        self.material_directory = self.source_directory/'texture'

        usd_path_base = f"{self.scene_directory}/{path.stem}"
        file_extension = '.usda' if debug else '.usd'
        usd_path = usd_path_base + file_extension

        # one usd per json
        self.stage = Usd.Stage.CreateNew(usd_path)
        with open(path, 'r') as file:
            data = json.load(file)
            self.scene = data["scene"]

        self.objects = data["furniture"]
        self.room_comps = data["mesh"] # mesh for wall, floor, ceil
        self.materials = data["material"] # material for wall, floor, ceils

        self.REFERENCE_ID = {}
        self.MATERIAL_ID = {}

    # real run
    def __call__(self):
        # @@ missing, Lux, incompleted materials
        self.add_materials_to_stage()
        self.add_prim_and_xform_to_stage()
        self.add_object_ref_to_stage()
        self.add_room_comp_to_stage()
        self.stage.Save()

    # 
    # methods
    # 
    def add_materials_to_stage(self):

        for mat in self.materials:

            texture_path = self.material_directory/f'{mat["jid"]}.png'
            if not texture_path.exists():
                continue

            prim_path = 'Materials'+ '/' + to_camel_case(mat.get("contentType", ["None", "None"])[1]) + f'{encode_uuid_to_path(mat["jid"].split("-")[0])}'
            self.MATERIAL_ID[mat['uid']] = prim_path

            # make material
            material_path = f'/{prim_path}'
            material = UsdShade.Material.Define(self.stage, material_path)
            material.CreateInput("stPrimvarName", Sdf.ValueTypeNames.Token).Set("st")
            
            # shadergraph
            nodegraph_path = material_path + "/UsdPreviewSurface"
            nodegraph = UsdShade.NodeGraph.Define(self.stage, nodegraph_path)

            # texcoord
            texcoordreader_path = nodegraph_path + "/texCoordReader"
            texcoordreader = UsdShade.Shader.Define(self.stage, texcoordreader_path)
            texcoordreader.CreateIdAttr("UsdPrimvarReader_float2")
            texcoordreader.CreateInput("varname", Sdf.ValueTypeNames.Token).ConnectToSource(material.GetInput("stPrimvarName"))
            texcoordreader.CreateOutput("result", Sdf.ValueTypeNames.Float2)

            # texture
            diffuseColor_path = nodegraph_path + "/diffuseColor"
            diffuseColor = UsdShade.Shader.Define(self.stage, diffuseColor_path)
            diffuseColor.CreateIdAttr("UsdUVTexture")
            diffuseColor.CreateInput("file", Sdf.ValueTypeNames.Asset).Set(f'./texture/{mat["jid"]}.png')
            diffuseColor.CreateInput("st", Sdf.ValueTypeNames.Float2).ConnectToSource(texcoordreader.GetOutput("result"))
            diffuseColor.CreateInput("wrapS", Sdf.ValueTypeNames.Token).Set("repeat")
            diffuseColor.CreateInput("wrapT", Sdf.ValueTypeNames.Token).Set("repeat")
            diffuseColor.CreateOutput("rgb", Sdf.ValueTypeNames.Float3)

            # material
            usdPreviewSurface_path = nodegraph_path + "/UsdPreviewSurface"
            usdPreviewSurface = UsdShade.Shader.Define(self.stage, usdPreviewSurface_path)
            usdPreviewSurface.CreateIdAttr("UsdPreviewSurface")
            usdPreviewSurface.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).ConnectToSource(diffuseColor.GetOutput("rgb"))
            usdPreviewSurface.CreateOutput("surface", Sdf.ValueTypeNames.Token)

            material.CreateOutput("surface", Sdf.ValueTypeNames.Token).ConnectToSource(f"{usdPreviewSurface_path}.outputs:surface")

    # xform
    def xform_to_prim(self, prim, dictionary):
        xformable = UsdGeom.Xformable(prim)
        
        # reset XformOpOrder
        xformable.SetXformOpOrder([])

        # translates the model based on the model info.
        rotation = dictionary.get('rot', [0, 0, 0, 1])
        rot = np.array(rotation)
        quaternion = R.from_quat(rot)
        euler_angles_degrees = quaternion.as_euler('xyz', degrees=True)

        # add as the original sequence in 3D future reader
        scale = dictionary.get('scale', [1, 1, 1])
        xformable.AddScaleOp().Set(Gf.Vec3f(scale))

        translate = dictionary.get('pos', [1, 1, 1])
        xformable.AddTranslateOp().Set(Gf.Vec3f(translate))
        xformable.AddRotateXYZOp().Set(Gf.Vec3f(list(euler_angles_degrees))) 

    # prim
    def add_prim_and_xform_to_stage(self):
        root_prim = self.stage.DefinePrim('/Scene', 'Xform')
        self.xform_to_prim(root_prim, self.scene)

        # starting from the root, instantiate prim and add a proper Xform transformation
        for rooms in self.scene["room"]:

            # global transformation
            rooms_name = 'Scene/' + rooms["instanceid"].replace("-", "")
            rooms_prim = self.stage.DefinePrim(f'/{rooms_name}', "Xform")
            self.xform_to_prim(rooms_prim, rooms)

            # for each room
            for room in rooms["children"]:

                instances = room['instanceid'].split('/')                
                prim_path = f'{rooms_name}'
                for instance in instances:
                    prim_path += "/" + encode_uuid_to_path(instance)
                    room_prim = self.stage.DefinePrim(f'/{prim_path}', 'Xform')

                self.REFERENCE_ID[room['ref']] = prim_path
                self.xform_to_prim(room_prim, room)

                # set group kind
                model = Usd.ModelAPI(room_prim)
                model.SetKind(Kind.Tokens.group)

    # add furniture to scene as reference
    def add_object_ref_to_stage(self):
        for object in self.objects:
            path = self.REFERENCE_ID.get(object['uid'])
            if path is None:
                continue
            if "valid" in object and object["valid"]:
                ref_prim = self.stage.GetPrimAtPath(f'/{path}')
                ref_prim.GetReferences().AddReference(f'./model/{object["jid"]}/raw_model.usd')
            else:
                self.stage.RemovePrim(path)
                
    # read room mesh (wall, ceil, floor) and convert to usd
    def add_room_comp_to_stage(self):
        for room_comp in self.room_comps:

            # object-level wall, floor, and someting
            path = self.REFERENCE_ID[room_comp['uid']]

            # real mesh from data 
            # processing mesh
            mesh = self.stage.DefinePrim(f'/{path}', "Mesh")

            # set material
            mtl_path = self.MATERIAL_ID.get(room_comp['material'], None)
            if mtl_path is not None:
                mtl = UsdShade.Material(self.stage.GetPrimAtPath(f'/{mtl_path}'))
                UsdShade.MaterialBindingAPI.Apply(mesh).Bind(mtl)

            # set metadata
            model = Usd.ModelAPI(mesh)
            model.SetKind(Kind.Tokens.component)

            mesh = self.stage.GetPrimAtPath(f'/{path}')
            mesh.SetMetadata('category', room_comp['type'])

            # reassign to call API
            mesh = UsdGeom.Mesh(mesh)
            verts = np.array(room_comp['xyz'], dtype=float).reshape(-1, 3)
            faces = np.array(room_comp['faces'], dtype=int).reshape(-1, 3)

            mesh.GetPointsAttr().Set(Vt.Vec3fArray.FromNumpy(verts))
            mesh.GetFaceVertexIndicesAttr().Set(faces)

            vertexCounts = Vt.IntArray([3] * faces.shape[0])
            mesh.GetFaceVertexCountsAttr().Set(vertexCounts)

            # Add UVs
            uvs = room_comp.get('uv')
            if uvs:
                uvs = np.array(uvs, dtype=float).reshape(-1, 2)  # Ensure it's an Nx2 array for UVs

                min_vals = uvs.min(axis=0)
                max_vals = uvs.max(axis=0)

                # Normalize the UVs to [0, 1] range
                normalized_uvs = 1 - (uvs - min_vals) / (max_vals - min_vals)

                uvPrimvar = UsdGeom.PrimvarsAPI(mesh).CreatePrimvar("st", Sdf.ValueTypeNames.TexCoord2fArray, UsdGeom.Tokens.vertex)
                uvPrimvar.Set(Vt.Vec2fArray(normalized_uvs.tolist()))
                uvPrimvar.SetIndices(Vt.IntArray(room_comp['faces']))

# 
# execution
# 
def sequence_excute(indir, outdir, Class):
    pathlist = list(Path(indir).glob("*"))
    new_directory = Path(outdir)

    for path in tqdm(pathlist):      
        function = Class(path, new_directory)
        function()
    return

# not working
def parellal_excute(indir, outdir, function):
    pathlist = list(Path(indir).glob("*"))
    new_directory = Path(outdir)

    with ProcessPoolExecutor() as executor:
        executor.map(function, [path for path in pathlist if path.is_dir()], [str(new_directory)]*len(list(pathlist)))

def convert_scene(indir, outdir):
    outdir = Path(outdir)
    outdir.mkdir(exist_ok=True, parents=True)
    sequence_excute(indir, outdir, FrontToUSD)
    return

parser = argparse.ArgumentParser()
parser.add_argument('-i', help='3D front dataset folder')
parser.add_argument('-o', help='Your USD output path')
args = parser.parse_args()

if __name__ == "__main__": 
    convert_scene(args.i, args.o)