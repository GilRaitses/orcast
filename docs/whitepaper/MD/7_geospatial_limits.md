# 7. Geospatial grounding limits for scientific evidence

We conducted a live benchmark comparing Google Maps grounding available through the Gemini Interactions API against the orcast structured provenance system on the same marine science query domain.

## Benchmark methodology

The benchmark used Gemini 3.5 Flash with Api-Revision 2026-05-20 and the google_maps tool enabled, with coordinates 48.5465, -123.03 (San Juan Islands pilot region). Three query types were tested: a place-of-interest query (cafe near Friday Harbor), an evidence query (where are southern resident killer whales seen from shore, and what is the evidence), and a mixed planning query (shore-based whale watching itinerary). For each query we measured the total citation count, the split between place citations and scientific or dataset citations, the grounding density per thousand words, and the unsupported scientific claim rate, defined as the fraction of sentences containing quantitative or scientific content with no bound citation.

The orcast-side comparison used the same orca evidence query submitted to the orcast /api/interactions/plan route with agent key authentication, counting annotations carrying an artifact reference or href (bound evidence) versus unbound annotations.

The measurement tool is available at tools/testing/maps_grounding_probe.py.

## Results

Across the three Maps grounding queries, 0 of 25 total citations resolved to scientific or dataset sources; all 25 resolved to Google Maps place pins (maps.google.com/?cid= links). The evidence query generated 9 sentences containing scientific content, including references to NOAA-style fisheries data, the Center for Whale Research census, Fraser River Chinook salmon corridors, and J/K/L pod hydrophone acoustic data; 8 of 9 sentences (89 percent) carried no citation. The mixed query produced 8 scientific sentences with 5 unsupported (63 percent). Averaged across evidence-bearing queries, the uncited scientific claim rate was 85 percent.

The orcast annotation result: 6 of 6 annotations carried an artifact reference or href, producing an uncited rate of 0 percent. All claims were bound to a producing skill, annotation type, and artifact or provenance link.

This result does not reflect a deficiency in the Gemini or Maps system; it reflects the structural scope boundary of geospatial grounding. Maps grounding is designed to provide place information (reviews, hours, locations) and excels at that: the POI query achieved 8 citations in 229 words (35 per thousand words) with 0 scientific claims and 0 unsupported sentences. The boundary is that place grounding cannot resolve scientific evidence claims to their origin data, method, or experiment. A domain-specific provenance system is required for the evidence layer.

The paper on LLM geospatial knowledge \cite{arxiv231013002} provides peer-reviewed evidence that geospatial competence in LLMs degrades substantially for knowledge that is not encoded as named places in training data. Scientific evidence about cetacean ecology (bathymetric corridors, salmon run timing, acoustic behavioral data) is domain-specific knowledge not encoded as place pins, and place grounding leaves it entirely uncited.

## Benchmark date and reproducibility

Benchmark run: 2026-06-24. Model: gemini-3.5-flash. API revision: 2026-05-20. Coordinates: 48.5465, -123.03. The benchmark is fully reproducible using tools/testing/maps_grounding_probe.py with a Gemini API key.
