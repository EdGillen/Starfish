import yaml
from Starfish import emulator
from Starfish import em_cov as em
import numpy as np
import math

f = open("scripts/emulator/Gl51.yaml")
cfg = yaml.load(f)
f.close()

pca = emulator.PCAGrid(cfg)

def plot_eigenspectra():
    import matplotlib.pyplot as plt
    for i,pcomp in enumerate(pca.pcomps):
        plt.plot(pca.wl, pcomp, label=i)
    plt.legend()
    plt.show()

def lnprob(p, weight_index):
    '''
    Calculate the lnprob using Eqn 2.29 R&W
    '''

    wi = pca.w[weight_index]


    loga, lt, ll, lz = p

    if (lt <= 0) or (ll <= 0) or (lz <= 0):
        return -np.inf

    if (lt > 3000) or (ll > 10) or (lz > 10):
        return -np.inf

    a2 = 10**(2 * loga)
    lt2 = lt**2
    ll2 = ll**2
    lz2 = lz**2

    #if loga < -1.:
    #    return -np.inf

    C = em.sigma(pca.gparams, a2, lt2, ll2, lz2)

    sign, pref = np.linalg.slogdet(C)

    central = wi.T.dot(np.linalg.solve(C, wi))

    s = 5.
    r = 5.
    prior_l = s * np.log(r) + (s - 1.) * np.log(ll) - r*ll - math.lgamma(s)

    s = 5.
    r = 5.
    prior_z = s * np.log(r) + (s - 1.) * np.log(lz) - r*lz - math.lgamma(s)

    return -0.5 * (pref + central + pca.m*np.log(2. * np.pi)) + prior_l + prior_z


def sample_lnprob(weight_index):
    import emcee

    ndim = 4
    nwalkers = 4 * ndim
    print("using {} walkers".format(nwalkers))
    p0 = np.vstack((np.random.uniform(-2, 2, size=(1, nwalkers)),
                    np.random.uniform(50, 300, size=(1, nwalkers)),
                    np.random.uniform(0.2, 1.5, size=(1, nwalkers)),
                    np.random.uniform(0.2, 1.5, size=(1, nwalkers)))).T

    sampler = emcee.EnsembleSampler(nwalkers, ndim, lnprob, args=(weight_index,), threads=cfg['threads'])

    print("Running Sampler")
    pos, prob, state = sampler.run_mcmc(p0, cfg['burn_in'])

    print("Burn-in complete")
    sampler.reset()
    sampler.run_mcmc(pos, cfg['samples'])

    samples = sampler.flatchain
    np.save(cfg['outdir'] + "samples_w{}.npy".format(weight_index), samples)

    import triangle
    fig = triangle.corner(samples)
    fig.savefig(cfg['outdir'] + "triangle_w{}.png".format(weight_index))

def main():
    #plot_eigenspectra()
    sample_lnprob(1)

if __name__=="__main__":
    main()