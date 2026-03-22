"""
Adaptive Stackelberg Leader using Recursive Least Squares (RLS)

Approach: Single leader for all followers (MK1–MK6).

The leader estimates the follower's reaction function u_F = theta_0 + theta_1 * u_L
online using RLS with a forgetting factor, then computes the Stackelberg-optimal
price at each step by maximising the daily profit:

    J_L = (u_L - c_L) * S_L(u_L, u_F)

where S_L = 100 - 5*u_L + 3*u_F and c_L = 1.00.
"""

import numpy as np


class AdaptiveStackelbergLeader(Leader):
    """
    Single adaptive leader using RLS with forgetting factor.

    Leader assignment:
        - MK1: AdaptiveStackelbergLeader
        - MK2: AdaptiveStackelbergLeader
        - MK3: AdaptiveStackelbergLeader
    """

    def __init__(self, name, engine):
        super().__init__(name, engine)
        # Known constants from the specification
        self.c_L = 1.0                          # leader unit cost
        # RLS state (initialised in start_simulation)
        self.theta = np.array([1.0, 0.5])       # reaction function parameters [intercept, slope]
        self.P = np.eye(2) * 100.0              # covariance matrix
        self.lam = 0.95                         # forgetting factor
        # Strategy space bounds
        self.price_lb = 1.0
        self.price_ub = 15.0                    # set adaptively in start_simulation

    # ------------------------------------------------------------------
    # Initialisation
    # ------------------------------------------------------------------
    def start_simulation(self):
        """
        Initialise the RLS estimator from the 100 days of historical data.

        Steps:
        1. Collect and clean historical observations (remove outliers).
        2. Seed theta with an OLS estimate on recent clean data.
        3. Warm the RLS by processing all clean historical data sequentially.
        4. Set an adaptive price ceiling based on the estimated slope.
        """
        u_L_hist, u_F_hist = [], []
        for day in range(1, 101):
            lp, fp = self.get_price_from_date(day)
            u_L_hist.append(lp)
            u_F_hist.append(fp)

        u_L_hist = np.array(u_L_hist, dtype=float)
        u_F_hist = np.array(u_F_hist, dtype=float)

        # --- Outlier removal using Median Absolute Deviation (MAD) ---
        median_fp = np.median(u_F_hist)
        mad = np.median(np.abs(u_F_hist - median_fp))
        # A generous threshold: 6 * MAD above/below the median
        threshold = 6.0 * (mad + 0.01)
        clean_mask = np.abs(u_F_hist - median_fp) < threshold
        u_L_clean = u_L_hist[clean_mask]
        u_F_clean = u_F_hist[clean_mask]

        if len(u_L_clean) < 5:
            # Fallback: use all data if too many were removed
            u_L_clean = u_L_hist
            u_F_clean = u_F_hist

        # --- OLS seed on the most recent 30 clean data points ---
        n_seed = min(30, len(u_L_clean))
        X = np.column_stack([np.ones(n_seed), u_L_clean[-n_seed:]])
        self.theta, _, _, _ = np.linalg.lstsq(X, u_F_clean[-n_seed:], rcond=None)

        # --- Reset P and warm up RLS through all clean historical data ---
        self.P = np.eye(2) * 10.0
        for i in range(len(u_L_clean)):
            phi = np.array([1.0, u_L_clean[i]])
            self._rls_update(phi, u_F_clean[i])

        # --- Adaptive price ceiling ---
        # Detect follower type to set the correct strategy space bound.
        # MK3/MK6-type followers have both a low reaction function slope AND
        # low follower prices.  We use both indicators for robust detection:
        #   - slope < 0.6   → weak mirroring  → likely MK3-type
        #   - median u_F < 2.0 → low follower price level → likely MK3-type
        # Either condition triggers the [1, 15] bound.
        estimated_slope = self.theta[1]
        median_fp = np.median(u_F_clean)
        if estimated_slope < 0.6 or median_fp < 2.0:
            self.price_ub = 15.0
        else:
            self.price_ub = 50.0

    # ------------------------------------------------------------------
    # RLS update
    # ------------------------------------------------------------------
    def _rls_update(self, phi, y):
        """
        One step of the Recursive Least Squares algorithm.

        Parameters
        ----------
        phi : np.ndarray, shape (2,)
            Regressor vector [1, u_L].
        y : float
            Observed follower price u_F.
        """
        e = y - phi @ self.theta                           # prediction error
        denom = self.lam + phi @ self.P @ phi              # scalar denominator
        K = (self.P @ phi) / denom                         # Kalman gain vector
        self.theta = self.theta + K * e                    # parameter update
        self.P = (self.P - np.outer(K, phi) @ self.P) / self.lam  # covariance update

        # Numerical stability: enforce symmetry of P
        self.P = 0.5 * (self.P + self.P.T)

    # ------------------------------------------------------------------
    # Stackelberg optimisation
    # ------------------------------------------------------------------
    def _compute_optimal_price(self):
        """
        Compute the Stackelberg-optimal leader price given the current
        reaction function estimate theta = [a, b].

        Substituting u_F = a + b*u_L into the profit function:
            J_L = (u_L - c_L) * (A + B*u_L)
        where A = 100 + 3a and B = 3b - 5.

        If B < 0 the profit is a downward parabola with maximum at
            u_L* = (B - A) / (2B).
        If B >= 0 the profit increases with u_L, so the optimum is at
        the upper bound of the strategy space.
        """
        a, b = self.theta
        A = 100.0 + 3.0 * a
        B = 3.0 * b - 5.0

        if B >= -1e-10:
            # Profit is non-decreasing in u_L — price at the ceiling
            return self.price_ub

        # B < 0: downward parabola with interior maximum
        u_star = (B - A) / (2.0 * B)

        # Ensure the demand is non-negative at the chosen price
        # S_L = A + B * u_star >= 0 is guaranteed when u_star is the unconstrained
        # optimum and B < 0, but we also clip to the strategy space bounds.
        return float(np.clip(u_star, self.price_lb, self.price_ub))

    # ------------------------------------------------------------------
    # Daily pricing decision
    # ------------------------------------------------------------------
    def new_price(self, date):
        """
        Return the leader's price for the given day.

        On each day after the first play day (day 101), we:
        1. Retrieve the previous day's (u_L, u_F) from the game platform.
        2. Update the RLS estimate of the reaction function.
        3. Compute and return the Stackelberg-optimal price.
        """
        if date > 101:
            prev_lp, prev_fp = self.get_price_from_date(date - 1)
            phi = np.array([1.0, prev_lp])

            # Skip the update if the observation is an extreme outlier
            # (more than 50 units from prediction) to protect the estimator.
            predicted_fp = phi @ self.theta
            if abs(prev_fp - predicted_fp) < 50.0:
                self._rls_update(phi, prev_fp)

        optimal = self._compute_optimal_price()

        # --- Exploration safeguard for early play days ---
        # The reaction function is estimated from historical data where u_L ≈ 1.8.
        # Extrapolating directly to u_L = 40+ on day 101 is unreliable and can
        # produce negative demand.  We ramp up over the first 3 play days to
        # collect observations at intermediate prices before going fully optimal.
        play_day = date - 100                      # 1 … 30
        if play_day <= 3 and optimal > 10.0:
            safe_start = 10.0                      # guaranteed positive demand
            ramp = play_day / 3.0                  # 0.33, 0.67, 1.0
            optimal = safe_start + ramp * (optimal - safe_start)

        return max(self.price_lb, min(self.price_ub, optimal))
