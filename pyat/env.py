import numpy as np
from copy import deepcopy
from matplotlib import pyplot as plt
from scipy.interpolate import interp1d


'''
Objects for interfacing with Michael Porter's models. 
Designed in analog with the types of objects called by read_shd, write_fieldflp, write_env, etc.
'''


class Source:
    def __init__(self, depth):
        self.depth = depth
        self.x = None
        self.y = None

class Dom:
    def __init__(self, ran, depth, offsets=None):
        self.range = ran # in km
        self.depth = depth
        if offsets is not None:
            self.offsets = offsets

class Pos:
    def __init__(self, Source, Dom):
        self.s = Source
        self.r = Dom

class Ice:
    def __init__(self, BumDen, eta, xi):
        self.BumDen=  BumDen
        self.eta = eta
        self.xi = xi

class SSPraw:
    def __init__(self,z, alphaR, betaR, rho, alphaI, betaI):
        self.z = z
        self.alphaR = alphaR # sound speed in array
        self.betaR = betaR # not sure
        self.rho = rho 
        self.alphaI = alphaI # atten. in array (alpha (z))
        self.betaI = betaI     

    def make_sspf(self):
        self.sspf = interp1d(self.z, self.alphaR)

class SSP:
    def __init__(self, raw, depth, NMedia, Opt=None, N=None, sigma=None):
        self.NMedia	= NMedia # number of media layers
        self.Opt = Opt # option: not sure what this is for
        self.N			=	N	 # array with num points in each layer
        self.sigma		=	sigma	 # not sure
        self.depth		=	depth # depth array for layers
        self.raw = raw # list of raw ssp profile
        self.sspf = None

    def make_sspf(self):
        for raw in self.raw:
            raw.make_sspf()
        if self.NMedia > 1:
            self.ssp_vals = np.zeros((len(self.depth), 1))
            if self.NMedia == 2:
                layer_depth = self.raw[0].z[-1]
                self.sspf = lambda z: np.piecewise(z, [z<layer_depth, z>=layer_depth], [lambda z: self.raw[0].sspf(z), lambda z: self.raw[1].sspf(z)])
            elif self.NMedia == 3:
                layer_depth_one = self.raw[0].z[-1]
                layer_depth_two = self.raw[1].z[-1]
                func1 = lambda z: np.piecewise(z, [z<layer_depth_one, z>= layer_depth_one], [lambda z: self.raw[0].sspf(z), lambda z: self.raw[1].sspf(z)])
                self.sspf = lambda z: np.piecewise(z, [z<layer_depth_two, z>= layer_depth_two], [lambda z: func1(z), lambda z: self.raw[2].sspf(z)])
            else:
                raise ValueError("too many layers")
        else:
            self.ssp_vals = self.raw[0].alphaR
            self.sspf = self.raw[0].sspf

class HS:
    def __init__(self, alphaR=np.array([]), betaR=np.array([]), rho=np.array([]), alphaI=np.array([]), betaI=np.array([])):
        self.alphaR = np.array(alphaR)
        self.betaR = np.array(betaR)
        self.rho = np.array(rho)
        self.alphaI = np.array(alphaI)
        self.betaI = np.array(betaI)
        


class BotBndry:
    def __init__(self, Opt, Hs, depth=[], betaI=[0], ):
        self.Opt = Opt # 'A' for analytic or 'CVW' for interpolated ssp
        self.hs = Hs

class TopBndry:
    def __init__(self, Opt, depth=[]):
        self.Opt = Opt
        self.cp = None
        self.cs = None
        self.rho = None 

class Bndry:
    def __init__(self, top, bot):
        self.Top = top
        self.Bot = bot

class Box:
    def __init__(self, r, z):
        self.r = r
        self.z = z

class Beam:
    def __init__(self, RunType=None, Type=None,Nbeams=None, Ibeam=None, Nrays=None, alpha=None, deltas=None, box=None, epmult=None, rloop=None, Ibwin=None, Nimage = None):
        self.RunType = RunType
        self.Type = Type
        self.Nbeams =  Nbeams
        self.Ibeam  =  Ibeam 
        self.Nrays  =  Nrays
        self.alpha  =  alpha
        self.deltas =  deltas
        self.box    =  box
        self.epmult =  epmult
        self.rloop  =  rloop
        self.Ibwin = Ibwin
        self.Nimage = None

class cInt:
    def __init__(self, low, high):
        self.Low = low
        self.High = high

class Env:
    def __init__(self, SSP, bndy,dens_array=None):
        self.SSP_array = SSP_array
        self.SSP_depths = SSP.depth
        self.SSP_vals = SSP_array[:,1]
        self.sspf = interp1d(self.SSP_depths, self.SSP)
        self.dens_array = dens_array
        if self.dens_array != None:
            self.rho_depths = self.dens_array[:,0]
            self.rho_vals = self.dens_array[:,1]
            self.rho_f = interp1d(self.rho_depths, self.rho_vals)

class Field:
    def __init__(self, **kwargs):
        self.pos = kwargs['pos']
        self.greens = kwargs['pressure']
        self.freq = kwargs['freq'] # a list of frequencies

    def contour(self):
        shape = np.shape(self.greens)
        if len(shape) > 2:
            raise ValueError("Field object is too high dimensional, try multi_contour")
        pos = self.pos 
        ax = plt.contourf(pos.r.range, -pos.r.depth, np.log10(abs(self.greens.real)))
        return ax

    def multi_contour(self):
        print('not implemented, maybe one day...')

class Modes:
    def __init__(self, **kwargs):
        self.M = kwargs['M']
        self.k = kwargs['modes_k']
        self.z = np.array(kwargs['z'])
        self.phi = kwargs['modes_phi']
        self.top = kwargs['top']
        self.bot = kwargs['bot']
        self.N = kwargs['N'] 
        self.Nfreq = kwargs['Nfreq']
        self.Nmedia = kwargs['Nmedia']
        self.depth = kwargs['depth']
        self.rho = kwargs['rho']
        self.freqvec = kwargs['freqVec']
        self.init_dict = kwargs
        self.num_modes = self.M # easier to remember

    def get_excited_modes(self, sd, threshold):
        '''
        return an array of modes that are excited by a source at sd meters depth
        threshold 
        
        also populate some structures in moded caled excited_phi and excited_k

        '''
        if sd not in self.z:
            raise ValueError("sd not in the depth array, are you sure it's the right depth you're passing?")
        depth_ind = [i for i in range(len(self.z)) if self.z[i] == sd][0]
        vals = self.phi[depth_ind,:]
        const = np.max(abs(vals)) 
        filtered_inds = [i for i in range(len(self.k)) if abs(self.phi[depth_ind, i]) / const > threshold]
        self.excited_phi = self.phi[:, filtered_inds]
        self.excited_k = self.k[filtered_inds]
        return self.excited_phi, self.excited_k

    def plot(self):
        figs = []
        if self.M > 5:
            for i in range(self.M):
                fig = plt.figure(i)
                plt.plot(self.phi[:,i], -self.z)
                figs.append(fig)
        return figs

    def __repr__(self):
        return 'Modes object with ' + str(self.M) + ' distinct modes'
                
        

class KernInput:
    def __init__(self, Field_r, Field_s, env):
        self.gr = Field_r.greens_mat
        self.num_rcvrs = len(self.gr)
        self.gs = np.flip(Fields.greens_mat, axis=1) # move source off axis
        self.env = env
        self.Pos = self.Field_r.Pos
        
    



         
