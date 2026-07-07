"""Routing-quality benchmark for :class:`~soup.strategies.bm25.BM25Strategy`.

Toy two-skill examples (like the README's) don't expose how BM25 behaves on a
realistic catalog, where a product has a few dozen skills/playbooks and real
users phrase requests however they like -- rarely echoing the exact words in
a skill's ``description``.

This script builds such a catalog (support/product-style skills, the target
use case for Soup: single-shot LLM calls that must pick context *before* the
call, with no tool-calling loop to fall back on) plus a labeled query set,
then reports precision/recall/F1 for two configurations:

* **baseline** -- retrieval over ``name`` + ``description`` + ``tags`` only.
* **with examples** -- retrieval also indexes ``examples`` (short "training
  phrases" authors attach to a skill), which is what ``BM25Strategy`` does by
  default.

Run with:

    python benchmarks/routing_benchmark.py

No external dependencies beyond Soup itself.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from soup import BM25Strategy, Skill

# --------------------------------------------------------------------------
# Catalog: a support/product-style skill set (~15 skills), each with a
# description an author would naturally write, plus a few realistic example
# phrasings ("training phrases") a real user might type.
# --------------------------------------------------------------------------

_SKILLS: list[Skill] = [
    Skill(
        name="billing-support",
        description="Handle billing questions: invoices, subscriptions, and charges.",
        instructions="...",
        tags=("billing", "invoices", "subscription"),
        examples=(
            "why was I charged twice this month",
            "I want to cancel my plan",
            "can I get an invoice for last month",
        ),
    ),
    Skill(
        name="account-security",
        description="Assist with account access: passwords, 2FA, and lockouts.",
        instructions="...",
        tags=("security", "login", "2fa"),
        examples=(
            "I can't log into my account anymore",
            "how do I turn on two factor authentication",
            "I forgot my password",
        ),
    ),
    Skill(
        name="shipping-returns",
        description="Guidance for order returns, refunds, and shipment tracking.",
        instructions="...",
        tags=("returns", "refunds", "shipping"),
        examples=(
            "my package never arrived",
            "how do I send this item back",
            "when will I get my money back for the return",
        ),
    ),
    Skill(
        name="api-auth",
        description="Explain API authentication: keys, tokens, and OAuth flows.",
        instructions="...",
        tags=("api", "auth", "oauth"),
        examples=(
            "how do I generate an api key",
            "my requests are getting 401 errors",
            "what oauth scopes do I need",
        ),
    ),
    Skill(
        name="deployment-devops",
        description="Help with CI/CD, containers, and production deployments.",
        instructions="...",
        tags=("devops", "deployment", "docker"),
        examples=(
            "my docker build is failing",
            "how do I set up a deploy pipeline",
            "the production rollout is stuck",
        ),
    ),
    Skill(
        name="data-export",
        description="Support exporting and downloading account data.",
        instructions="...",
        tags=("export", "csv", "download"),
        examples=(
            "how do I download all my data",
            "can I get a csv of my records",
        ),
    ),
    Skill(
        name="email-notifications",
        description="Configure email alerts and notification preferences.",
        instructions="...",
        tags=("email", "notifications", "alerts"),
        examples=(
            "how do I stop getting so many emails",
            "I want a notification every time something changes",
        ),
    ),
    Skill(
        name="mobile-app",
        description="Troubleshoot the iOS and Android mobile applications.",
        instructions="...",
        tags=("mobile", "ios", "android"),
        examples=(
            "the app keeps crashing on my phone",
            "it won't open on my iPad",
        ),
    ),
    Skill(
        name="performance-optimization",
        description="Diagnose and improve application response times.",
        instructions="...",
        tags=("performance", "latency", "optimization"),
        examples=(
            "everything feels really slow lately",
            "pages take forever to load",
            "help me speed things up",
        ),
    ),
    Skill(
        name="legal-compliance",
        description="Answer questions about privacy policy, GDPR, and terms.",
        instructions="...",
        tags=("legal", "privacy", "gdpr"),
        examples=(
            "how do I delete all my personal data",
            "where is your privacy policy",
        ),
    ),
    Skill(
        name="onboarding",
        description="Walk new users through initial setup and first steps.",
        instructions="...",
        tags=("onboarding", "setup", "getting-started"),
        examples=(
            "I just signed up, what do I do first",
            "how do I set up my workspace",
        ),
    ),
    Skill(
        name="internationalization",
        description="Support localization, translations, and language settings.",
        instructions="...",
        tags=("i18n", "locale", "translation"),
        examples=(
            "can I use the app in spanish",
            "how do I change the display language",
        ),
    ),
    Skill(
        name="react-ui",
        description="React UI implementation patterns for components and hooks.",
        instructions="...",
        tags=("react", "ui", "components"),
        examples=(
            "my dashboard layout looks broken on mobile",
            "how do I make this button component reusable",
        ),
    ),
    Skill(
        name="sql-postgres",
        description="Postgres SQL guidance for query design and indexing.",
        instructions="...",
        tags=("sql", "postgres", "database"),
        examples=(
            "my database queries are taking too long",
            "should I add an index for this filter",
        ),
    ),
    Skill(
        name="pdf-processing",
        description="Extract PDF text, fill forms, and merge files.",
        instructions="...",
        tags=("pdf", "forms", "documents"),
        examples=(
            "how do I pull text out of a pdf",
            "can I merge multiple pdf files into one",
        ),
    ),
]

# --------------------------------------------------------------------------
# Labeled query set: realistic phrasings, deliberately avoiding the exact
# wording of the matching skill's description where possible. `expected`
# is `None` for queries that shouldn't trigger any skill (specificity check).
# --------------------------------------------------------------------------


@dataclass
class Case:
    query: str
    expected: str | None
    note: str = ""


_CASES: list[Case] = [
    Case("why did you bill me two times this month?", "billing-support"),
    Case("I need to stop my subscription", "billing-support"),
    Case("locked out of my account, can't remember the password", "account-security"),
    Case("need to enable 2fa on my profile", "account-security"),
    Case("the item I sent back hasn't been refunded yet", "shipping-returns"),
    Case("tracking says delivered but I never got the box", "shipping-returns"),
    Case("getting 401 unauthorized on every api call", "api-auth"),
    Case("what scopes does my oauth token need for this endpoint", "api-auth"),
    Case("kubernetes pods keep crashlooping after deploy", "deployment-devops"),
    Case("our ci pipeline is red, docker build fails", "deployment-devops"),
    Case("I want a csv dump of everything in my account", "data-export"),
    Case("too many notification emails, please help", "email-notifications"),
    Case("android app force closes on launch", "mobile-app"),
    Case("my database is slow, what should I check?", "sql-postgres", note="vocab-gap case"),
    Case(
        "help me speed up my website",
        "performance-optimization",
        note="vocab-gap case",
    ),
    Case(
        "how do I make my app UI faster and more interactive for end users?",
        "performance-optimization",
        note="vocab-gap, ui+speed overlap with react-ui",
    ),
    Case("can you delete every bit of my personal info", "legal-compliance"),
    Case("just signed up, where do I even start", "onboarding"),
    Case("switch the interface to french please", "internationalization"),
    Case("this card component re-renders way too often", "react-ui"),
    Case("need to pull the text content out of a scanned pdf", "pdf-processing"),
    Case("what's the weather like tomorrow", None, note="no relevant skill exists"),
    Case("tell me a joke", None, note="no relevant skill exists"),
]


@dataclass
class Report:
    label: str
    hits_at_1: int = 0
    recall_hits: int = 0
    false_positives: int = 0
    total_positive: int = 0
    total_negative: int = 0
    misses: list[Case] = field(default_factory=list)


def _evaluate(label: str, skills: list[Skill]) -> Report:
    strategy = BM25Strategy()
    report = Report(label=label)
    for case in _CASES:
        ranked = strategy.rank(case.query, skills)
        names = [s.name for s, _ in ranked]
        top = names[0] if names else None

        if case.expected is None:
            report.total_negative += 1
            if names:
                report.false_positives += 1
                report.misses.append(case)
        else:
            report.total_positive += 1
            if top == case.expected:
                report.hits_at_1 += 1
            if case.expected in names:
                report.recall_hits += 1
            else:
                report.misses.append(case)
    return report


def _strip_examples(skills: list[Skill]) -> list[Skill]:
    return [s.model_copy(update={"examples": ()}) for s in skills]


def _print_report(report: Report) -> None:
    recall = report.recall_hits / report.total_positive if report.total_positive else 0.0
    hit1 = report.hits_at_1 / report.total_positive if report.total_positive else 0.0
    fpr = report.false_positives / report.total_negative if report.total_negative else 0.0

    print(f"\n=== {report.label} ===")
    print(f"Hit@1        : {hit1:.0%}  ({report.hits_at_1}/{report.total_positive})")
    print(f"Recall       : {recall:.0%}  ({report.recall_hits}/{report.total_positive})")
    print(
        f"False-pos rate: {fpr:.0%}  ({report.false_positives}/{report.total_negative} "
        "unrelated queries wrongly matched)"
    )
    if report.misses:
        print("Misses:")
        for case in report.misses:
            note = f"  [{case.note}]" if case.note else ""
            print(f"  - {case.query!r} (expected={case.expected!r}){note}")


def main() -> None:
    baseline = _evaluate("baseline: name + description + tags", _strip_examples(_SKILLS))
    with_examples = _evaluate("with examples (current BM25Strategy)", _SKILLS)

    _print_report(baseline)
    _print_report(with_examples)

    print(
        f"\nRecall improvement from adding examples: "
        f"{baseline.recall_hits}/{baseline.total_positive} -> "
        f"{with_examples.recall_hits}/{with_examples.total_positive} "
        f"({len(_CASES)} queries, {len(_SKILLS)} skills)"
    )


if __name__ == "__main__":
    main()
