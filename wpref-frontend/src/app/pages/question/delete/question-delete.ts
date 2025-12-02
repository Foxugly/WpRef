import {Component, inject, OnInit, signal} from '@angular/core';

import {ActivatedRoute} from '@angular/router';
import {Question, QuestionService} from '../../../services/question/question';
import {Button} from 'primeng/button';

@Component({
  standalone: true,
  selector: 'question-delete',
  imports: [Button],
  templateUrl: './question-delete.html',
  styleUrl: './question-delete.scss'
})
export class QuestionDelete implements OnInit {
  id!: number;
  question = signal<Question | null>(null);
  private route = inject(ActivatedRoute);
  private questionService = inject(QuestionService);

  ngOnInit() {
    this.id = Number(this.route.snapshot.paramMap.get('id'));
    this.questionService.retrieve(this.id).subscribe(s => this.question.set(s));
  }

  goBack():void{
    this.questionService.goBack();
  }

  confirm() {
    this.questionService.delete(this.id).subscribe({
      next: () => this.questionService.goList()
    });
  }
}
