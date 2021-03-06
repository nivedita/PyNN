"""
A fairly generic script to produce plots that compare two or more Neo data sets.

Usage:

    python comparison_plot.py <datafile1>, <datafile2>, etc.

"""

import argparse
import os
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np
import neo
from neo.io import get_io


def variable_names(segment):
    return set(signal.name for signal in segment.analogsignalarrays)


def plot_signal(panel, signal, index, colour='b', linewidth='1', label=''):
    label = "%s (Neuron %d)" % (label, signal.channel_index[index])
    panel.plot(signal.times, signal[:, index], colour, linewidth=linewidth, label=label)
    panel.set_ylabel("%s (%s)" % (signal.name, signal.units._dimensionality.string))
    plt.setp(plt.gca().get_xticklabels(), visible=False)
    

def plot(datafiles, output_file, annotation=None):
    print datafiles
    print output_file
    blocks = [get_io(datafile).read_block() for datafile in datafiles]
    # note: Neo needs a pretty printer that is not tied to IPython
    for block in blocks:
        print (block.describe())
    # for now take only the first segment
    segments = [block.segments[0] for block in blocks]
    labels = [block.annotations['simulator'] for block in blocks]
    variables_to_plot = set.union(*(variable_names(s) for s in segments))
    print "Plotting the following variables: %s" % ", ".join(variables_to_plot)
    n_panels = sum(a.shape[1] for a in segments[0].analogsignalarrays) #+ bool(segments[0].spiketrains)
    script_name = blocks[0].annotations.get('script_name', '')
    if script_name:
        for block in blocks[1:]:
            assert block.annotations['script_name'] == script_name
    
    fig_settings = {  # pass these in a configuration file?
        'lines.linewidth': 0.5,
        'axes.linewidth': 0.5,
        'axes.labelsize': 'small',
        'legend.fontsize': 'small',
        'font.size': 8,
    }
    plt.rcParams.update(fig_settings)
    width, height = 6, 3*n_panels + 1.2
    plt.figure(1, figsize=(width, height))
    gs = gridspec.GridSpec(n_panels, 1)
    gs.update(bottom=1.2/height)  # leave space for annotations
    panels = [plt.subplot(gs[i, 0]) for i in reversed(range(n_panels))]
    n_seg = len(segments)
    for k, (segment, label) in enumerate(zip(segments, labels)):
        panel = 0
        lw = 2*(n_seg - k) - 1
        col = 'rbgmck'[k%6]
        for array in segment.analogsignalarrays:
            sorted_channels = sorted(array.channel_index)
            for channel in sorted_channels:
                i = array.channel_index.tolist().index(channel)
                print "plotting '%s' for %s in panel %d" % (array.name, label, panel)
                plot_signal(panels[panel], array, i, colour=col, linewidth=lw, label=label)
                panel += 1
    for panel in panels:
        panel.legend()
    plt.xlabel("time (%s)" % array.times.units._dimensionality.string)
    plt.setp(plt.gca().get_xticklabels(), visible=True)
    plt.title(script_name)
    
    # also consider adding metadata to PNG file - see http://stackoverflow.com/questions/10532614/can-matplotlib-add-metadata-to-saved-figures
    context = ["Generated by: %s" % __file__,
               "Working directory: %s" % os.getcwd(),
               "Timestamp: %s" % datetime.now().strftime("%Y-%m-%d %H:%M:%S%z"), 
               "Output file: %s" % output_file,
               "Input file(s): %s" % "\n                    ".join(datafiles)]
    if annotation:
        context.append(annotation)
    plt.figtext(0.01, 0.01, "\n".join(context), fontsize=6, verticalalignment='bottom')
    plt.savefig(output_file)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("datafiles", metavar="datafile", nargs="+",
                        help="a list of data files in a Neo-supported format")
    parser.add_argument("-o", "--output-file", default="output.png",
                        help="output filename")
    parser.add_argument("-a", "--annotation", help="additional annotation (optional)")
    args = parser.parse_args()
    plot(args.datafiles, output_file=args.output_file, annotation=args.annotation)

    
if __name__ == "__main__":
    main()