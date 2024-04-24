# ! /usr/bin/env python3
__author__ = "Giacomo Bergami"
__copyright__ = "Copyright 2023, Datagram-DB"
__credits__ = ["Giacomo Bergami"]
__license__ = "GPL"
__version__ = "3.0"
__maintainer__ = "Giacomo Bergami"
__email__ = "bergamigiacomo@gmail.com"
__status__ = "Production"

import json
import os
import sys
import collections
import numpy
from sklearn.model_selection import StratifiedKFold

d = dict()

print("File reading...")
line_count = 0
to_hist = list()
traces_data = list()
nsplits = 1000


def do_bins(data, binsize, samplefoldsize):
    rng1 = numpy.random.RandomState(1)
    rng2 = numpy.random.RandomState(2)
    yvals = list()
    bins = {}
    bins_size = {}
    bins_sized = {}
    min_val = min(data)  # needed to anchor the first bin
    max_val = max(data)
    i = 0
    for value in data:
        bin_num = int(round(((value - min_val) / max_val) * binsize))  # integer division to find bin
        yvals.append(bin_num)
        if bin_num not in bins:
            bins[bin_num] = list()
        bins[bin_num].append(i)
        i = i + 1
    for k, v in bins.items():
        n = len(v)
        if n not in bins_size:
            bins_size[n] = 0
            bins_sized[n] = list()
        bins_size[n] = bins_size[n] + 1
        bins_sized[n].append(k)
    bins_size = collections.OrderedDict(bins_size)
    print(bins_size)
    todel = list()
    curr = 0
    collection = list()
    selected_traces = list()
    x = 0
    while (x < binsize) and len(bins_size) > 0:
        # Sampling from the bins according to their associated frequency of items
        keys =[x for x in bins_size.keys()]
        doReplace = len(keys) < samplefoldsize
        L = list(
            rng1.choice(range(len(keys)), p=[x / len(bins) for x in bins_size.values()], replace=doReplace,
                        size=samplefoldsize - len(selected_traces)))
        todel = list()
        for idx in L:
            # if len(keys) != len(bins_size.keys()):
            #     print("ERROR")
            original_sample_bin_size = keys[idx]
            ls = bins_sized[original_sample_bin_size]
            if doReplace:
                if sum([(bins_size[x]) for x in keys]) == 0:
                    todel = keys
                    break
                while len(ls) == 0:
                    if idx + 1 < len(keys):
                        idx = idx + 1
                        original_sample_bin_size = keys[idx]
                        ls = bins_sized[original_sample_bin_size]
                    else:
                        idx = 0
                        original_sample_bin_size = keys[idx]
                        ls = bins_sized[original_sample_bin_size]
            bins_size[original_sample_bin_size] = bins_size[original_sample_bin_size] - 1
            bucket_id = bins_sized[original_sample_bin_size].pop(rng2.randint(0, len(ls)))
            if bins_size[original_sample_bin_size] == 0 or len(ls) == 0:
                todel.append(original_sample_bin_size)
            ls2 = bins[bucket_id]
            trace_id = bins[bucket_id].pop(rng2.randint(0, len(ls2)))
            selected_traces.append(trace_id)
            novel_sample_bin_size = original_sample_bin_size - 1
            if len(ls2) == 0 or novel_sample_bin_size == 0:
                del bins[bucket_id]
            else:
                if novel_sample_bin_size not in bins_size:
                    bins_size[novel_sample_bin_size] = 0
                    bins_sized[novel_sample_bin_size] = list()
                if novel_sample_bin_size in todel:
                    todel.remove(novel_sample_bin_size)
                bins_sized[novel_sample_bin_size].append(bucket_id)
                bins_size[novel_sample_bin_size] = bins_size[novel_sample_bin_size] + 1
        for d in todel:
            del bins_size[d]
            del bins_sized[d]
        if len(selected_traces) == samplefoldsize:
            collection.append(selected_traces[:])
            selected_traces.clear()
            x = x + samplefoldsize
    return collection


def serialize_tab(log, filename, pw_step, f):
    filename = filename + "_" + str(pw_step) + ".tab"
    with open(filename, "w") as writer:
       writer.write(os.linesep.join(log))
    for line in log:
        f.write(str(pw_step) + "," + str(len(line.strip().split())) + os.linesep)


filename = sys.argv[1]
with open(filename, "r") as file1:
    for line in file1:
        line = line.strip()
        trace = line.strip().split()
        traces_data.append(line)
        to_hist.append(len(trace))
        line_count = line_count + 1
    min_val = min(to_hist)
    max_val = max(to_hist)
    x = range(line_count)
    pw = 10
    maxo = 6
    iter = 0
    log = list()
    uniques = None
    curr = pw
    done = False
    f = open(filename + "_hists.csv", "w")
    for ls in do_bins(to_hist, pw ** maxo, pw):
        if (iter == 0):
            log = [traces_data[x] for x in ls]
            uniques = ls
            serialize_tab(log, filename, curr, f)
            curr = curr * pw
            iter = iter + 1
            done = True
        else:
            for x in ls:
                done = False
                uniques.append(x)
                log.append(traces_data[x])
                if len(log) == curr:
                    serialize_tab(log, filename, curr, f)
                    curr = curr * pw
                    iter = iter + 1
                    done = True
            if len(uniques) != len(set(uniques)):
                print("ERROR!!")
    if not done:
        serialize_tab(log, filename, len(log), f)
    f.close()

# print(plotille.hist(to_hist,log_scale=True,bins=20000))
# print("#lines = "+str(line_count))

