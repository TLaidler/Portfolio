"""
PPO Actor-Critic network for trading.

Architecture:
    Input(obs_dim) -> LayerNorm -> Linear(64) -> Tanh -> Dropout(0.1)
                   -> LayerNorm -> Linear(64) -> Tanh -> Dropout(0.1)
                   |-> policy_head: Linear(3) -> Categorical distribution
                   |-> value_head:  Linear(1) -> scalar state value

~5,100 parameters total. Deliberately small for ~31k-bar dataset.
"""

from typing import List, Optional, Tuple

import numpy as np
import torch
import torch.nn as nn
from torch.distributions import Categorical


class ActorCritic(nn.Module):
    """
    Shared-encoder actor-critic for PPO.

    Parameters
    ----------
    obs_dim : int
        Observation dimension (n_features + 3 position-state vars).
    n_actions : int
        Number of discrete actions (3: flat/long/short).
    hidden_dims : list of int
        Hidden layer sizes for shared encoder.
    dropout_rate : float
        Dropout probability (disabled during eval).
    use_layer_norm : bool
        Whether to apply LayerNorm before each hidden layer.
    """

    def __init__(
        self,
        obs_dim: int,
        n_actions: int = 3,
        hidden_dims: Optional[List[int]] = None,
        dropout_rate: float = 0.10,
        use_layer_norm: bool = True,
    ):
        super().__init__()
        if hidden_dims is None:
            hidden_dims = [64, 64]

        # Build shared encoder
        layers = []
        in_dim = obs_dim
        for h_dim in hidden_dims:
            if use_layer_norm:
                layers.append(nn.LayerNorm(in_dim))
            layers.append(nn.Linear(in_dim, h_dim))
            layers.append(nn.Tanh())
            layers.append(nn.Dropout(dropout_rate))
            in_dim = h_dim

        self.encoder = nn.Sequential(*layers)
        self.encoder_out_dim = hidden_dims[-1]

        # Policy head (action logits)
        self.policy_head = nn.Linear(self.encoder_out_dim, n_actions)

        # Value head (state value)
        self.value_head = nn.Linear(self.encoder_out_dim, 1)

        # Orthogonal initialization (standard PPO practice)
        self._init_weights()

    def _init_weights(self) -> None:
        """Orthogonal init: gain=sqrt(2) for hidden, gain=0.01 for policy."""
        for module in self.encoder:
            if isinstance(module, nn.Linear):
                nn.init.orthogonal_(module.weight, gain=np.sqrt(2))
                nn.init.zeros_(module.bias)

        nn.init.orthogonal_(self.policy_head.weight, gain=0.01)
        nn.init.zeros_(self.policy_head.bias)

        nn.init.orthogonal_(self.value_head.weight, gain=1.0)
        nn.init.zeros_(self.value_head.bias)

    def forward(
        self, obs: torch.Tensor
    ) -> Tuple[Categorical, torch.Tensor]:
        """
        Forward pass.

        Parameters
        ----------
        obs : torch.Tensor
            Shape (batch, obs_dim) or (obs_dim,).

        Returns
        -------
        dist : Categorical
            Action probability distribution.
        value : torch.Tensor
            State value estimate, shape (batch,) or scalar.
        """
        shared = self.encoder(obs)
        logits = self.policy_head(shared)
        dist = Categorical(logits=logits)
        value = self.value_head(shared).squeeze(-1)
        return dist, value

    def get_action_and_value(
        self,
        obs: torch.Tensor,
        action: Optional[torch.Tensor] = None,
    ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        For rollout collection (action=None) or PPO update (action provided).

        Parameters
        ----------
        obs : torch.Tensor
            Observation(s).
        action : torch.Tensor or None
            If None, sample from policy. If provided, evaluate that action.

        Returns
        -------
        action : torch.Tensor
        log_prob : torch.Tensor
        entropy : torch.Tensor
        value : torch.Tensor
        """
        dist, value = self.forward(obs)

        if action is None:
            action = dist.sample()

        log_prob = dist.log_prob(action)
        entropy = dist.entropy()

        return action, log_prob, entropy, value

    def get_greedy_action(self, obs: torch.Tensor) -> int:
        """
        Select action greedily (argmax) for deterministic evaluation.

        Parameters
        ----------
        obs : torch.Tensor
            Single observation, shape (obs_dim,).

        Returns
        -------
        action : int
        """
        with torch.no_grad():
            dist, _ = self.forward(obs)
            return int(dist.probs.argmax().item())

    def count_parameters(self) -> int:
        """Total number of trainable parameters."""
        return sum(p.numel() for p in self.parameters() if p.requires_grad)
