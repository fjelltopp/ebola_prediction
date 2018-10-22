import scipy.stats as stats
import numpy as np



def discrete_prob(distribution, kwargs):
    return lambda x: distribution.cdf(x + 1, **kwargs) - distribution.cdf(x, **kwargs)


def force_of_infection(incidence, discrete_dist, max_length=1000, is_shifted=False):
    s = np.arange(max_length)
    w_s = discrete_dist(s)
    if not is_shifted:
        w_s[0] = 0
        w_s = w_s / np.sum(w_s)
    return np.sum(np.flip(incidence) * w_s[:incidence.shape[0]])

def force_of_infection_time(incidence, serial_dist):
    force_of_infections = []
    for i in range(2, incidence.shape[0]+1):
        fi = force_of_infection(incidence[0:i], serial_dist)
        force_of_infections.append(fi)
    force_of_infections = np.array(force_of_infections)
    return force_of_infections

        
def log_liklihood(R, incidence, serial_dist):
    
    fis = []
    for i in range(2, incidence.shape[0]+1):
        fi = force_of_infection(incidence[0:i], serial_dist)
        fis.append(fi)
    return -np.sum(np.log(stats.poisson.pmf(incidence[1:], R*np.array(fis))))


def posterior(time, window_length, incidence, force_of_infection, serial_dist, prior=(1, 5)):
    assert time > window_length
    Y = np.sum(incidence[(time - window_length - 1):time])
    sum_lambda_s = np.sum(force_of_infection[(time - window_length - 2): time - 1])
    return (prior[0] + Y, 1 / (1/prior[1] + sum_lambda_s))


def estimated_r(incidence, force_of_infection, serial_dist, prior=(1,5), start_day=8, interval=7):
    mean_r = []
    upper = []
    lower = []
    posterior_a = []
    posterior_b = []
    a, b = prior
    for i in range(start_day, len(force_of_infection)):
        a, b = posterior(i, interval, incidence, force_of_infection, serial_dist)
        posterior_a.append(a)
        posterior_b.append(b)
        mean_r.append(stats.gamma.mean(a=a, scale=b))
        l, u = stats.gamma.interval(0.90, a=a, scale=b)
        upper.append(u)
        lower.append(l)
    return (mean_r, lower, upper, posterior_a, posterior_b)


def simulate_from_end(incidence, n_steps, serial_dist, R):
    
    for i in range(n_steps):
        fi = force_of_infection(incidence, serial_dist)
        I_t = stats.poisson.rvs(mu=R(i) * fi)
        incidence = np.append(incidence, I_t)
    return incidence


def simulate_from_end_N(incidence, serial_dist, n_pred, R, N=1000):
    sims = []
    for i in range(N):
        sims.append(simulate_from_end(incidence, n_pred, serial_dist, R))
    return np.array(sims)
                    
                                            
