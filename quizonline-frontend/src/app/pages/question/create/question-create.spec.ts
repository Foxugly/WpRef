import {ComponentFixture, TestBed} from '@angular/core/testing';
import {ActivatedRoute, convertToParamMap} from '@angular/router';
import {of} from 'rxjs';
import {MessageService} from 'primeng/api';

import {MediaAssetDto, MediaAssetKindEnumDto, MediaAssetUploadKindEnumDto} from '../../../api/generated';
import {MediaSelectorValue} from '../../../components/media-selector/media-selector';
import {DomainService} from '../../../services/domain/domain';
import {QuestionService} from '../../../services/question/question';
import {SubjectService} from '../../../services/subject/subject';
import {TranslationService} from '../../../services/translation/translation';
import {UserService} from '../../../services/user/user';
import {QuestionCreate} from './question-create';
import {uploadQuestionEditorMediaAssets} from '../../../services/question/question-editor-form';

describe('QuestionCreate media uploads', () => {
  let component: QuestionCreate;
  let fixture: ComponentFixture<QuestionCreate>;
  let questionService: jasmine.SpyObj<QuestionService>;

  beforeEach(async () => {
    questionService = jasmine.createSpyObj<QuestionService>('QuestionService', [
      'questionMediaCreate',
      'create',
      'goList',
      'goBack',
      'consumeDuplicateDraft',
    ]);
    questionService.consumeDuplicateDraft.and.returnValue(null);

    await TestBed.configureTestingModule({
      imports: [QuestionCreate],
      providers: [
        {
          provide: DomainService,
          useValue: {
            list: () => of([]),
            retrieve: () => of({
              allowed_languages: [],
            }),
          },
        },
        {
          provide: SubjectService,
          useValue: {
            list: () => of([]),
          },
        },
        {
          provide: QuestionService,
          useValue: questionService,
        },
        {
          provide: TranslationService,
          useValue: {
            translateBatch: () => Promise.resolve({}),
          },
        },
        {
          provide: UserService,
          useValue: {
            currentLang: 'fr',
          },
        },
        {
          provide: ActivatedRoute,
          useValue: {
            snapshot: {
              queryParamMap: convertToParamMap({}),
            },
          },
        },
        MessageService,
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(QuestionCreate);
    component = fixture.componentInstance;
  });

  async function createMediaAssets(media: MediaSelectorValue[]) {
    return uploadQuestionEditorMediaAssets(
      media,
      (params) => questionService.questionMediaCreate(params),
    );
  }

  function mediaAsset(id: number): MediaAssetDto {
    return {
      id,
      kind: MediaAssetKindEnumDto.External,
      file: null,
      external_url: null,
      sha256: null,
      created_at: '',
    };
  }

  it('sends an image file with the image enum to the backend', async () => {
    const file = new File(['img'], 'image.png', {type: 'image/png'});
    questionService.questionMediaCreate.and.returnValue(of(mediaAsset(11)));

    const ids = await createMediaAssets([
      {kind: 'image', file, external_url: null, sort_order: 1},
    ]);

    expect(ids).toEqual([11]);
    expect(questionService.questionMediaCreate).toHaveBeenCalledOnceWith({
      file,
      kind: MediaAssetUploadKindEnumDto.Image,
    });
  });

  it('sends a video file with the video enum to the backend', async () => {
    const file = new File(['vid'], 'video.mp4', {type: 'video/mp4'});
    questionService.questionMediaCreate.and.returnValue(of(mediaAsset(12)));

    const ids = await createMediaAssets([
      {kind: 'video', file, external_url: null, sort_order: 1},
    ]);

    expect(ids).toEqual([12]);
    expect(questionService.questionMediaCreate).toHaveBeenCalledOnceWith({
      file,
      kind: MediaAssetUploadKindEnumDto.Video,
    });
  });

  it('sends a youtube link as an external url to the backend', async () => {
    const youtubeUrl = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ';
    questionService.questionMediaCreate.and.returnValue(of(mediaAsset(13)));

    const ids = await createMediaAssets([
      {kind: 'external', file: null, external_url: youtubeUrl, sort_order: 1},
    ]);

    expect(ids).toEqual([13]);
    expect(questionService.questionMediaCreate).toHaveBeenCalledOnceWith({
      kind: MediaAssetUploadKindEnumDto.External,
      externalUrl: youtubeUrl,
    });
  });
});
