# TerraSim2 documentation

One page per part of the system. Read them in order for the whole picture, or go straight to the part you need; every page carries links to the previous page, this index and the next. The repository's `CLAUDE.md` is the compact reference the code is held to; these pages explain the same material at more length. Where the two disagree, the code is right and both should be fixed.

## Pages

1. **[Overview](overview.md)** — What TerraSim2 is, the three programs, the handoff between them, and the conventions every file follows
2. **[Model inputs](model-inputs.md)** — The `ModelInputs` object, its on-disk layout (format version 4), and the committed development sites
3. **[Soil](soil.md)** — From the Soil and Landscape Grid to a retention curve and a capacity per cell; the field-capacity and wilting-point conventions and their calibration
4. **[Terrain](terrain.md)** — What is derived from the elevation model: filled surface, flow directions, flow order, contributing area, slope, aspect and annual irradiance
5. **[Process steps](process-steps.md)** — The step protocol and the three steps (closed bucket, routed bucket, subsurface), their parameters and their named fluxes
6. **[Runs](runs.md)** — The run loop, the zarr run store and how a run is read back
7. **[Vegetation](vegetation.md)** — The tree–grass map from a year of Sentinel-2 NDVI, root depth per class and the cover lever on demand
8. **[Observations](observations.md)** — Field observations as the model holds them, how they are prepared, paired with a run and scored
9. **[Evaluation](evaluation.md)** — What the evaluation at five sites found: settings per site, scores, the soil-convention calibration, per-site figures and caveats
10. **[Ingest](ingest.md)** — `troi_ingest`: how inputs, observations and vegetation maps are prepared from the lab's data stores
11. **[Service](service.md)** — The `app/api` service: routes, the run request, run ids and the worker
12. **[Visualiser](visualiser.md)** — The `app/visualiser` Next.js viewer: pages, components, colourings and charts
13. **[Development](development.md)** — Environment, tests, branches and pull requests, and how to regenerate the committed data
14. **[History](history.md)** — How the code base grew, pull request by pull request, and what each step found

## Sections

### [Overview](overview.md)

- [Why](overview.md#why)
- [Three programs](overview.md#three-programs)
- [Conventions that hold everywhere](overview.md#conventions-that-hold-everywhere)
- [Where things are](overview.md#where-things-are)

### [Model inputs](model-inputs.md)

- [The object](model-inputs.md#the-object)
- [On disk: format version 4](model-inputs.md#on-disk-format-version-4)
- [The committed sites](model-inputs.md#the-committed-sites)

### [Soil](soil.md)

- [From the map to a curve](soil.md#from-the-map-to-a-curve)
- [Capacity and hydraulics over the root depth](soil.md#capacity-and-hydraulics-over-the-root-depth)
- [The conventions: −10 and −500 J/kg](soil.md#the-conventions-10-and-500-jkg)
- [The reference tables](soil.md#the-reference-tables)

### [Terrain](terrain.md)

- [What each is for](terrain.md#what-each-is-for)
- [Resolution](terrain.md#resolution)

### [Process steps](process-steps.md)

- [The protocol](process-steps.md#the-protocol)
- [The closed bucket — `step_bucket_model`](process-steps.md#the-closed-bucket--step_bucket_model)
- [The routed bucket — `step_routed_bucket_model`](process-steps.md#the-routed-bucket--step_routed_bucket_model)
- [The subsurface step — `step_subsurface_bucket_model`](process-steps.md#the-subsurface-step--step_subsurface_bucket_model)
- [Levers outside the step](process-steps.md#levers-outside-the-step)
- [What the evaluation made of them](process-steps.md#what-the-evaluation-made-of-them)

### [Runs](runs.md)

- [The loop](runs.md#the-loop)
- [The run store](runs.md#the-run-store)
- [Reading a run](runs.md#reading-a-run)
- [As the service runs it](runs.md#as-the-service-runs-it)

### [Vegetation](vegetation.md)

- [The map](vegetation.md#the-map)
- [Classification](vegetation.md#classification)
- [Root depth per class](vegetation.md#root-depth-per-class)
- [The cover lever](vegetation.md#the-cover-lever)

### [Observations](observations.md)

- [The object](observations.md#the-object)
- [Preparation](observations.md#preparation)
- [Pairing](observations.md#pairing)
- [Scores](observations.md#scores)
- [In the service and the viewer](observations.md#in-the-service-and-the-viewer)

### [Evaluation](evaluation.md)

- [Method](evaluation.md#method)
- [Settings and scores](evaluation.md#settings-and-scores)
- [What each site constrains](evaluation.md#what-each-site-constrains)
- [The soil-convention calibration](evaluation.md#the-soil-convention-calibration)
- [Per-site figures](evaluation.md#per-site-figures)
- [Caveats](evaluation.md#caveats)

### [Ingest](ingest.md)

- [The stores](ingest.md#the-stores)
- [The window](ingest.md#the-window)
- [Functions and commands](ingest.md#functions-and-commands)
- [Provenance](ingest.md#provenance)

### [Service](service.md)

- [Start](service.md#start)
- [The run request](service.md#the-run-request)
- [Routes](service.md#routes)
- [Known limitation](service.md#known-limitation)
- [Tests](service.md#tests)

### [Visualiser](visualiser.md)

- [Run](visualiser.md#run)
- [Pages](visualiser.md#pages)
- [The run page](visualiser.md#the-run-page)
- [The soils page](visualiser.md#the-soils-page)
- [Structure](visualiser.md#structure)

### [Development](development.md)

- [Environment](development.md#environment)
- [Tests](development.md#tests)
- [Branches and pull requests](development.md#branches-and-pull-requests)
- [Conventions](development.md#conventions)
- [Regenerating the committed data](development.md#regenerating-the-committed-data)
- [Evaluating a site](development.md#evaluating-a-site)

### [History](history.md)

- [Phase 1: viewer, ingest, model loop, service (PRs 1–13, 27 Oct – 1 Nov)](history.md#phase-1-viewer-ingest-model-loop-service-prs-113-27-oct--1-nov)
- [Phase 2: soil physics and terrain (PRs 14–19, 4 Nov)](history.md#phase-2-soil-physics-and-terrain-prs-1419-4-nov)
- [Phase 3: flow, observations, levers, calibration (PRs 20–28, 8 Nov)](history.md#phase-3-flow-observations-levers-calibration-prs-2028-8-nov)
- [Afterwards](history.md#afterwards)

## By question

- *What does a cell hold and what moves it?* [Process steps](process-steps.md), [Soil](soil.md), [Terrain](terrain.md)
- *Where do the numbers come from?* [Ingest](ingest.md), [Model inputs](model-inputs.md)
- *How good is it, and where?* [Evaluation](evaluation.md), [Observations](observations.md)
- *How do I run it and look at it?* [Service](service.md), [Visualiser](visualiser.md), [Runs](runs.md)
- *How do I change it without breaking the rules?* [Overview](overview.md), [Development](development.md)
- *Why is it the way it is?* [History](history.md)
