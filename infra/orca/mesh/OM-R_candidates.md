# OM-R Orca Mesh Candidate Survey

Read-only research. Dated 2026-06-28. Wave OM-R for the ORCA biologging twin program.

This document surveys open-source orca and killer whale 3D meshes with verified permissive licenses for use in a react-three-fiber / three.js underwater scene. Nothing was downloaded, converted, or committed. All license fields below were read off the live source pages on 2026-06-28.

## License rule applied

A mesh is acceptable only if it carries a verified CC0, CC-BY, CC-BY-SA, or public-domain license, with the source URL, author, exact license, and required attribution text recorded. CC-BY-NC and CC-BY-ND are not acceptable. Derivatives must be allowed because the mesh will be re-rigged and converted to glb.

## License verdict

Acceptable meshes found. There are multiple full-body orca meshes under CC-BY and CC-BY-SA with download enabled and derivatives allowed. No escalation is required. The license risk is concentrated in the rejected pile (Sketchfab Free Standard, CGTrader Royalty Free, AI-generated CC0 claims, and unmarked portfolio previews), which is why those are excluded below rather than ranked.

## Ranked candidate table

| Rank | Name | Source URL | Author | Exact license | Formats | Poly count | Topology / rig-readiness | UVs / textures | Caveats |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Killer Whale | https://sketchfab.com/3d-models/killer-whale-63b680d7e58f463a9868ed7bf163094a | Trouvaille (@dashdu) | CC Attribution (CC-BY 4.0) | Sketchfab download ships glTF and glb, plus original upload format | 3.1k triangles, 1.5k vertices | Full-body orca with dorsal fin, pectoral flippers, and fluke all modeled in one piece. Low triangulated mesh, easy to weight, but coarse. Fluke and flippers are visually separable but not separate objects, so the rigging wave gets a single clean skin to weight. Needs light cleanup or retopo if a smooth fluke beat is wanted. | Reported as a basic colored model. Treat UVs and textures as minimal and verify on download. | Triangulated rather than quad. Low detail. Confirm UV presence after download. |
| 2 | Killer Whale (Poly by Google) | https://poly.pizza/m/7pqZEQ9b_E- | Poly by Google | CC Attribution 3.0 (https://creativecommons.org/licenses/by/3.0/) | OBJ and glTF | About 1.5k triangles, 4.4k vertices | Stylized low-poly full body. Single node, single mesh. Native glTF, which matches the existing glb plus meshopt path most directly. Easy to scale and orient. Triangulated, so coarse deformation on a fluke beat. | No textures. Single node, vertex or material color only. | No textures and very low detail. Cleanest license provenance of the set. Poly by Google is retired, so Poly Pizza is the durable mirror. |
| 3 | Orca | https://blendswap.com/blend/4425 | DaveC | CC-BY | .blend only (Blender 2.6x) | Low poly, count not stated | Hand-built Blender mesh described as just a mesh and a texture, no rig, with a corrected blow hole. Native Blender source means the cleanest quad-ish topology of the set, which is the best raw base for re-rigging and for subdividing into a smooth fluke. | Has a texture per the description. | .blend only, so it must be opened in Blender and exported to glb. Very old (about 14 years). No rig. Best topology, worst convenience. |
| 4 (reference only) | Orcinus orca 3D scan, C 301 | https://commons.wikimedia.org/wiki/File:Orcinus_orca_3d_scan_Natural_History_Museum_University_of_Pisa_C_301.stl | Natural History Museum of the University of Pisa | CC BY-SA 4.0 | STL | Dense scan, count not stated | Real museum specimen scan, but it is a skeleton, not a fleshed body. STL triangle soup with no UVs. Not suitable as the swimming skin. Useful only as an anatomical and proportion reference for the odontocete skeleton placement in the rigging wave. | None. STL has no UVs or textures. | Skeleton only. Wrong subject for a skinned swimming body. CC-BY-SA is share-alike, so any derivative distributed must also be BY-SA. Keep as reference, do not use as the body mesh. |

## Rejected or not usable

These were checked and excluded for license or availability reasons. They were not downloaded.

| Name | Source URL | Reason rejected |
|---|---|---|
| Killer whale (Orcinus orca), 72.2k tris | https://sketchfab.com/3d-models/killer-whale-orcinus-orca-174dc4d068984453b78dfe8a46929e19 | High detail and good topology, but the page shows no download button and no Creative Commons license. It reads as a portfolio preview for Cinema 4D, effectively all rights reserved. Not usable. |
| Low Poly Killer Whale (Orca) | https://sketchfab.com/3d-models/low-poly-killer-whale-orca-3d-model-da8c4f4d4fc94cae9baee8849e6e1e64 | License is Sketchfab Free Standard plus an explicit NoAI clause. Free Standard is not a Creative Commons license and its redistribution and derivative terms are restrictive and ambiguous for this use. Excluded. |
| Orca (Killer Whale) Rigged 3D Model | https://sketchfab.com/3d-models/orca-killer-whale-rigged-3d-model-b959c9c432d84987b8170235ca9d555f | 129.3k tris, rigged, textured, but no Creative Commons license is shown on the page and the rig is noted as not animation grade. License not verifiable as permissive. Excluded. |
| Killer Whale Orca, Rigged (CGTrader) | https://www.cgtrader.com/free-3d-models/animal/mammal/killer-whale-orca-rigged | License is CGTrader Royalty Free with a no-AI clause. This is a proprietary EULA, not Creative Commons, with constrained redistribution. Not clearly permissive for re-rig and re-host. Excluded. |
| Meshy AI-generated orca assets | https://www.meshy.ai/tags/orca | Claimed CC0, but assets are AI-generated on demand with unverifiable provenance and unreliable topology. CC0 claim on machine-generated output is not a dependable basis. Excluded. |
| Printables orca STL models (Matt, LowPolyFigures, Jopek Design) | https://www.printables.com/model/1528043-orca | Print-oriented STL meshes. Licenses are not confirmed as Creative Commons on the listing summaries, and STL has no UVs and watertight print topology that is poor for skinning. Excluded. |

