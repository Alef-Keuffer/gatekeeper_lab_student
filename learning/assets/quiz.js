// Quiz component. Markup:
//   <div class="quiz" data-answer="2">            (0-based index of the right option)
//     <p class="q">Question</p>
//     <ol><li>Option</li>…</ol>
//     <p class="explain">Why the right answer is right.</p>
//   </div>
//   <p class="quiz-score"></p>                     (optional running score)
// First click counts: retrieval practice, not trial and error.

document.querySelectorAll('.quiz').forEach((quiz) => {
  const answer = Number(quiz.dataset.answer);
  const items = [...quiz.querySelectorAll('ol > li')];
  quiz.querySelector('.explain')?.setAttribute('aria-live', 'polite');
  items.forEach((li, i) => {
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.innerHTML = li.innerHTML;
    li.replaceChildren(btn);
    btn.addEventListener('click', () => {
      if (quiz.classList.contains('done')) return;
      quiz.classList.add('done');
      items[answer].classList.add('right');
      if (i === answer) quiz.dataset.correct = '';
      else li.classList.add('wrong');
      items.forEach((x) => (x.querySelector('button').disabled = true));
      updateScore();
    });
  });
});

function updateScore() {
  const el = document.querySelector('.quiz-score');
  if (!el) return;
  const total = document.querySelectorAll('.quiz').length;
  const done = document.querySelectorAll('.quiz.done').length;
  const right = document.querySelectorAll('.quiz[data-correct]').length;
  el.textContent = done === 0
    ? `${total} questions · your first click counts`
    : done < total
      ? `${right} / ${done} correct so far · ${total - done} to go`
      : `${right} / ${total} correct`;
  if (done === total) {
    const again = document.createElement('button');
    again.type = 'button';
    again.textContent = 'Retake later';
    again.title = 'Reset the quiz — best done after a day or two';
    again.addEventListener('click', () => location.reload());
    el.append(again);
  }
}

updateScore();
