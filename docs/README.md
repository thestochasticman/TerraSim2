# TerraSim2 documentation

These pages describe the code at commit `4f45710` on branch `rename/flux-terms` (pull request #30, not merged on 24 November 2026). Statements were checked against that code on 24 November 2026. Where a page reports a result that was not reproduced on that date, it says so. Where the pages and the code disagree, the code is authoritative, and the page is in error.

`CLAUDE.md` at the repository root is the compact reference and file tree.

## Pages

1. **[Overview](overview.md)**: scope, what is not represented, the four programs, conventions, layout
2. **[Model inputs](model-inputs.md)**: `ModelInputs`, the on-disk format (version 4), the committed sites
3. **[Soil](soil.md)**: from SLGA to a retention curve, capacity and hydraulics; the −10/−500 J/kg conventions and their basis
4. **[Terrain](terrain.md)**: filled surface, flow direction, flow order, upslope cells, slope, aspect, solar ratio
5. **[Process steps](process-steps.md)**: the step signature and the exact rules of the three steps
6. **[Runs](runs.md)**: the run loop, the zarr store, memory and compute time
7. **[Vegetation](vegetation.md)**: the tree–grass map, tree root depth, the demand factor
8. **[Observations](observations.md)**: observation records, preparation, pairing and scores
9. **[Evaluation](evaluation.md)**: settings and scores at five sites, with provenance and limitations
10. **[Ingest](ingest.md)**: `troi_ingest`, sources and treatment
11. **[Service](service.md)**: `app/api`, the run request, routes, known limitations
12. **[Visualiser](visualiser.md)**: `app/visualiser`, pages and structure
13. **[Development](development.md)**: environment, tests, branches, regenerating data
14. **[History](history.md)**: pull requests 1 to 31

## Sections

### [Overview](overview.md)

- [Scope](overview.md#scope)
- [Programs](overview.md#programs)
- [Code conventions](overview.md#code-conventions)
- [Layout](overview.md#layout)

### [Model inputs](model-inputs.md)

- [The object](model-inputs.md#the-object)
- [On disk: format version 4](model-inputs.md#on-disk-format-version-4)
- [Committed sites](model-inputs.md#committed-sites)

### [Soil](soil.md)

- [From SLGA to a curve per layer](soil.md#from-slga-to-a-curve-per-layer)
- [Capacity and hydraulics over the root depth](soil.md#capacity-and-hydraulics-over-the-root-depth)
- [Conventions: −10 and −500 J/kg](soil.md#conventions-10-and-500-jkg)
- [Reference tables](soil.md#reference-tables)

### [Terrain](terrain.md)

- [Use in the model](terrain.md#use-in-the-model)
- [Resolution](terrain.md#resolution)

### [Process steps](process-steps.md)

- [Signature](process-steps.md#signature)
- [Closed bucket: `step_bucket_model`](process-steps.md#closed-bucket-step_bucket_model)
- [Routed bucket: `step_routed_bucket_model`](process-steps.md#routed-bucket-step_routed_bucket_model)
- [Subsurface step: `step_subsurface_bucket_model`](process-steps.md#subsurface-step-step_subsurface_bucket_model)
- [Settings applied outside the step](process-steps.md#settings-applied-outside-the-step)
- [Not represented](process-steps.md#not-represented)

### [Runs](runs.md)

- [The loop](runs.md#the-loop)
- [The run store](runs.md#the-run-store)
- [Reading a run](runs.md#reading-a-run)
- [Service runs](runs.md#service-runs)
- [Compute time](runs.md#compute-time)

### [Vegetation](vegetation.md)

- [The map](vegetation.md#the-map)
- [Classification](vegetation.md#classification)
- [Tree root depth](vegetation.md#tree-root-depth)
- [Demand factor (cover)](vegetation.md#demand-factor-cover)

### [Observations](observations.md)

- [The object](observations.md#the-object)
- [Preparation](observations.md#preparation)
- [Pairing](observations.md#pairing)
- [Scores](observations.md#scores)
- [In the service and viewer](observations.md#in-the-service-and-viewer)

### [Evaluation](evaluation.md)

- [Provenance](evaluation.md#provenance)
- [Limitations](evaluation.md#limitations)
- [Method](evaluation.md#method)
- [Settings and scores](evaluation.md#settings-and-scores)
- [Observations at each site](evaluation.md#observations-at-each-site)
- [Effect of the soil-convention change](evaluation.md#effect-of-the-soil-convention-change)
- [Per-site figures](evaluation.md#per-site-figures)

### [Ingest](ingest.md)

- [Sources and treatment](ingest.md#sources-and-treatment)
- [The window](ingest.md#the-window)
- [Functions and commands](ingest.md#functions-and-commands)
- [Provenance](ingest.md#provenance)

### [Service](service.md)

- [Start](service.md#start)
- [Run request](service.md#run-request)
- [Routes](service.md#routes)
- [Known limitations](service.md#known-limitations)
- [Tests](service.md#tests)

### [Visualiser](visualiser.md)

- [Commands](visualiser.md#commands)
- [Pages](visualiser.md#pages)
- [Run page](visualiser.md#run-page)
- [Soils page](visualiser.md#soils-page)
- [Code structure](visualiser.md#code-structure)

### [Development](development.md)

- [Environment](development.md#environment)
- [Tests](development.md#tests)
- [Branches and pull requests](development.md#branches-and-pull-requests)
- [Conventions](development.md#conventions)
- [Regenerating the committed data](development.md#regenerating-the-committed-data)
- [Evaluation scripts](development.md#evaluation-scripts)

### [History](history.md)

- [Phase 1: viewer, ingest, model loop, service (PRs 1–13, 27 Oct – 1 Nov)](history.md#phase-1-viewer-ingest-model-loop-service-prs-113-27-oct--1-nov)
- [Phase 2: soil physics and terrain (PRs 14–19, 4 Nov)](history.md#phase-2-soil-physics-and-terrain-prs-1419-4-nov)
- [Phase 3: flow, observations, levers, calibration (PRs 20–28, 8 Nov)](history.md#phase-3-flow-observations-levers-calibration-prs-2028-8-nov)
- [After 8 November](history.md#after-8-november)
