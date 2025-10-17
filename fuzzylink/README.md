# Record Linkage
Let’s say you have two records: one is an L2 voter file with ~22 million registered voters from California and the second is the California Election Data Archive (CEDA), containing the names of over 9,000 candidates from public office. Now, because of the different information contained in each file, you may have a research question that would require information from both datasets. However, to merge the two files, you need to have a procedure to identify if person A in the L2 file is the same as person B from the CEDA file. Unfortunately, in the two files, spelling errors, nicknames, middle names, etc. might prevent there being a single shared variable (i.e. "full name") that unambiguously identifies that the two records refer to the same person. Because of this, researchers must rely on _fuzzy record linkage_, which links records based on a certain degree of similarity as opposed to exact matches. 

<!--
If an image showcasing what record linkage is would be helpful, I like the one available here: https://dbs.uni-leipzig.de/research/projects/pprl 
-->


## What is Fuzzylink?

In his paper “Probabilistic Record Linkage Using Pretrained Text Embeddings,” Joseph Ornstein developed a probabilistic record linkage procedure (dubbed “fuzzylink”) that relies on large language models (LLMs) to determine if two records, `A` and `B`, refer to the same entity [^1]. His use of LLMs allow records to be linked based on _semantic_ similarity as opposed to simply lexical similarity. His procedure can be summarized in these six steps:
1. Use a model to retrieve text embeddings for the string representations of `A` and `B`.
2. Compute the cosine similarity between each pair of embedding vectors in the set `A x B`, using blocking, if possible, to improve efficiency.
3. Label a training set using a LLM to identify "true" matches for a subset of the record pairs.
4. Using the labeled data, fit a model to predict the likelihood of a match given cosine similarity.
5. Using the fitted model, estimate match probabilities for all record pairs in `A x B`. Select `N` record pairs using uncertainty sampling and label them as in Step 3; add these to the training set and repeat Step 4 and 5 until the estimated likelihoods stabilize.
6. Return all record pairs and their match probability.

Though his procedure outperforms other, preexisting algorithms in terms of both precision and recall, his findings rely on the use of closed-source models and are therefore subject to potential cost/scaling, privacy, and replication concerns. 

If you need to merge two records using Ornstein's probabilistic record linkage procedure and want to do it easily, transparently, and for free, you can use Blackfish to run open-source models on a HPC cluster. You will know exactly what models you are using, and your results can be reproduced by anyone with access to the same model. The following tutorial will walk through all the steps you need to take to use Ornstein’s fuzzylink approach on your HPC cluster. 

# Running the Example

