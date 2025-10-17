#' ---
#' title: Application 1: Candidate Merge
#' author: Joe Ornstein
#' date: 2025-02-27
#' version: 0.3
#' ---

cat('**Application 1: Linking Candidate Names**\n\n')

library(tidyverse)

model <- 'local'
fmla <- match ~ sim + jw
data_dir <- "./data"

# Load fuzzylink matches
load(file = paste0(data_dir, 'matches.RData'))

# Load hand-labeled pairs
load(paste0(data_dir, "hand_labels.RData"))
load(paste0(data_dir, "recall.RData"))

# Calculate Precision = true_positives / (true_positives + false_positives)
fuzzylink_matches <- df |> 
  select(A,B,block) |> 
  unique() |> 
  filter(!is.na(B)) |> 
  mutate(exact_match = if_else(A==B, 'Yes','No')) |> 
  left_join(hand_labels) |> 
  mutate(true_match = as.numeric(exact_match == 'Yes' | hand_label == 'Yes')) |>
  filter(!is.na(true_match))

cat('Precision (fuzzylink):', mean(fuzzylink_matches$true_match), '\n')

# Calculate Recall = true_positives / (true_positives + false_negatives)
true_positives <- sum(fuzzylink_matches$true_match)
shared_A <- intersect(recall$A, fuzzylink_matches$A) # get the names that are in both files (fuzzylink guessed them)
missed <- recall %>% filter(!(A %in% shared_A)) # remove the rows from recall which fuzzylink guessed
false_negatives <-sum(missed$match_in_L2)

cat('Recall (fuzzylink):', true_positives / (true_positives + false_negatives), '\n')