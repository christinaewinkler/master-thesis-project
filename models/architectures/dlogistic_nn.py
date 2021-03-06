import torch.nn as nn

from ..distributions.distributions import DiscLogistic
from models.architectures.condNF import LrNet


class DLogistic_NN(nn.Module):
    """
    NN Module to estimate parmaters of dsicretized logistic distribution.
    """

    def __init__(
        self, cond_channels, y_shape, s, L, K, bsz, nb, nbits, filter_size=512
    ):

        super(DLogistic_NN, self).__init__()

        C, H, W = y_shape
        self.H = H
        self.C = C
        self.W = W
        self.bsz = bsz
        self.nbins = 2 ** nbits

        # RRDB Net to estimate params of DLogistic
        self.rrdb1 = LrNet(
            in_c=3,
            cond_channels=cond_channels,
            s=s,
            input_shape=(C, W // s, H // s),
            nb=nb,
            gc=55,
        )

        self.pred_mean = nn.Conv2d(cond_channels, C, 3, padding=1)
        self.pred_h_sigma = nn.Conv2d(cond_channels, C, 3, padding=1)

        # for computing logpmass of Dlogistic
        self.DLogistic = DiscLogistic()

    def forward(self, y=None, x=None, log_pmass=None, sample=False):

        # estimate mu and logsigma (stability)
        h = self.rrdb1(x)

        # Constant of 0.5 added to mean such that the pred_mean is centered.
        means = self.pred_mean(h) + 0.5
        log_sigmas = self.pred_h_sigma(h)

        if not sample:
            # evaluate DLogistic(y|x,mu,sigma)
            log_pmass = self.DLogistic.log_pmass(y, means, log_sigmas, self.nbins)
        return log_pmass, means, log_sigmas

    def _sample(self, x):
        _, means, logsigmas = self.forward(x=x, sample=True)
        return self.DLogistic.sample_logistic(means, logsigmas)
