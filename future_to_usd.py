import os, json, logging, argparse
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
from tqdm import tqdm

os.environ['PXR_PLUGINPATH_NAME'] = str(Path(__file__).parent.resolve()) + ":" + (os.environ['PXR_PLUGINPATH_NAME'] if os.environ['PXR_PLUGINPATH_NAME'] else '')
from pxr import Usd

# 
# Object
# 
def process_metadata(directory):
    path = Path(directory/"model_info.json")
    with open(path, 'r') as file:
        metadata = json.load(file)

        new_dict = {}
        for item in metadata:
            new_dict[item['model_id']] = {
                'super-category' : item['super-category'],
                'category' : item['category'],
                'style' : item['style'],
                'theme' : item['theme'],
                'material' : item['material'],
            }
    return new_dict

# convert per path
def future_to_usd(path, new_directory, metadata):
    
    logging.basicConfig(filename='FutureToUSD.log', filemode='w', format='%(name)s - %(levelname)s - %(message)s', level=logging.INFO)
    
    if not path.is_dir():
        pass

    # new path
    new_path = new_directory/path.name
    new_path.mkdir(exist_ok=True)

    try:
        # open as usd file, assumption one file in one folder
        for file_path in path.glob('*.obj'):
            print(file_path)
            stage = Usd.Stage.Open(f"{file_path}:SDF_FORMAT_ARGS:objAssetsPath={new_path}&objPhong=true")

            # set metadata
            if metadata is not None:
                metainfo = metadata.get(path.name)
                prim = stage.GetPrimAtPath("/raw_model")

                for key, value in metainfo.items():
                    prim.SetMetadata(key, value)

            stage.Export(str(new_path/f"{file_path.stem}.usd"))
    except Exception as e:
        logging.warning(f'{path.name}: {e}')
        raise Exception('Exception: Check logfile')

    return

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

# 
# Object
# 
def convert_object(indir, outdir):

    outdir = Path(outdir, 'model')
    outdir.mkdir(exist_ok=True, parents=True)

    # run sequencely
    pathlist = list(Path(indir).glob("*"))

    # find model_json.info
    metadata = None
    for path in pathlist:
        if path.name == "model_info.json":
            metadata = process_metadata(pathlist[0].parent)

    new_directory = Path(outdir)
    for path in tqdm(pathlist):      
        future_to_usd(path, new_directory, metadata)
    return

parser = argparse.ArgumentParser()
parser.add_argument('-i', help='3D future dataset folder')
parser.add_argument('-o', help='Your USD output path')
args = parser.parse_args()

if __name__ == "__main__": 
    convert_object(args.i, args.o)