# Optional cinema-screen texture

Use this effect to make the footage look like a recording of a projected cinema screen. The conservative default changes quality while preserving the scene's geometry.

The renderer applies this chain before splitting the footage into its sharp panel and blurred moving background:

```text
gblur=sigma=0.65,
eq=contrast=0.85:brightness=0.018:saturation=0.76:gamma=1.04,
noise=alls=5:allf=t+u:all_seed=23,
vignette=PI/9,
eq=brightness='0.004*sin(2*PI*7*t)+0.003*sin(2*PI*0.6*t)':eval=frame
```

Softness and grain should be noticeable without hiding faces or expressions. The small brightness oscillation suggests a recorded projection. Keep it mild. Apply the effect to footage, then add the sharp headline, watermark, and CTA.

Do not make perspective skew, handheld drift, downsampling, mirror, crop, or zoom implicit. Earlier one-off edits used some of those; they are separate creative requests. A request to change only quality forbids changing sizing or placement.

Select the option with:

```sh
python3 scripts/build_reel.py \
  --clip-a source.mp4 --start-a 57 --end-a 96 \
  --title-a 'PAID TOKENS RAN OUT' \
  --watermark approved-watermark.mov \
  --footage-effect cinema \
  --output output/cinema-reel.mp4 --preview-dir output/previews
```

For an A/B review, render the same input with `--footage-effect clean`. Compare resolution, source trim, panel boundaries, graphic placement, runtime, and audio. Inspect a face and a dark area for excessive softness or grain. Both versions should use the same layout and timing. A deliberate final-frame hold, if enabled for CTA fit, must be reported separately from the cinema effect.
