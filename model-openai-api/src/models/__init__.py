import os
import tarfile
import zipfile
import requests

from .clm import init_clm
from .chatglm import init_chatglm
from .phoenix import init_phoenix
from .seq2seq import init_seq2seq
from .embeddings import init_embeddings_model

def download_file(url, local_filename, force=False):
    if not force and os.path.isfile(local_filename):
        return local_filename

    # NOTE the stream=True parameter below
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(local_filename, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192): 
                # If you have chunk encoded response uncomment if
                # and set chunk_size parameter to None.
                #if chunk: 
                f.write(chunk)
    return local_filename

def download_model(model_name, url, cache_dir, force=False):
    model_dir = os.path.join(cache_dir, 'models', model_name)
    os.makedirs(model_dir, exist_ok=True)
    model_file = os.path.join(cache_dir, 'models', 
        model_name+"-"+url.split('/')[-1])

    try:
        if url.endswith('.gz'):
            fname = download_file(url, model_file, force=force)
            tar = tarfile.open(fname, "r:gz")
            tar.extractall(model_dir)
            tar.close()
        elif url.endswith('.tar'):
            fname = download_file(url, model_file, force=force)
            tar = tarfile.open(fname, "r:")
            tar.extractall(model_dir)
            tar.close()
        elif url.endswith('.zip'):
            fname = download_file(url, model_file, force=force)
            zip = zipfile.ZipFile(fname, "r")
            zip.extractall(model_dir)
            zip.close()
        else:
            return None
    except Exception as e:
        return None

    return model_dir
