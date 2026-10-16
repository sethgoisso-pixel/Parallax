"""
Persona reliability backtest.

Makes N simulated people answer a real survey question, then compares the
simulated answer distribution with the published one.

  python scripts/backtest.py --truth data/my_survey.json --n 100
  python scripts/backtest.py --truth data/ground_truth.example.json --n 20 --mock   # no API key needed

Metric: total variation distance (TVD, 0 = identical, 1 = disjoint).
We compare against a uniform baseline: a useful simulator must beat it.
"""
import argparse, json, os, random, re, sys
from collections import Counter
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def sample_persona(demo, rng):
    return {k: rng.choices(list(v), weights=list(v.values()))[0] for k, v in demo.items()}


def build_prompt(persona, population, question, options):
    who = ", ".join(f"{k}: {v}" for k, v in persona.items())
    opts = "\n".join(f"{k}. {v}" for k, v in options.items())
    system = (
        "You role-play a real person answering a survey. Stay in character, answer as "
        "that person honestly would, not as an AI and not with what seems 'correct'."
    )
    user = (
        f"You are a member of this population: {population}.\n"
        f"Your profile - {who}.\n\n"
        f"Survey question: {question}\n{opts}\n\n"
        f"Reply with ONLY the letter of your answer ({', '.join(options)})."
    )
    return system, user


def parse_answer(text, options):
    # Take the LAST standalone option letter (models may reason before answering)
    letters = [l for l in re.findall(r"\b([A-Z])\b", (text or "").upper()) if l in options]
    return letters[-1] if letters else None


def tvd(p, q, keys):
    return 0.5 * sum(abs(p.get(k, 0) - q.get(k, 0)) for k in keys)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--truth", required=True)
    ap.add_argument("--n", type=int, default=100)
    ap.add_argument("--model", default=os.environ.get("PARALLAX_CROWD_MODEL"))
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--mock", action="store_true", help="fake answers, no API call (test the script)")
    a = ap.parse_args()

    truth = json.load(open(a.truth))
    if truth.get("source") == "PLACEHOLDER":
        print("WARNING: ground truth is PLACEHOLDER data - results are meaningless.\n")
    opts, true_dist = truth["options"], truth["true_distribution"]
    keys = list(opts)
    rng = random.Random(a.seed)
    personas = [sample_persona(truth["demographics"], rng) for _ in range(a.n)]

    if a.mock:
        answers = [rng.choice(keys) for _ in personas]
    else:
        if not a.model:
            sys.exit("Set PARALLAX_CROWD_MODEL in .env or pass --model (run scripts/list_models.py).")
        from parallax.llm import get_client, chat
        client = get_client()

        def ask(p):
            s, u = build_prompt(p, truth["population"], truth["question"], opts)
            try:
                return parse_answer(chat(client, a.model, s, u, temperature=0.9, max_tokens=20), opts)
            except Exception as e:
                print("API error:", e, file=sys.stderr)
                return None

        with ThreadPoolExecutor(a.workers) as ex:
            answers = list(ex.map(ask, personas))

    valid = [x for x in answers if x]
    if not valid:
        sys.exit("No valid answers were parsed.")
    c = Counter(valid)
    sim = {k: c.get(k, 0) / len(valid) for k in keys}
    uniform = {k: 1 / len(keys) for k in keys}

    print(f"Answers parsed: {len(valid)}/{a.n}")
    print(f"{'opt':<4}{'real':>8}{'simulated':>11}")
    for k in keys:
        print(f"{k:<4}{true_dist[k]:>8.2%}{sim[k]:>11.2%}   {opts[k][:50]}")
    d_sim, d_uni = tvd(sim, true_dist, keys), tvd(uniform, true_dist, keys)
    print(f"\nTVD simulated vs real : {d_sim:.3f}")
    print(f"TVD uniform  vs real : {d_uni:.3f}  (baseline to beat)")
    verdict = "PROMISING" if d_sim < 0.5 * d_uni and d_sim < 0.15 else "NOT CONVINCING"
    print(f"Verdict (rough rule): {verdict}")

    os.makedirs("results", exist_ok=True)
    json.dump({"truth": true_dist, "simulated": sim, "tvd": d_sim, "tvd_uniform": d_uni,
               "n": a.n, "model": a.model, "mock": a.mock},
              open("results/last_backtest.json", "w"), indent=2)


if __name__ == "__main__":
    main()