## Smithsonian, NOAA, MorphoSource notes

The Smithsonian Open Access 3D portal (https://3d.si.edu) returns no downloadable fleshed killer whale body. The only orca-related 3D object found is the Tlingit Killer Whale Hat (https://3d.si.edu/object/3d/killer-whale-hat%3Ad8c6343a-4ebc-11ea-b77f-2e728ce88125), which carries usage conditions and an explicit clan request that downloads are not authorized, so it is off limits and is not an orca animal anyway. The physical Smithsonian orca skeleton is a research specimen with no published 3D download. No NOAA-hosted downloadable orca mesh was found. MorphoSource and museum scan repos in this space tend to host skeleton or skull scans with access requests and BY or BY-SA terms, the same category as the Pisa skeleton above, which is reference material and not a skinned body.

## Primary recommendation

Primary: Killer Whale by Trouvaille on Sketchfab.

- Source URL: https://sketchfab.com/3d-models/killer-whale-63b680d7e58f463a9868ed7bf163094a
- Author: Trouvaille (@dashdu)
- Exact license: Creative Commons Attribution (CC-BY 4.0)
- Required attribution text to reproduce: "Killer Whale" by Trouvaille (https://sketchfab.com/dashdu) licensed under CC-BY 4.0 (https://creativecommons.org/licenses/by/4.0/), via Sketchfab (https://sketchfab.com/3d-models/killer-whale-63b680d7e58f463a9868ed7bf163094a). Confirm the exact creator handle and the copy-paste attribution string Sketchfab presents in the download dialog at download time.

Why this is primary. It is a complete orca body with dorsal fin, pectoral flippers, and fluke modeled, it is CC-BY with derivatives allowed, and the Sketchfab download path already produces glTF and glb, which lines up with the proven glb plus EXT_meshopt_compression tile path in web/lib/scene/tiles/useTilesLayer.ts. At 3.1k triangles it is light, it scales and orients cleanly to heading +X and up +Y, and it maps comfortably into the twin frame where an adult orca around 6 to 8 m lands near 0.018 to 0.024 scene units at the live worldUnitsPerMeter of about 0.003. The single-piece skin is straightforward for the rigging wave to place an odontocete skeleton against and weight, and the fluke is present for the motion wave dorso-ventral beat.

Rig-readiness caveat. The mesh is triangulated and low detail, so the rigging wave should expect to do light cleanup or a quick retopo if a smooth fluke deformation is required, and should verify UVs after download.

## Backup recommendation

Backup: Killer Whale by Poly by Google, hosted on Poly Pizza.

- Source URL: https://poly.pizza/m/7pqZEQ9b_E-
- Author: Poly by Google
- Exact license: Creative Commons Attribution 3.0 (https://creativecommons.org/licenses/by/3.0/)
- Required attribution text to reproduce: "Killer Whale" by Poly by Google licensed under CC-BY 3.0 (https://creativecommons.org/licenses/by/3.0/), via Poly Pizza (https://poly.pizza/m/7pqZEQ9b_E-).

Why this is backup. It ships native glTF and OBJ, which is the most direct match for the glb pipeline, the CC-BY 3.0 provenance is the cleanest and least ambiguous in the survey, and it is extremely light at about 1.5k triangles. The trade-offs are that it has no textures and very low detail, so it is a fallback if the primary download has UV or topology problems.

Topology alternative worth noting. If the rigging wave prefers the cleanest quad base over convenience, the DaveC Orca on BlendSwap (https://blendswap.com/blend/4425, CC-BY) is native Blender geometry and likely the best raw topology for re-rigging and smooth fluke subdivision, at the cost of a .blend to glb export step and its age.

## Handoff notes for the rigging wave (OR) and motion wave (OG)

- All recommended bodies are single-piece skins. Pectoral flippers, dorsal fin, and fluke are modeled but are not separate objects, so plan to define them by region or vertex group during weighting rather than expecting separate meshes.
- Use the Pisa skeleton scan as an anatomy and proportion reference for odontocete skeleton placement, not as geometry to import.
- Confirm UVs and the exact attribution string at download time. The attribution text above must travel with the converted glb and any published build.
