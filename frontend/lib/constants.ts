export const MODEL_NAMES = [
  "linear_regression",
  "random_forest",
  "gradient_boosting",
  "xgboost",
  "extra_trees",
] as const;

export type ModelName = (typeof MODEL_NAMES)[number];

export const MODEL_LABELS: Record<ModelName, string> = {
  linear_regression: "Linear Regression (OLS)",
  random_forest: "Random Forest",
  gradient_boosting: "Gradient Boosting",
  xgboost: "XGBoost",
  extra_trees: "Extra Trees",
};

export const MODEL_DESCRIPTIONS: Record<ModelName, string> = {
  linear_regression:
    "Standard Ordinary Least Squares (OLS) linear benchmark. Provides interpretable coefficients without overfitting.",
  random_forest:
    "Ensemble of randomized decision trees. Handles non-linear climate interactions and feature variances robustly.",
  gradient_boosting:
    "Sequential gradient tree boosting. Minimizes residual loss iteratively on tabular panel data.",
  xgboost:
    "Regularized extreme gradient boosting. Highly efficient and regularized against multicollinearity.",
  extra_trees:
    "Extremely randomized trees ensemble. Randomizes cut-points to achieve lower variance on small-to-medium panels.",
};

export const DISCLAIMER =
  "Estimates are not official forecasts or proof of an El Niño causal effect. The target is RBI/NSO crop GSVA at constant 2011–12 prices—not total GDP or farmer income. Climate inputs use one representative grid point per state, not state-wide averages.";

export const ONI_PRESETS = [
  { label: "La Niña", value: -1.2, desc: "Illustrative cool-phase ONI input" },
  { label: "Neutral ENSO", value: 0.0, desc: "Illustrative near-neutral ONI input" },
  { label: "Weak El Niño", value: 0.8, desc: "Illustrative weak warm-phase ONI input" },
  { label: "Moderate El Niño", value: 1.5, desc: "Illustrative moderate warm-phase ONI input" },
  { label: "Strong El Niño", value: 2.2, desc: "Illustrative strong warm-phase ONI input" },
];
