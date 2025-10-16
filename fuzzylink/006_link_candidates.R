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

file_save_name <- "l2_fuzzylink_Mixtral-8x7B-Instruct-v0_1"
rdata_pathway <- "/Users/nv5842/github/fuzzylink/testing/Ornstein_application1/"

load(file = paste0(rdata_pathway, file_save_name,'.RData'))

# load hand-labeled pairs
load(paste0(rdata_pathway, "hand_labels.RData"))
load(paste0(rdata_pathway, "recall.RData"))


## Precision and Recall ---------------------------

# fuzzylink
fuzzylink_matches <- df |> 
  select(A,B,block) |> 
  unique() |> 
  filter(!is.na(B)) |> 
  mutate(exact_match = if_else(A==B, 'Yes','No')) |> 
  left_join(hand_labels) |> 
  mutate(true_match = as.numeric(exact_match == 'Yes' | hand_label == 'Yes')) |>
  filter(!is.na(true_match))

#print("true_match summary:")
#print(table(fuzzylink_matches$true_match, useNA = "always"))
# print("rows where true_match is NA:")
# print(fuzzylink_matches |> filter(is.na(true_match)))
#print("hand_label summary:")
#print(table(fuzzylink_matches$hand_label, useNA = "always"))


cat('Precision (fuzzylink):', mean(fuzzylink_matches$true_match), '\n')


# recall = true_positives / (true_positives + false_negatives)
true_positives <- sum(fuzzylink_matches$true_match)
# false_negatives <- sum(recall$match_in_L2)
shared_A <- intersect(recall$A, fuzzylink_matches$A) #get the names that are in both files (fuzzylink guessed them)
missed <- recall %>% filter(!(A %in% shared_A)) #remove the rows from recall which fuzzylink guessed
false_negatives <-sum(missed$match_in_L2)

#print("recall before culling:")
#print(table(recall$match_in_L2, useNA = "always"))
#print("recall after culling:")
#print(table(missed$match_in_L2, useNA = "always"))

cat('Recall (fuzzylink):', true_positives / (true_positives + false_negatives), '\n')

#save(fuzzylink_matches,
#     file = paste0('fuzzylink/testing/Ornstein_application1/RESULTS.RData'))
