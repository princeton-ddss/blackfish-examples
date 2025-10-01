#' ---
#' title: Application 1: Candidate Merge
#' author: Joe Ornstein
#' date: 2025-02-27
#' version: 0.3
#' ---

cat('**Application 1: Linking Candidate Names**\n\n')

rm(list = ls())

library(tidyverse)

## Load Merged Datasets -------------------------------

# fuzzylink
model <- 'local'
fmla <- match ~ sim + jw
file_save_name <- "l2_fuzzylink_Apertus-8B-Instruct-2509"

load(file = paste0('testing/Ornstein_application1/', file_save_name,'.RData'))

# load hand-labeled pairs
load('testing/Ornstein_application1/hand_labels.RData')
load(file = paste0('testing/Ornstein_application1/recall.RData'))


## Precision and Recall ---------------------------

# fuzzylink
fuzzylink_matches <- df |> 
  select(A,B,block) |> 
  unique() |> 
  filter(!is.na(B)) |> 
  mutate(exact_match = if_else(A==B, 'Yes','No')) |> 
  left_join(hand_labels) |> 
  mutate(true_match = as.numeric(exact_match == 'Yes' | hand_label == 'Yes')) |>
  filter(!is.na(hand_label), !is.na(true_match)) #ADDED THIS TO PREVENT RESULTS = NA

# print("true_match summary:")
# print(table(fuzzylink_matches$true_match, useNA = "always"))
# print("rows where true_match is NA:")
# print(fuzzylink_matches |> filter(is.na(true_match)))
# print("hand_label summary:")
# print(table(fuzzylink_matches$hand_label, useNA = "always"))


cat('Precision (fuzzylink):', mean(fuzzylink_matches$true_match), '\n')


# recall = true_positives / (true_positives + false_negatives)
true_positives <- sum(fuzzylink_matches$true_match)
false_negatives <- sum(recall$match_in_L2)

cat('Recall (fuzzylink):', true_positives / (true_positives + false_negatives), '\n')

