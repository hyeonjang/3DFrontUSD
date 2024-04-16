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

    # check already existing
    # if Path(new_path/"raw_model.usda").exists():
        # return

    try:
        stage = Usd.Stage.Open(str(path.joinpath(f"raw_model.obj:SDF_FORMAT_ARGS:objAssetsPath={new_path}&objPhong=true")))

        metainfo = metadata.get(path.name)
        prim = stage.GetPrimAtPath("/raw_model")

        for key, value in metainfo.items():
            prim.SetMetadata(key, value)

        stage.Export(str(new_path/"raw_model.usd"))
    except Exception as e:
        logging.warning(f'{path.name}: {e}')

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
def convert_object():

    outdir = Path(DATASET_PATH, 'model')
    outdir.mkdir(exist_ok=True, parents=True)

    # run sequencely
    pathlist = list(Path("datasets/3d-future/3D-FUTURE-model").glob("*"))
    new_directory = Path(outdir)

    metadata = process_metadata(pathlist[0].parent)
    for path in tqdm(pathlist):      
        future_to_usd(path, new_directory, metadata)
    return

if __name__ == "__main__": 
    convert_object()