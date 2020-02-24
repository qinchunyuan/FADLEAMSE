# -*- coding:utf-8 -*-
"""
Search a file full of embedded spectra against a faiss index, and save the results to a file.
"""

import argparse
import os
import faiss
import sys
import numpy as np
import h5py

H5_MATRIX_NAME = 'MATRIX'

def read_faiss_index(index_filepath):
    """
    Load a FAISS index. If we're on GPU, then convert it to GPU index
    :param index_filepath:
    :return:
    """
    print("read_faiss_index start.")
    index = faiss.read_index(index_filepath)
    if faiss.get_num_gpus():
        print("read_faiss_index: Converting FAISS index from CPU to GPU.")
        index = faiss.index_cpu_to_gpu(faiss.StandardGpuResources(), 0, index)
    return index

def search_index(index, embedded, k):
    """
    Simple search. Making this a method so I always remember to square root the results
    :param index:
    :param embedded:
    :param k:
    :return:
    """
    D, I = index.search(embedded, k)
    # search() returns squared L2 norm, so square root the results
    D = D**0.5
    return D, I

def write_search_results(D, I, outpath):
    with h5py.File(outpath, 'w') as h5f:
        h5f.create_dataset('spectrum_ids', data=np.array(range(D.shape[0])), chunks=True)
        h5f.create_dataset('D', data=D, chunks=True)
        h5f.create_dataset('I', data=I, chunks=True)

def declare_gather_args():
    """
    Declare all arguments, parse them, and return the args dict.
    Does no validation beyond the implicit validation done by argparse.
    return: a dict mapping arg names to values
    """

    # declare args
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('indexfile', type=argparse.FileType('r'),
                        help='input index file')
    parser.add_argument('embedded', type=argparse.FileType('r'), nargs='+',
                        help='input embedded spectra file(s)')
    parser.add_argument('--k', type=int, help='k for kNN', default=5)
    parser.add_argument('--out', type=argparse.FileType('w'), required=True,
                        help='output file (should have extension .h5)')
    return parser.parse_args()

def loadVector(path: str) -> np.array:
    """
    load embedded vectors from input file
    :param path: the input file type is .txt or the h5 with vectors in it
    :return:
    """
    if os.path.exists(path):
        vectors = np.loadtxt(path)
        vectors = np.ascontiguousarray(vectors, dtype=np.float32)
        return vectors
    else:
        raise Exception('File "{}" does not exists'.format(path))

def read_array_file(filepath):
    """
    Read a numpy array from a .h5 or .npy file. infer extension
    :param filepath:
    :return:
    """
    extension_lower = filepath[filepath.rfind("."):].lower()
    if extension_lower == '.h5':
        h5f = None
        try:
            h5f = h5py.File(filepath, 'r')
            result = h5f[H5_MATRIX_NAME][:]
            return result
        except Exception as e:
            print("Failed to read array named {} from file {}".format(
                H5_MATRIX_NAME, filepath
            ))
            raise e
        finally:
            if h5f:
                h5f.close()
    elif extension_lower == '.npy':
        return np.load(filepath)
    else:
        raise ValueError("read_array_file: Unknown extension {} for file {}".format(
            extension_lower, filepath
        ))

def executeSearch(embedded, indexfile, resultfile):

    index = read_faiss_index(indexfile)

    embedded_arrays = []
    print(embedded)
    # for embedded_file in embedded:
    #     print(embedded_file)
    #     print("Reading embedded spectra from {}".format(embedded_file))
    # run_spectra = loadVector(embedded)
    run_spectra = read_array_file(embedded)
    embedded_arrays.append(run_spectra)
    embedded_spectra = np.vstack(embedded_arrays)
    print("Read a total of {} spectra".format(embedded_spectra.shape[0]))
    D, I = search_index(index, embedded_spectra, 1)
    print("Writing results to {}...".format(resultfile))
    write_search_results(D, I, resultfile)
    print("Wrote output file.")

def main():
    args = declare_gather_args()
    # logging
    print("loading index %s" % args.indexfile.name)
    index = read_faiss_index(args.indexfile.name)
    print("Loaded index of type %s" % type(index))
    sys.stdout.flush()

    embedded_arrays = []
    for embedded_file in args.embedded:
        print("Reading embedded spectra from {}".format(embedded_file.name))
        run_spectra = loadVector(embedded_file.name)
        embedded_arrays.append(run_spectra)

    embedded_spectra = np.vstack(embedded_arrays)
    print("Read a total of {} spectra".format(embedded_spectra.shape[0]))

    D, I = search_index(index, embedded_spectra, args.k)
    print("Writing results to {}...".format(args.out.name))
    sys.stdout.flush()
    args.out.close()
    write_search_results(D, I, args.out.name)
    print("Wrote output file.")
    args.out.close()

if __name__ == '__main__':
    all_file = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "15", "16", "17", "18", "19", "20", "21", "22", "23", "24"]
    # indexfile = './data/library/1216_nist_20140529_all_splib.index' #1202-080802_all_splib_embed.index
    indexfile = './0108_nist_20140529_all_speclib.index' #1202-080802_all_splib_embed.index
    for i in range(len(all_file)):
        embedded = "./E2_h5/0108_CHPP_LM3_RP" + all_file[i] + "_2.h5"
        resultfile = "./E2_faiss_search_result/0112_CHPP_LM3_RP" + all_file[i] + "_2_RESULT.h5"

        # embedded = "1005-080802_CHPP_LM3_RP" + all_file[i] + "_2.txt"
        # resultfile = "1202_CHPP_LM3_RP" + all_file[i] + "_2_RESULT.h5"
        executeSearch(embedded, indexfile, resultfile)
    # index = read_faiss_index(indexfile)
    # for i in index:
    #     print(i)
    # # print(index.ntotal)
    # # print(index.nprobe)
