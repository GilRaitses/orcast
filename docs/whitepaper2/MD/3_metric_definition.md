# Section 3: R_uncited as a formal evaluation metric

## Definition

Let $S$ be the set of sentences in a system's output. Define $S_\text{sci} \subseteq S$ as the sentences containing scientific or quantitative markers — references to named scientific organizations, species, numerical quantities, statistical terms, or domain-specific technical claims. For each sentence $s \in S_\text{sci}$, let $\text{cited}(s)$ be the indicator that $s$ names at least one entity that appears in the set of bound citations $C$ (place names, artifact labels, or named sources with explicit reference links).

$$R_\text{uncited} = \frac{|\{ s \in S_\text{sci} : \neg\,\text{cited}(s) \}|}{|S_\text{sci}|}$$

This metric is 0 when every scientific sentence names at least one bound citation, and 1 when no scientific sentence does. It is undefined when $|S_\text{sci}| = 0$ (the query produced no scientific claims, as in a pure POI query).

## Properties

$R_\text{uncited}$ has four properties that make it useful as an evaluation primitive:

**Claim-level granularity.** The metric operates at the sentence level rather than the response level. A response with 10 scientific sentences and 9 bound citations still has $R_\text{uncited} = 0.1$. This distinguishes it from response-level accuracy metrics that treat any response as a pass/fail unit.

**Architecture-diagnostic.** Two systems with the same surface accuracy can have very different $R_\text{uncited}$ values depending on whether their reasoning traces are passed as context to the language model. The metric discriminates between systems that produce claims from parametric knowledge and systems that produce claims from evidence-bound context.

**Reproducible.** $R_\text{uncited}$ is computed from the raw output of the language model API — no human annotation is required. The only judgment call is the definition of $S_\text{sci}$, which is implemented as a regex over scientific marker terms and automated from the tool.

**Independent of model.** $R_\text{uncited}$ can be applied to any language model's output, not just Gemini. It does not require access to model internals, training data, or retrieval indices. It measures the binding between output and context, not internal model behavior.

## Relation to Ragas and ALCE

The Ragas framework [2309.15217] evaluates RAG pipelines on faithfulness (whether claims are supported by retrieved context), answer relevancy, and context precision. These metrics require a reference context and measure whether the model used it correctly. $R_\text{uncited}$ measures a weaker but more deployable condition: whether the model's output names sources that appear in the context it was given, without requiring that those sources be in a predefined reference set.

The ALCE benchmark [2305.14627] evaluates citation generation at the claim level — the model must produce text with supporting citations and the benchmark checks citation validity. $R_\text{uncited}$ is complementary: it measures the rate of claims that carry no citation at all, regardless of citation validity. A system that generates mostly uncited claims has a high $R_\text{uncited}$ even if its occasional citations are accurate.
