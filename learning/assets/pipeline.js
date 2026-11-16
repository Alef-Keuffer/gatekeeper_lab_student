// Pipeline component: the gatekeeper's four stages, one optionally highlighted.
//   <div class="pipeline" data-highlight="checks">Contract → Checks → Report → Policy</div>
// The text inside is the no-JS / print fallback.

const STAGES = [
  ['contract', 'Contract', 'Relationship', 'valid object, or ValidationError'],
  ['checks', 'Checks', 'span · negation-cue · uncertainty · causal-claim', 'one Finding each'],
  ['report', 'Report', 'Report(findings=[…])', 'report.has(code)'],
  ['policy', 'Policy', 'decide(rel, report, consequence)', 'Decision: disposition + reason codes'],
];

document.querySelectorAll('.pipeline').forEach((el) => {
  const hi = el.dataset.highlight;
  const arrow = '<span class="arrow" aria-hidden="true"></span>';
  const stages = STAGES.map(([key, name, code, out]) =>
    `<div class="stage${key === hi ? ' hi' : ''}"><b>${name}</b><code>${code}</code><span>→ ${out}</span></div>`);
  el.setAttribute('role', 'img');
  el.setAttribute('aria-label', 'LLM candidate, then Contract, Checks, Report, Policy, then database');
  el.innerHTML = ['<span class="end">LLM candidate</span>', ...stages, '<span class="end">database</span>'].join(arrow);
});
