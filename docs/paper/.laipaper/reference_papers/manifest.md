# Reference Papers for LLM Agents, RAG, and LLM Algorithms

Generated on 2026-07-09.

Selection rule: "past three years" is interpreted as papers appearing from 2023-01-01 through 2026-07-09. Citation counts are `citationCount` values returned by the Semantic Scholar Graph API on 2026-07-09; treat them as a ranking signal, not an absolute citation truth. PDFs were downloaded from arXiv and validated locally as PDF files.

The original ReAct paper is not included because it appeared in 2022, outside this window. The list instead keeps high-citation ReAct-line successors and adjacent agent methods: Toolformer, Tree of Thoughts, Reflexion, Self-Refine, and CodeAct.

| Rank | Theme | Paper | Year | Venue/source | Semantic Scholar citations | arXiv | Local PDF |
|---:|---|---|---:|---|---:|---|---|
| 1 | Foundation LLM | LLaMA: Open and Efficient Foundation Language Models | 2023 | arXiv | 20655 | 2302.13971 | `2302.13971_LLaMA_Open_and_Efficient_Foundation_Language_Models.pdf` |
| 2 | Foundation/chat LLM | Llama 2: Open Foundation and Fine-Tuned Chat Models | 2023 | arXiv | 17502 | 2307.09288 | `2307.09288_Llama_2_Open_Foundation_and_Fine_Tuned_Chat_Models.pdf` |
| 3 | Preference optimization | Direct Preference Optimization: Your Language Model is Secretly a Reward Model | 2023 | NeurIPS | 9546 | 2305.18290 | `2305.18290_DPO_Your_Language_Model_is_Secretly_a_Reward_Model.pdf` |
| 4 | Efficient fine-tuning | QLoRA: Efficient Finetuning of Quantized LLMs | 2023 | NeurIPS | 4961 | 2305.14314 | `2305.14314_QLoRA_Efficient_Finetuning_of_Quantized_LLMs.pdf` |
| 5 | Tool use | Toolformer: Language Models Can Teach Themselves to Use Tools | 2023 | NeurIPS | 4586 | 2302.04761 | `2302.04761_Toolformer_Language_Models_Can_Teach_Themselves_to_Use_Tools.pdf` |
| 6 | Reasoning/search | Tree of Thoughts: Deliberate Problem Solving with Large Language Models | 2023 | NeurIPS | 4414 | 2305.10601 | `2305.10601_Tree_of_Thoughts_Deliberate_Problem_Solving_with_LLMs.pdf` |
| 7 | Agent reflection | Reflexion: Language Agents with Verbal Reinforcement Learning | 2023 | NeurIPS | 4229 | 2303.11366 | `2303.11366_Reflexion_Language_Agents_with_Verbal_Reinforcement_Learning.pdf` |
| 8 | Self-repair/refinement | Self-Refine: Iterative Refinement with Self-Feedback | 2023 | NeurIPS | 3923 | 2303.17651 | `2303.17651_Self_Refine_Iterative_Refinement_with_Self_Feedback.pdf` |
| 9 | RAG/self-critique | Self-RAG: Learning to Retrieve, Generate, and Critique through Self-Reflection | 2023 | ICLR | 2139 | 2310.11511 | `2310.11511_Self_RAG_Learning_to_Retrieve_Generate_and_Critique.pdf` |
| 10 | Code-action agents | Executable Code Actions Elicit Better LLM Agents | 2024 | ICML | 527 | 2402.01030 | `2402.01030_CodeAct_Executable_Code_Actions_Elicit_Better_LLM_Agents.pdf` |

Checked but not included in the 10-paper set:

- RAFT: Adapting Language Model to Domain Specific RAG (2024), 367 Semantic Scholar citations. It is relevant to domain-specific RAG, but lower-cited than Self-RAG and lower priority for a 10-paper cap.
- DSPy: Compiling Declarative Language Model Calls into Self-Improving Pipelines (2023), 824 citations. Relevant to LM pipeline optimization, but less central than the included agent/RAG/code-action papers for this repository.
- HuggingGPT: Solving AI Tasks with ChatGPT and its Friends in Hugging Face (2023), 1566 citations. Relevant to tool orchestration, but less directly aligned than Toolformer and CodeAct.
- Judging LLM-as-a-judge with MT-Bench and Chatbot Arena (2023), 9624 citations. Highly cited and useful for evaluation, but omitted because this set is focused on algorithms rather than evaluator methodology.