## Setting Up
This tutorial is going to walk through using `fuzzylink` to merge the L2 voter file and CEDA file described above using Blackfish (this is Application 1 from Ornstein's paper). Some notes before we begin:
- This example assumes you are working in an environment where Blackfish is installed and setup to work with an HPC cluster. For instructions on how to do this, visit [the Blackfish documentation](https://princeton-ddss.github.io/blackfish/latest/getting_started/).
- The original data we will be using is available for download [here](https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/7U5KEJ). The files you will need are `ceda.RData` and `L2.RData` for matching the records, and `hand_labels.RData` and `recall.RData` for evaluating performance. 

<!--
You will also need to obtain the `fuzzylink` code. Ornstein created an R package that can be installed from CRAN, but that package only works with closed-source models. This example demonstrates how to use `fuzzylink` with *open-source* models using Blackfish and `text-generation` services. To use the updated version of fuzzylink [clone this repository](https://github.com/princeton-ddss/fuzzylink-for-blackfish) by typing the following in your terminal:
```shell
git clone git@github.com:princeton-ddss/fuzzylink-for-blackfish.git
```
This will create a directory called `fuzzylink-for-blackfish` which will house the code to run the fuzzy record linkage.
-->

Finally, to obtain the files to preprocess the data and call the fuzzylink code, either clone this directory by typing
```shell
git clone git@github.com:princeton-ddss/blackfish-examples.git
```
in your terminal, or directly download the `001_link-candidates.R` and `006_link-candidates.R` files, as these are the only ones you'll be needing. 

## Running the Blackfish Services
Now that you have your data files, the code, and Blackfish set up, you're ready to start. 

If you installed Blackfish in a virtual environment, activate that virtual environment. Before we start any service, let's start the Blackfish API by typing
```shell
blackfish start
```
in the command line. If everything worked, you should see a message stating the application startup is complete. Leave this running and open a new terminal tab/window (again activating your vitual environment if using one).

For this application, you will need two services: one service to generate embeddings (from step 1 in the fuzzylink procedure) and another to assess if the records refer to the same person (from step 3). If you have used Blackfish before and already have some models installed, you might be able to use your preexisting models, which can be seen by running
```shell
blackfish model ls
```
However, for the sake of this tutorial, we will assume you have no existing models. Let's start the embedding service first. We are going to use the `TinyLlama/TinyLlama-1.1B-Chat-v1.0` from Hugging Face, though feel free to experiment with different models. To [download this model](https://princeton-ddss.github.io/blackfish/latest/#step-4-obtain-a-model), type
```shell
blackfish model add TinyLlama/TinyLlama-1.1B-Chat-v1.0
```
Once this has finished downloading, you should be able to see it by typing
```shell
blackfish model ls --refresh
```
Now that you have that model, you can use it to start your service! This is technically a text generation model, but we can use it for text embeddings by adding the `--task embed` argument to our command [^2]. To start this service, type
```shell
blackfish run --gres 1 --mem 8 --ntasks-per-node 4 --time 01:00:00 --constraint 'amd&gpu40' text-generation TinyLlama/TinyLlama-1.1B-Chat-v1.0 --api-key sealsaretasty --task embed --name embedding-model
```
into the terminal. You can feel to change/remove the `api-key` as you desire and update the `time` to best suit your needs. If all goes well, you should get a message that the service was successfully started. You can monitor your services by typing
```shell
blackfish ls
```
The service status should change from "PENDING" to “STARTING” shortly but will take a few minutes to change to “HEALTHY.” While waiting, let's start working on the second service [^3]. For this tutorial, we are going to use the `meta-llama/Llama-3.3-70B-Instruct` model. If you don't have it already, download it by typing
```shell
blackfish model add meta-llama/Llama-3.3-70B-Instruct
```
You can again confirm that it was added by typing
```shell
blackfish model ls --refresh
```
To start this service, enter the following command
```shell
blackfish run --grace-period 600 --gres 4 --mem 16 --ntasks-per-node 4 --time 01:00:00  --constraint gpu80 text-generation meta-llama/Llama-3.3-70B-Instruct --api-key sealsaretasty
```
If you chose to update/remove the `api-key`, it is important to note that it must match the one you chose for the embedding service. If you encounter an `huggingface_hub.errors.GatedRepoError: 401 Client Error`, you may need to explicitly specify the model revision in your command. You can see the revision by typing
```shell
blackfish ls
```
and can simply add the model's revision to the end of your command (ie. `... --api-key sealsaretasty --revision 6f6073b423013f6a7d4d9f39144961bfbfbc386b`). You will need to wait until both models' status is "HEALTHY" before you can use the services, which might take 5-10 minutes depending on your model of choice. Once both services are "STARTING," though, you can get their port numbers. Again, type 
```shell
blackfish ls
```
and take note of the port number for the embedding service and the regular text generation service. For the rest of this tutorial, we'll assume the embedding service is running on port 8080 and the text generation service is running on 8081. While those services finish starting, we can hop to the next step.


## Running Fuzzylink
To install the `fuzzylink-for-blackfish` package containing the modified `fuzzylink` code, you can use devtools or pak. To use devtools, type the following in your R session:
```shell
install.packages("devtools")
devtools::install_github("princeton-ddss/fuzzylink-for-blackfish")
```
To use pak:
```shell
install.packages("pak")
pak::pkg_install("princeton-ddss/fuzzylink-for-blackfish")
```
After you've installed the `fuzzylink-for-blackfish` package, you'll be able to make calls to `BFfuzzylink::fuzzylink` directly. First, we'll run an R script to match the candidate records to L2, `001_link-candidates.R`. Before running the script, modify the following constants to match your Blackfish deployments:
```R
data_dir <- "./data"
openai_api_key <- "sealsaretasty"
embedding_port_num <- 8080
text_gen_port_num <- 8081
embedding_dimensions <- 2048
```
 
(If you aren't using an API key, you can set this to `null`[^4]). The output of this script (`matches.RData`) contains all the CEDA records for which `fuzzylink` found a match in the L2 file. Note that the call to `BFfuzzylink::fuzzylink` sets both `model` and `embedding_model` to `"EMPTY"`. This is used to indicate to the API that we are running models locally. Wait until the status of both your services is "HEALTHY," then start the script. 

## How well did your models preform?

In his paper, Ornsetin used OpenAI to obtain embeddings and match labels, In his discussion he claims that "Because these models are closed-source and operated by for-profit entities... the results that fuzzylink produces—including those presented in this article—are not fully reproducible." He also claims that, while open-source models would solve this problem, the accuracy provided by OpenAI's state-of-the-art closed source models is worth the cost and inability to reproduce his results. <!-- That sounds like a challenge! (This seems like good motivation for the example–maybe this should be stated in the introduction?) --> 


`006_link-candidates.R` is a modified version of Ornstein's R code to analyze the performance of `fuzzylink` on the candidate matching exercise. You can analyze your model's performance by first updating the `data_dir` and then running the script. The script calculates two performance metrics: precision and recall. Precision (also known as "specificity") is the probability that a predicted match is *actually* a match; recall (also known as "sensitivity") is the probability that an actual match is predicted to be a match. We want both of these metrics to be as close to `1.0` as possible. Ornstein’s estimated precision and recall are both 95.8%. Below, we report our results for various text generation models that we've tested (`TinyLlama/TinyLlama-1.1B-Chat-v1.0` is used for embeddings in all cases).

| Text Generation Model                | Precision | Recall    |
| ------------------------------------ | --------- | --------- |
| meta-llama/Llama-3.1-70B-Instruct.   | 0.9938272 | 0.9378641 |
| meta-llama/Llama-3.3-70B-Instruct    | 0.99591   | 0.938343  |
| Google/gemma-3-27b-it | 0.9898374    | 0.938343  |           |
| swiss-ai/Apertus-8B-Instruct-2509    | 0.9952038 | 0.9284116 |
| Mistralai/Mixtral-8x7B-Instruct-v0.1 | 1.000000  | 0.895082  |

 The results demonstrate that the open-source models identify fewer matches than the closed-source ones[^5], but match candidates with higher precision. Overall, the performance of the open-source models is comparable to the closed-source ones used by Ornstein and worth it to get free, reproducible results!

## Some Extra Details
Not all models support passing the `--task embed` argument to the `vLLM` service. Below is a list of models that work based on our testing as well as the dimensionality of the embedding vector.

| Model                                      | Dimension |
| ------------------------------------------ | --------: |
| deepseek-ai/DeepSeek-R1-Distill-Llama-70B  | 8192      |
| deepseek-ai/DeepSeek-R1-Distill-Qwen-32B   | 5120      |
| deepseek-ai/DeepSeek-V2-Lite               | 2048      |
| deepseek-ai/DeepSeek-V2-Lite-Chat          | 2048      |
| google/gemma-3-1b-it                       | 1152      |
| meta-llama/Llama-3.1-70B-Instruct          | 8192      |
| meta-llama/Llama-3.1-8B-Instruct           | 4096      |
| meta-llama/Llama-3.2-1B-Instruct           | 2048      |
| meta-llama/Llama-3.2-3B-Instruct           | 3072      |
| meta-llama/Llama-3.3-70B-Instruct          | 8192      |
| meta-llama/Meta-Llama-3-70B-Instruct       | 8192      |
| meta-llama/Meta-Llama-3-8B-Instruct        | 4096      |
| mistralai/Mistral-7B-Instruct-v0.3         | 4096      |
| mistralai/Mixtral-8x7B-Instruct-v0.1       | 4096      | 
| Qwen/Qwen2-Audio-7B-Instruct               | 4096      | 
| Qwen/Qwen2.5-32B                           | 5120      | 
| Qwen/Qwen2.5-32B-Instruct                  | 5120      | 
| Qwen/Qwen2.5-72B                           | 8192      | 
| Qwen/Qwen2.5-72B-Instruct                  | 8192      | 
| Qwen/Qwen3-14B                             | 5120      | 
| Qwen/Qwen3-32B                             | 5120      | 
| Qwen/Qwen3-8B                              | 4096      | 
| Qwen/QwQ-32B                               | 5120      | 
| TinyLlama/TinyLlama-1.1B-Chat-v1.0         | 2048      |


[^1]: Ornstein, J. T. (2025). Probabilistic Record Linkage Using Pretrained Text Embeddings. Political Analysis, 1–12
[^2]: If you decide to use a different model, make sure that it is compatible with the `--task embed` argument. To see a select number of models that are compatible with this argument, visit [the blackfish README](https://github.com/princeton-ddss/blackfish).
[^3]: If you get the error message `Error in family$linkfun(mustart) : Argument mu must be a nonempty numeric vector` when trying to run the fuzzylink code, this is because the model did not respond with a strictly ‘Yes’ or ‘No’ response. Modifying the fuzzylink prompt might solve the issue. I’ve left the prompt as-is and stuck to more powerful models that returned properly formatted responses.
[^4]: If you leave the api key parameter empty, the `fuzzylink` code will, by default, try to get an OpenAI api key from your system's environment. If you don't have one, the local model will still be able to run if you having specified an API key for your services. However, if you did not set an `--api-key` when starting your services *and** you have an OpenAI key available in your system's environment, you will likely encounter an error and will need to define an `--api-key` to use for your local models.
[^5]: Due to the nature of the recall file provided, some false negatives may be missing in the recall calculation.







<!-- 
# Old:
In his paper “Probabilistic Record Linkage Using Pretrained Text Embeddings,” Joseph Ornstein developed a probabilistic record linkage procedure (dubbed “fuzzylink”) which relies on large language models to determine if two records refer to the same entity. Though his procedure outperformed other algorithms in both precision and recall, his use of closed-source models meant that the models were (1) not free to use and (2) could be modified at any time. When a model is modified or deprecated, any results that were obtained using Ornstein’s method on that model are not fully reproducible. 

Ornstein's fuzzylink algorithm can be broken into the following steps:
1. Use a model to retrieve text embeddings for the string variables in records _A_ and _B_.
2. Compute the cosine similarity between the embedding vectors for each pair of records in the set _A_ x _B_, blocking, if possible, to improve efficiency.
3. Using a subset of the record pairs, label a training set with 1 if the records are a true match and 0 if they are not.
4. Fit a probabilistic model to map the cosign similarities *(from the labeled subset??)* onto a match probability.
5. Using the fitted model from step 4, estimate match probabilities for all record pairs in _A_ X _B_. Select _N<sub>L</sub>_ record pairs using uncertainty sampling and label them as in Step 3; add these to the training set and repeat steps 4-5 until some criterion is met. (Ornstein stopped when none of the estimated probabilities changed by more than 0.01 between iterations.)
6. Return all record pairs and their match probability. 

*CONFIRM CORRECTNESS^^* 

If you need to merge two records using Ornstein's probabilistic record linkage procedure and want to do it easily, transparently, and for free, you can use Blackfish to run open-source models on a HPC cluster. You will know exactly what models you are using, and your results can be reproduced by anyone with access to the same model. The following tutorial will walk through all the steps you need to take to use Ornstein’s fuzzylink approach on your HPC cluster. 




## Data
The original data is available for download [here](https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/7U5KEJ). The files we use in this example are:
```shell
ceda.RData
L2.RData
hand_labels.RData #for measuring precision
recall.RData #for measuring recall
```


## Usage

### Step 1: Setting up
Let’s say you have two records: one is an L2 voter file with ~22 million registered voters from California and the second contains the names of over 9,000 candidates from public office (this is application 1 from Orstein’s paper). To merge the names of the candidates with their records from the L2 voter file, you’ll need the following:
- The two .RData files containing the records that you wish to link placed in your working directory (`ceda.RData` and `L2.RData` for this example)
- Blackfish installed and set up. For instructions on how to do this, visit [the blackfish documentation](https://princeton-ddss.github.io/blackfish/latest/getting_started/)

Next, you’re going to need the fuzzylink code. Ornstein created an R package that can be installed from CRAN, but that package only works with Mistral and OpenAI models. For this example, I’ve modified Ornstein’s package to work with the vLLM server used by Blackfish--[clone this repository](https://github.com/princeton-ddss/fuzzylink-for-blackfish) to use the updated version of fuzzylink.

### Step 2: Running the Services on Blackfish
Once you have the data files and fuzzylink code, you can start running your blackfish services. The fuzzylink method requires two services: one used to generate embeddings and a second regular text generation model. In your terminal (in your cloned blackfish directory), start the blackfish API:
*I don't think users will have a "cloned blackfish directory," but I'm not sure where they should be...the directory where they ran blackfish init??*
```shell
uv run blackfish start
```
Next, in a new terminal (again, in your blackfish directory), activate the blackfish environment by typing:
```shell
source .venv/bin/activate
```
This will allow you to run blackfish commands directly and easily. If you don't care too much about the specifics of the models you are running, you can automatically start the two default services described in this tutorial using `start_services.sh` by typing:
```shell
bash start_services.sh
```
This will prompt you for an api key (which you can leave blank if desired) and start the services for you. You can modify this file directly to automatically start your services, or you can start them manually in the command line, as described below. Additionally, if you want to use an embedding specific model, you can [download one yourself](https://princeton-ddss.github.io/blackfish/latest/#step-4-obtain-a-model). If you want to do this, I recommend the `Qwen/Qwen3-Embedding-0.6B` model which can be downloaded by running:
```shell
blackfish model add Qwen/Qwen3-Embedding-0.6B
```
To start the embedding service using one of the models already available on Blackfish, type the following command, changing the api key and/or time[^1] if desired:
```shell
blackfish run --gres 1 --mem 16 --ntasks-per-node 4 --time 00:30:00 --constraint 'amd&gpu40' text-generation TinyLlama/TinyLlama-1.1B-Chat-v1.0 --api-key sealsaretasty --task embed
```
You can check the status and port number of this service by typing:
```shell
blackfish ls
```
The service status should change from "PENDING" to “STARTING” shortly, but will take a few minutes to change to “HEALTHY.” While waiting, you can start the second service. For the text generation model, you can pick which model you want to use, though models that are not powerful enough might cause the fuzzylink code to fail if they do not respond to queries with a strictly ‘Yes’ or ‘No’ response[^2]. To see which models you have available on Blackfish type:
```shell
blackfish model ls
```
You are going to want to pick a model that is a “text-generation” model. You can also [download your own model](https://princeton-ddss.github.io/blackfish/latest/#step-4-obtain-a-model) if you want one that is not available. For this example, we will use the `meta-llama/Llama-3.3-70B-Instruct` model--to start this service, type the following in the CLI:
```shell
blackfish run --grace-period 600 --gres 4 --mem 16 --ntasks-per-node 4 --time 00:30:00  --constraint gpu80 text-generation meta-llama/Llama-3.3-70B-Instruct --api-key sealsaretasty --revision 6f6073b423013f6a7d4d9f39144961bfbfbc386b
```
Again, you can set the API key and time as desired, as long as the API key matches that of your embedding model. You will need to wait until this model’s status is "HEALTHY" before proceeding, which might take 5-10 minutes after transition to "STARTING," depending on your model of choice. While those services are starting, we can hop to the next step.


### Step 3: Running Fuzzylink
~~If you want to quickly test that your services are working properly, you can follow the following steps to update/run the `simple_test.R` file.~~


In `001_link-candidates.R`, first, change the `file_save_name` variable to equal the name you wish to use for your output file. Similarly, modify `rdata_pathway` to be the pathway to your working directory which contains your downloaded .RData files (this will also be where the fuzzylink output gets saved). You can then modify the following call to fuzzylink[^3]:
```R
df <- BFfuzzylink::fuzzylink(
 dfA = ceda,
 dfB = l2,
 by = 'fullname',
 blocking.variables = c('last', 'place', 'cntyname'),
 record_type = 'person',
 instructions = 'The first name comes from a list of candidates for public office in California. The second name comes from a voter registration file. Bear in mind that some candidates may run for office under a nickname or middle name, and some records may contain spelling errors.',
 fmla = fmla,
 learner = learner,
 openai_api_key = "sealsaretasty",
 model = "EMPTY",
 embedding_model = "EMPTY",
 embedding_port_num = 8080,
 text_gen_port_num = 8081,
 embedding_dimensions = 2048 
)
```
In this function call, setting the models to `EMPTY` indicates that you are running them locally. The `open_api_key` should match what you set as your `--api-key` when initiating the services (or can be removed/left empty if you did not set one[^4]). `Embedding_port_num` should be the port number the embedding service is running on, and `text_gen_port_num` should be the second service’s port number; both port numbers can be seen after running `blackfish ls`. Once the port numbers, api key, and file save name/pathway have been updated, you are ready to go! Wait until the status of both your services is "HEALTHY," then start an R session. Make sure your session's working directory is set to the directory containing the fuzzylink package, type `devtool::load_all()`, then simply run the 001_link-candidates file! It should take a few minutes to run and will save the results to a .RData file with the name you specified in the `file_save_name` variable. 

### How well the models perform
Below, we provide some basic metrics on performance for five potential text generation models that you can use for this process. Precision and Recall were calculated by comparing the output of fuzzylink on Ornstein's L2 and California Election Data Archive (CEDA) files with his recall and hand_labels files. Make sure you have these files downloaded if you want to measure your models' performance on this linkage process.

*It is important to note that, due to the nature of the recall file provided, some false negatives may be missing in the recall calculation.*

In `006_link-candidates.R`, update `file_save_name` to be the name of the file containing the results from running the fuzzylink code (this should match the `file_save_name` from `001_link-candidates.R`). Similarly, update `rdata_pathway` to be the full pathway to where the .RData files are being stored. Now, you can simply run this file. The precisions and recalls for various text generation models are reported below--the same embedding model was used for all. Precision is a measure of the fraction of identified matches are correct ($\\frac{true  positives}{true  positives + false  positives}$) while recall measures the fraction of matches which were identified ($\\frac{true  positives}{true  positives + false  negatives}$).

| Text Generation Model | Precision | Recall |
| ------ | ------- | ------|
| meta-llama/Llama-3.1-70B-Instruct | 0.9938272 | 0.9378641 |
| meta-llama/Llama-3.3-70B-Instruct | 0.99591 | 0.938343 |
| Google/gemma-3-27b-it | 0.9898374 | 0.938343 |
| swiss-ai/Apertus-8B-Instruct-2509 | 0.9952038 | 0.9284116 |
| Mistralai/Mixtral-8x7B-Instruct-v0.1 | 1.000000 | 0.895082 |

In his paper, Ornstein used OpenAI for getting the embeddings and the Y/N responses. In his discussion he claimed, "Because these models are closed-source and operated by for-profit entities...the results that fuzzylink produces—including those presented in this article—are not fully reproducible." He states that, while open-source models would solve this problem, the accuracy provided by OpenAI's state-of-the-art closed source models is worth the cost and inability to reproduce his results. However, the precision and recall that we report here are not too far off Ornstien's; Orsntein's estimated precision and recall were both 95.8%. While the closed-source OpenAI models might have a higher recall, our open-source models all have higher precisions; it appears that the open-source models identify less matches than the closed-source ones. Therefore, fuzzylink using these models might miss more correct matches, but will also produce fewer incorrect matches. Overall, we believe that the performance of the open-source models is comparable to the closed-source ones used by Ornstein and worth it to get free, reproducible results!




Models that support --task embed:

| Model    | Embedding Dimension |
| -------- | ------- |
| deepseek-ai/DeepSeek-R1-Distill-Llama-70B  | 8192    |
| deepseek-ai/DeepSeek-R1-Distill-Qwen-32B  | 5120    |
| deepseek-ai/DeepSeek-V2-Lite | 2048 |
| deepseek-ai/DeepSeek-V2-Lite-Chat | 2048 |
| google/gemma-3-1b-it | 1152 |
| meta-llama/Llama-3.1-70B-Instruct | 8192 |
| meta-llama/Llama-3.1-8B-Instruct | 4096 |
| meta-llama/Llama-3.2-1B-Instruct | 2048 |
| meta-llama/Llama-3.2-3B-Instruct | 3072 |
| meta-llama/Llama-3.3-70B-Instruct | 8192 |
| meta-llama/Meta-Llama-3-70B-Instruct | 8192 |
| meta-llama/Meta-Llama-3-8B-Instruct | 4096|
| mistralai/Mistral-7B-Instruct-v0.3 | 4096 |
| mistralai/Mixtral-8x7B-Instruct-v0.1 | 4096 | 
| Qwen/Qwen2-Audio-7B-Instruct | 4096 | 
| Qwen/Qwen2.5-32B | 5120 | 
| Qwen/Qwen2.5-32B-Instruct | 5120 | 
| Qwen/Qwen2.5-72B | 8192 | 
| Qwen/Qwen2.5-72B-Instruct | 8192 | 
| Qwen/Qwen3-14B | 5120 | 
| Qwen/Qwen3-32B | 5120 | 
| Qwen/Qwen3-8B | 4096 | 
| Qwen/QwQ-32B | 5120 | 
| TinyLlama/TinyLlama-1.1B-Chat-v1.0 | 2048 |


[^1]: You can also change which model you use for your embeddings if you don't want to use the `TinyLlama/TinyLlama-1.1B-Chat-v1.0` model. A list of models which are compatible with the --task embed argument is COMING SOON, or you can use an embedding model you download such as the `Qwen/Qwen3-Embedding-0.6B` model.
[^2]: If you get the error message `Error in family$linkfun(mustart) : Argument mu must be a nonempty numeric vector`, this is because the model did not respond with a strictly ‘Yes’ or ‘No’ response. Modifying the fuzzylink prompt might solve the issue. I’ve left the prompt as-is and stuck to models that returned properly formatted responses.
[^3]: In this fuzzylink call, `embedding_dimensions` is set to 2048; this is the length of the embedding vector which the TinyLlama/TinyLlama-1.1B-Chat-v1.0 model creates. If you decide to use a different model, you may want to edit this number to have it match that model's specific embedding dimensions. A list of models with their embedding dimensions is COMING SOON.
[^4]: If you leave the api key parameter empty, the fuzzylink code will, by default, try to get an OpenAI api key from your system's environment. If you don't have one, this will cause no problems, and the local model will be able to run without an api key specified. However, if you did not set an `--api-key` when starting your services AND you have an OpenAI api key findable in your system's environment, you will likely encounter an error and will need to define an `--api-key` to use for your local models.
-->

