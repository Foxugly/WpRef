from question.models import Question, Subject, AnswerOption
from quiz.models import Quiz, QuizQuestion

subject = Subject.objects.create(name="Scrum", description="Questions sur Scrum")



q1 = Question.objects.create(
    title="Combien y a-t-il de rôles dans Scrum ?",
    description="Sélectionne la bonne réponse.",
)

q1a1 = AnswerOption.objects.create(question=q1, content="1", sort_order=1, is_correct=False)
q1a2 = AnswerOption.objects.create(question=q1, content="2", sort_order=2, is_correct=False)
q1a3 = AnswerOption.objects.create(question=q1, content="3", sort_order=3, is_correct=True)
q1a4 = AnswerOption.objects.create(question=q1, content="4", sort_order=4, is_correct=False)

q2 = Question.objects.create(
    title="La Daily Scrum dure maximum 15 minutes.",
    description="Vrai ou faux ?",
)
q2a1 = AnswerOption.objects.create(question=q2, content="Vrai", sort_order=1, is_correct=True)
q2a2 = AnswerOption.objects.create(question=q2, content="Faux", sort_order=2, is_correct=False)


q3 = Question.objects.create(
    title="Qui est responsable du Product Backlog ?",
    description="Sélectionne la bonne réponse.",
)

q3a1 = AnswerOption.objects.create(question=q3, content="Le Product Owner", sort_order=1, is_correct=True)
q3a2 = AnswerOption.objects.create(question=q3, content="Le Scrum Master", sort_order=2, is_correct=False)
q3a3 = AnswerOption.objects.create(question=q3, content="Les développeurs", sort_order=3, is_correct=False)

quiz = Quiz.objects.create(
    subject=subject,
    title="Quiz Scrum – Niveau débutant",
    slug="quiz-scrum-debutant",
)

QuizQuestion.objects.create(quiz=quiz, question=q1, order=1)
QuizQuestion.objects.create(quiz=quiz, question=q2, order=2)
QuizQuestion.objects.create(quiz=quiz, question=q3, order=3)
