from pyimzml.ImzMLParser import ImzMLParser, getionimage
import matplotlib.pyplot as plt
import numpy as np
import os
import scipy
from skimage import transform as tf
from skimage.color import rgb2gray
from matplotlib.widgets import Button

def getionimages(filename, mzs , tol = 1, outdir = 'EIT'):
    """Extract from an ImzML file a series of
    extracted ion images and save them as txt files
    in a specific folder

    Keyword arguments:
    filename -- the name of the ImzML file
    mzs -- a string with the target ions sebarated by commas
    tol -- the m/z tolerance for extracting the trace (default = 1)
    outdir -- the directory where the EIT are stored (default = 'EIT')
    """
    p = ImzMLParser(filename)
    ## Extracct the ion images

    mz = [float(x.strip()) for x in mzs.split(',')]
    EITs  = [getionimage(p, x, tol) for x in mz]

    ## create the foder to save the EITs
    if not os.path.exists(outdir):
        os.makedirs(outdir)

    ## save the files
    for i in range(0,len(EITs)):
        finalpath = os.path.join(outdir,'mz_' + str(mz[i]) + '.csv')
        print finalpath
        np.savetxt(finalpath, EITs[i], delimiter=",")


## Alignment with the optical image -------------------------------------------

def hook(optical,EIT):
    '''Identify (and save) a series of reference points
    between an optical image and a specific MS image. The coordinates
    of the points are saved into a txt (hooks.tis) file

    Keyword arguments:
    optical  --  the name of the image file with the optical image
    EIT -- the file name of the csv containing the mz image
    '''

    ## read the two input files
    tissue = plt.imread(optical)
    mz =  np.genfromtxt(EIT, delimiter = ',')

    ## initialize the axes
    axs = []

    ## construct the figure with two subplots
    ## and the buttons
    fig = plt.figure()
    axs.append(fig.add_subplot(121))
    axs.append(fig.add_subplot(122))
    ## put there the two butons
    axcancel = plt.axes([0.7, 0.05, 0.1, 0.075])
    axsave = plt.axes([0.81, 0.05, 0.1, 0.075])


    ## actually display the two images
    axs[0].imshow(tissue, interpolation = "None")
    axs[0].set_title("Optical Image")
    axs[1].imshow(mz, interpolation = "None")
    axs[0].set_title("m/z trace")
    ## this stores the dimensions of the two arrays, it will be needed to
    ## be sure that the clicking is performed only inside the files
    dims = [tissue.shape[0:2], mz.shape]

    ## some 'global' variables
    coords = []         ## the matched pixels
    active_subplot = 0  ## where my mouse is working now
    bbs = [ax.get_position() for ax in axs]  ## the position of the plots in the
    ## global coordinate system, here we have four places: 2 for the plot, 2 for
    ## the buttons

    ## Now thw function handling the actions --------------------------------#

    ## onclick
    def onclick(event):
        ## this means that active_subplot is a global variable
        ## which can be modified inside the method
        global active_subplot

        ## if: I click out, some of the button on top is active,
        ## I'm clicking on the two buttons or I do not use the left
        ## button, please do nothing
        if (event.inaxes is None) or (fig.canvas.toolbar.mode != '') or \
            (event.inaxes == axcancel.axes) or (event.inaxes == axsave.axes) or \
            (event.button != 1):
            return


        x, y = int(round(event.xdata)), int(round(event.ydata))
        if (x < 0) or (y < 0):
            return

        ## relates the coordinates of the mause with the one shown
        ## in the two subplots
        fx, fy = fig.transFigure.inverted().transform((event.x,event.y))
        subplot = [bb.contains(fx, fy) for bb in bbs].index(True)

        ## further checks
        if subplot != active_subplot:
            return

        if (x>=dims[subplot][0]) and (y>=dims[subplot][1]):
            return

        ## draw the markers on the plots
        xlim, ylim = axs[subplot].get_xlim(), axs[subplot].get_ylim()
        axs[subplot].plot(x, y, 'g+', markersize=20, markeredgewidth=5, c = 'Lime')
        axs[subplot].set_xlim(xlim); axs[subplot].set_ylim(ylim)
        fig.canvas.draw()

        ## If I'm in the first plot I create a new entri in the matching list
        if active_subplot == 0:
            coords.append([])

        coords[-1].append((x, y))

        active_subplot +=1
        if active_subplot >= len(axs):
            active_subplot = 0

        print(coords)

    def cancel(event):
        if event.button != 1:
            return

        for ax in axs:
            for i in range(len(ax.lines)):
                ax.lines.pop(0)
                fig.canvas.draw()
        del coords[:]


    def save(event):
        if active_subplot != 0:
            print "ERROR: missing point in subplot {:d}".format(active_subplot+1)

        ## reshape the output to mak eit nice
        np.savetxt('hooks.tis', np.reshape(coords, newshape = (np.shape(coords)[0],4)), delimiter=",")


    ## Actually create the two buttons
    bcancel = Button(axcancel, 'Cancel')
    bcancel.on_clicked(cancel)

    bsave = Button(axsave, 'Save')
    bsave.on_clicked(save)

    fig.canvas.mpl_connect('button_press_event', onclick)

    plt.show()

## Batch warping of the ion images according to a series of hook points

def transform(hooks,opticalimage,EITimage = '',EITfolder = '',outdir = 'EITwarp'):
    '''
    Estimate and perform the affine transformation of one (or more) EIT images
    on the bases of a set of hook points. EIT images are resampled to match
    the size of the optical image
    '''
    tissue = plt.imread(optical)
    hookpt =  np.genfromtxt(hooks, delimiter = ',')
    src = hookpt[:,0:2]
    dst = hookpt[:,2:4]

    tform3 = tf.AffineTransform()
    tform3.estimate(src,dst)

    if not os.path.exists(outdir):
        os.makedirs(outdir)

    if EITfolder == '':
        mzimage = np.genfromtxt(EITimage, delimiter = ',')
        warped = tf.warp(mzimage, tform3, output_shape=tissue.shape[0:2])
        ## save the file
        finalpath = os.path.join(outdir,'wpd' + os.path.basename(EITimage))
        np.savetxt(finalpath, warped, delimiter=",")
        return

    for file in os.listdir(EITfolder):
        if file.endswith(".csv"):
            mzimage = np.genfromtxt(file, delimiter = ',')
            warped = tf.warp(mzimage, tform3, output_shape=tissue.shape[0:2])
            finalpath = os.path.join(outdir,'wpd' + file)
            np.savetxt(finalpath, warped, delimiter=",")


    ## if te input is a folder process all the images present inside
