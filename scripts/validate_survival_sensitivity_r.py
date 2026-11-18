"""Optional independent R survival check using fully synthetic admissions only.

R is a validation tool, not a dependency of the production Python supplements.
The CSV sent over local process stdin is generated here; no clinical loader is
called. Save only aggregate reference coefficients, covariance and fixed-grid CIF.
"""
from pathlib import Path
import argparse
import io
import json
import subprocess

import numpy as np
import pandas as pd

from survival_sensitivity import BASE, CORE, GRID, aalen_johansen, fit_clustered_cox, synthetic_data

R_CHECK = r'''
suppressPackageStartupMessages(library(survival))
d <- read.csv(file("stdin"))
d$gender_M <- as.numeric(d$gender == "M")
d$event_type <- factor(ifelse(d$death_event == 1, 1, 2), levels=c(0,1,2))
out <- data.frame(block=character(), row=character(), column=character(), value=double())
add <- function(block, row, column, value) {
  out <<- rbind(out, data.frame(block=block, row=as.character(row), column=as.character(column), value=as.numeric(value)))
}
for (model_name in c("primary_refined", "core")) {
  covariates <- c("raas_pre_icu", "age", "gender_M")
  if (model_name == "core") covariates <- c(covariates, "sofa_score", "chf", "ckd", "diabetes")
  f <- as.formula(paste("Surv(time_to_event_days, death_event) ~", paste(covariates, collapse=" + "), "+ strata(anchor_year_group) + cluster(subject_id)"))
  fit <- coxph(f, data=d, ties="efron", control=coxph.control(eps=1e-10, iter.max=200, timefix=FALSE))
  for (i in seq_along(covariates)) {
    add(paste0(model_name, "/beta"), covariates[i], "value", coef(fit)[i])
    for (j in seq_along(covariates)) {
      add(paste0(model_name, "/ordinary"), covariates[i], covariates[j], fit$naive.var[i,j])
      add(paste0(model_name, "/cluster"), covariates[i], covariates[j], vcov(fit)[i,j])
    }
  }
}
for (group in 0:1) {
  sf <- survfit(Surv(time_to_event_days, event_type) ~ 1, data=d[d$raas_pre_icu == group,], timefix=FALSE)
  s <- summary(sf, times=0:28, extend=TRUE)
  for (i in seq_along(s$time)) {
    for (cause in c("1", "2")) add(paste0("AJ/", group), s$time[i], cause, s$pstate[i,match(cause, sf$states)])
  }
}
cat(paste0("R=", getRversion(), ";survival=", packageVersion("survival"), "\n"))
write.table(out, stdout(), row.names=FALSE, sep=",", quote=TRUE)
'''


def verify(output):
    cases = []
    for tied in [False, True]:
        frame = synthetic_data(tied)
        completed = subprocess.run(["Rscript", "--vanilla", "-e", R_CHECK],
                                   input=frame.to_csv(index=False), text=True, capture_output=True, check=True)
        version, csv = completed.stdout.split("\n", 1)
        require_no_warning = not completed.stderr.strip()
        if not require_no_warning:
            raise RuntimeError("Independent synthetic R check emitted warnings")
        table = pd.read_csv(io.StringIO(csv), dtype={"row": str, "column": str})
        maximum = 0.0
        for name, covariates in [("primary_refined", BASE), ("core", CORE)]:
            actual = fit_clustered_cox(frame, covariates)
            for _, row in table.loc[table.block.str.startswith(name + "/")].iterrows():
                kind = row.block.split("/")[1]
                if kind == "beta":
                    value = actual["estimates"][row["row"]]["log_coefficient"]
                else:
                    matrix = actual["ordinary_covariance" if kind == "ordinary" else "patient_cluster_covariance"]
                    value = matrix[covariates.index(row["row"])][covariates.index(row["column"])]
                maximum = max(maximum, abs(value - row.value))
        for group in [0, 1]:
            subset = frame.loc[frame.raas_pre_icu.eq(group)]
            event = np.where(subset.death_event == 1, 1, 2)
            cif = aalen_johansen(subset.time_to_event_days, event, GRID)
            for _, row in table.loc[table.block.eq(f"AJ/{group}")].iterrows():
                maximum = max(maximum, abs(cif[int(row["row"]), int(row["column"]) - 1] - row.value))
        if maximum > 1e-6:
            raise RuntimeError("Independent synthetic R comparison failed")
        cases.append({"tied_times": tied, "software": version, "maximum_absolute_difference": maximum,
                      "passed": True, "R_reference_values": table.to_dict(orient="records")})
    output.write_text(json.dumps({"data_origin": "fully_synthetic_not_MIMIC", "status": "passed",
                                 "absolute_tolerance": 1e-6, "covers": ["Efron coefficients", "ordinary covariance", "patient-cluster covariance", "tied two-cause Aalen-Johansen CIF"],
                                 "clinical_analysis_validated": False, "cases": cases}, indent=2) + "\n")
    print(json.dumps({"status": "passed", "synthetic_cases": 2, "maximum_absolute_difference": max(c["maximum_absolute_difference"] for c in cases)}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    verify(args.output)
