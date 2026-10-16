# Parallax

> Test a message on a simulated crowd before you send it to the real one.

Parallax makes thousands of persona agents react to a campaign, product message or
policy, finds *why* it fails, rewrites it, and re-simulates to show the improvement.

Built for the **Nebius x NVIDIA Global AI Hackathon** (track: Best Apps and Agents).

**Status: early prototype.** The first milestone is a reliability backtest: can
simulated personas reproduce a *real, published* survey result? If not, the project
changes direction (see "Honest limits").

## How it uses NVIDIA Nemotron and Nebius

| Step | Model | Why |
|---|---|---|
| Crowd: thousands of short persona reactions | Nemotron Nano-class (fast, cheap) on **Nebius Token Factory** | Throughput and cost per call |
| Analysis: why it fails + rewrite | Nemotron Ultra-class on Token Factory | Heavier reasoning, few calls |
| Grounding persona context in real data | Tavily API (runtime call) | Fresh local context |

Exact model IDs are read from your Token Factory account: `python scripts/list_models.py`.

## Quick start

```bash
git clone <this repo> && cd parallax
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env            # add NEBIUS_API_KEY (never commit it)
python scripts/list_models.py   # find the Nemotron IDs, put them in .env
```

### Step 1 - reliability backtest

1. Pick a real survey question with published results (Pew, Gallup, Eurobarometer, ...).
2. Copy `data/ground_truth.example.json` to `data/my_survey.json` and fill in the real
   question, options, published distribution and population demographics.
3. Run:

```bash
python scripts/backtest.py --truth data/my_survey.json --n 100
```

It prints real vs simulated distributions and the total variation distance (TVD),
compared with a uniform baseline. No API key? Test the script with `--mock`.

## Honest limits

- Simulated respondents are not real people. Results are directional, not predictions.
- Results depend heavily on persona quality and the chosen survey.
- Validate important decisions with real audience feedback.

## Roadmap

- [x] Backtest script
- [ ] Persona generator grounded in demographic data
- [ ] Crowd simulation engine (parallel, async)
- [ ] Analyst loop: diagnose, rewrite, re-simulate
- [ ] Web UI with live crowd map
- [ ] Demo + 3-minute video

## AI assistance disclosure

Parts of this project were written with AI coding assistants (Claude) and a UI builder
(Lovable). Product decisions and architecture are the author's.

## License

MIT - see [LICENSE](LICENSE).
