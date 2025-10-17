#' ---
#' title: Link CEDA and L2 Datasets
#' author: Joe Ornstein
#' date: 2025-06-20
#' version: 0.4
#' ---

library(tidyverse)
library(glue)

# Update these to match your Blackfish services!
data_dir <- "./data"
openai_api_key <- "sealsaretasty"
embedding_port_num <- 8080
text_gen_port_num <- 8081
embedding_dimensions <- 2048

## Load and clean raw datasets
load(paste0(data_dir, "ceda.RData"))
load(paste0(data_dir, "L2.RData"))

# Keep Alameda, Kern, and Ventura county candidates since 2016
ceda <- ceda |>
  filter(cntyname %in% c('ALAMEDA', 'KERN', 'VENTURA'),
         date > '2016-01-01')

# Create fuzzy string and blocking variables
ceda <- ceda |>
  # Convert UTF-8 encoding to ASCII for blocking.variables
  # (L2 data doesn't include characters with accents or tildes)
  mutate(
    first = iconv(first, to = 'ASCII//TRANSLIT'),
    last = iconv(last, to = 'ASCII//TRANSLIT'),
    place = iconv(place, to = 'ASCII//TRANSLIT')
  ) |>
  mutate(fullname = str_squish(glue('{first} {last}', .na = ''))) |>
  # Remove suffixes from last names for blocking
  mutate(last = str_remove_all(
    last,
    ' Jr.|, Jr.| Jr|, Jr| Sr.|, Sr.| Sr|, Sr|, III| III|, II| II|, IV| IV'
  )) |>
  # Harmonize place names
  mutate(
    place = case_when(
      place == 'Union' ~ 'Union City',
      place == 'California' ~ 'California City',
      place == 'McFarland' ~ 'Mc Farland',
      place == 'San Buenaventura' ~ 'Ventura',
      TRUE ~ place
    )
  )

l2 <- l2 |>
  mutate(
    last = Voters_LastName,
    place = case_when(
      Residence_Addresses_City == 'Calif City' ~ 'California City',
      TRUE ~ Residence_Addresses_City
    ),
    fullname = str_squish(
      glue(
        '{Voters_FirstName} {Voters_MiddleName} {Voters_LastName}',
        .na = ''
      )
    )
  ) |>
  rename(cntyname = County)


## Perform record linkage with fuzzylink
fmla <- match ~ sim + jw
learner <- 'glm'

df <- BFfuzzylink::fuzzylink(
  dfA = ceda,
  dfB = l2,
  by = 'fullname',
  blocking.variables = c('last', 'place', 'cntyname'),
  record_type = 'person',
  instructions = 'The first name comes from a list of candidates for public office in California. The second name comes from a voter registration file. Bear in mind that some candidates may run for office under a nickname or middle name, and some records may contain spelling errors.',
  fmla = fmla,
  learner = learner,
  openai_api_key = openai_api_key,
  model = "EMPTY", 
  embedding_model = "EMPTY",
  embedding_port_num = embedding_port_num,
  text_gen_port_num = text_gen_port_num,
  embedding_dimensions = embedding_dimensions
)

save(df, file = paste0(data_dir,'matches.RData'))
