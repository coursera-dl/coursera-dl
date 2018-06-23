"""
Test APIs.
"""
from os.path import expanduser
import json

import pytest
from mock import patch, Mock

from coursera import api
from coursera import define

from coursera.test.utils import slurp_fixture, links_to_plain_text
from coursera.utils import BeautifulSoup

from requests.exceptions import HTTPError
from requests import Response


@pytest.fixture
def course():
    course = api.CourseraOnDemand(
        session=Mock(cookies={}), course_id='0', course_name='test_course')
    return course


@patch('coursera.api.get_page')
def test_extract_links_from_programming_http_error(get_page, course):
    """
    This test checks that downloader skips locked programming assignments
    instead of throwing an error. (Locked == returning 403 error code)
    """
    locked_response = Response()
    locked_response.status_code = define.HTTP_FORBIDDEN
    get_page.side_effect = HTTPError('Mocked HTTP error',
                                     response=locked_response)
    assert None == course.extract_links_from_programming('0')


@patch('coursera.api.get_page')
def test_extract_links_from_exam_http_error(get_page, course):
    """
    This test checks that downloader skips locked exams
    instead of throwing an error. (Locked == returning 403 error code)
    """
    locked_response = Response()
    locked_response.status_code = define.HTTP_FORBIDDEN
    get_page.side_effect = HTTPError('Mocked HTTP error',
                                     response=locked_response)
    assert None == course.extract_links_from_exam('0')


@patch('coursera.api.get_page')
def test_extract_links_from_supplement_http_error(get_page, course):
    """
    This test checks that downloader skips locked supplements
    instead of throwing an error. (Locked == returning 403 error code)
    """
    locked_response = Response()
    locked_response.status_code = define.HTTP_FORBIDDEN
    get_page.side_effect = HTTPError('Mocked HTTP error',
                                     response=locked_response)
    assert None == course.extract_links_from_supplement('0')


@patch('coursera.api.get_page')
def test_extract_links_from_lecture_http_error(get_page, course):
    """
    This test checks that downloader skips locked lectures
    instead of throwing an error. (Locked == returning 403 error code)
    """
    locked_response = Response()
    locked_response.status_code = define.HTTP_FORBIDDEN
    get_page.side_effect = HTTPError('Mocked HTTP error',
                                     response=locked_response)
    assert None == course.extract_links_from_lecture('fake_course_id', '0')


@patch('coursera.api.get_page')
def test_extract_links_from_quiz_http_error(get_page, course):
    """
    This test checks that downloader skips locked quizzes
    instead of throwing an error. (Locked == returning 403 error code)
    """
    locked_response = Response()
    locked_response.status_code = define.HTTP_FORBIDDEN
    get_page.side_effect = HTTPError('Mocked HTTP error',
                                     response=locked_response)
    assert None == course.extract_links_from_quiz('0')


@patch('coursera.api.get_page')
def test_extract_references_poll_http_error(get_page, course):
    """
    This test checks that downloader skips locked programming assignments
    instead of throwing an error. (Locked == returning 403 error code)
    """
    locked_response = Response()
    locked_response.status_code = define.HTTP_FORBIDDEN
    get_page.side_effect = HTTPError('Mocked HTTP error',
                                     response=locked_response)
    assert None == course.extract_references_poll()


@patch('coursera.api.get_page')
def test_extract_links_from_reference_http_error(get_page, course):
    """
    This test checks that downloader skips locked resources
    instead of throwing an error. (Locked == returning 403 error code)
    """
    locked_response = Response()
    locked_response.status_code = define.HTTP_FORBIDDEN
    get_page.side_effect = HTTPError('Mocked HTTP error',
                                     response=locked_response)
    assert None == course.extract_links_from_reference('0')


@patch('coursera.api.get_page')
def test_extract_links_from_programming_immediate_instructions_http_error(
        get_page, course):
    """
    This test checks that downloader skips locked programming immediate instructions
    instead of throwing an error. (Locked == returning 403 error code)
    """
    locked_response = Response()
    locked_response.status_code = define.HTTP_FORBIDDEN
    get_page.side_effect = HTTPError('Mocked HTTP error',
                                     response=locked_response)
    assert (
        None == course.extract_links_from_programming_immediate_instructions('0'))


@patch('coursera.api.get_page')
def test_ondemand_programming_supplement_no_instructions(get_page, course):
    no_instructions = slurp_fixture(
        'json/supplement-programming-no-instructions.json')
    get_page.return_value = json.loads(no_instructions)

    output = course.extract_links_from_programming('0')
    assert {} == output


@patch('coursera.api.get_page')
@pytest.mark.parametrize(
    "input_filename,expected_output", [
        ('peer-assignment-instructions-all.json', 'intro Review criteria section'),
        ('peer-assignment-instructions-no-title.json', 'intro section'),
        ('peer-assignment-instructions-only-introduction.json', 'intro'),
        ('peer-assignment-instructions-only-sections.json', 'Review criteria section'),
        ('peer-assignment-no-instructions.json', ''),
    ]
)
def test_ondemand_from_peer_assgnment_instructions(
        get_page, course, input_filename, expected_output):
    instructions = slurp_fixture('json/%s' % input_filename)
    get_page.return_value = json.loads(instructions)

    output = course.extract_links_from_peer_assignment('0')
    assert expected_output == links_to_plain_text(output)


@patch('coursera.api.get_page')
def test_ondemand_from_programming_immediate_instructions_no_instructions(
        get_page, course):
    no_instructions = slurp_fixture(
        'json/supplement-programming-immediate-instructions-no-instructions.json')
    get_page.return_value = json.loads(no_instructions)

    output = course.extract_links_from_programming_immediate_instructions('0')
    assert {} == output


@patch('coursera.api.get_page')
def test_ondemand_programming_supplement_empty_instructions(get_page, course):
    empty_instructions = slurp_fixture(
        'json/supplement-programming-empty-instructions.json')
    get_page.return_value = json.loads(empty_instructions)
    output = course.extract_links_from_programming('0')

    # Make sure that SOME html content has been extracted, but remove
    # it immeditely because it's a hassle to properly prepare test input
    # for it. FIXME later.
    assert 'html' in output
    del output['html']

    assert {} == output


@patch('coursera.api.get_page')
def test_ondemand_programming_immediate_instructions_empty_instructions(
        get_page, course):
    empty_instructions = slurp_fixture(
        'json/supplement-programming-immediate-instructions-empty-instructions.json')
    get_page.return_value = json.loads(empty_instructions)
    output = course.extract_links_from_programming_immediate_instructions('0')

    # Make sure that SOME html content has been extracted, but remove
    # it immeditely because it's a hassle to properly prepare test input
    # for it. FIXME later.
    assert 'html' in output
    del output['html']

    assert {} == output


@patch('coursera.api.get_page')
def test_ondemand_programming_supplement_one_asset(get_page, course):
    one_asset_tag = slurp_fixture('json/supplement-programming-one-asset.json')
    one_asset_url = slurp_fixture('json/asset-urls-one.json')
    asset_json = json.loads(one_asset_url)
    get_page.side_effect = [json.loads(one_asset_tag),
                            json.loads(one_asset_url)]

    expected_output = {'pdf': [(asset_json['elements'][0]['url'],
                                'statement-pca')]}
    output = course.extract_links_from_programming('0')

    # Make sure that SOME html content has been extracted, but remove
    # it immeditely because it's a hassle to properly prepare test input
    # for it. FIXME later.
    assert 'html' in output
    del output['html']

    assert expected_output == output


@patch('coursera.api.get_page')
def test_extract_references_poll(get_page, course):
    """
    Test extracting course references.
    """
    get_page.side_effect = [
        json.loads(slurp_fixture('json/references-poll-reply.json'))
    ]
    expected_output = json.loads(
        slurp_fixture('json/references-poll-output.json'))
    output = course.extract_references_poll()
    assert expected_output == output


@patch('coursera.api.get_page')
def test_ondemand_programming_immediate_instructions_one_asset(get_page, course):
    one_asset_tag = slurp_fixture(
        'json/supplement-programming-immediate-instructions-one-asset.json')
    one_asset_url = slurp_fixture('json/asset-urls-one.json')
    asset_json = json.loads(one_asset_url)
    get_page.side_effect = [json.loads(one_asset_tag),
                            json.loads(one_asset_url)]

    expected_output = {'pdf': [(asset_json['elements'][0]['url'],
                                'statement-pca')]}
    output = course.extract_links_from_programming_immediate_instructions('0')

    # Make sure that SOME html content has been extracted, but remove
    # it immeditely because it's a hassle to properly prepare test input
    # for it. FIXME later.
    assert 'html' in output
    del output['html']

    assert expected_output == output


@patch('coursera.api.get_page')
def test_ondemand_programming_supplement_three_assets(get_page, course):
    three_assets_tag = slurp_fixture(
        'json/supplement-programming-three-assets.json')
    three_assets_url = slurp_fixture('json/asset-urls-three.json')
    get_page.side_effect = [json.loads(three_assets_tag),
                            json.loads(three_assets_url)]

    expected_output = json.loads(slurp_fixture(
        'json/supplement-three-assets-output.json'))
    output = course.extract_links_from_programming('0')
    output = json.loads(json.dumps(output))

    # Make sure that SOME html content has been extracted, but remove
    # it immeditely because it's a hassle to properly prepare test input
    # for it. FIXME later.
    assert 'html' in output
    del output['html']

    assert expected_output == output


@patch('coursera.api.get_page')
def test_extract_links_from_lecture_assets_typename_asset(get_page, course):
    open_course_assets_reply = slurp_fixture(
        'json/supplement-open-course-assets-reply.json')
    api_assets_v1_reply = slurp_fixture(
        'json/supplement-api-assets-v1-reply.json')
    get_page.side_effect = [json.loads(open_course_assets_reply),
                            json.loads(api_assets_v1_reply)]

    expected_output = json.loads(slurp_fixture(
        'json/supplement-extract-links-from-lectures-output.json'))
    assets = ['giAxucdaEeWJTQ5WTi8YJQ']
    output = course._extract_links_from_lecture_assets(assets)
    output = json.loads(json.dumps(output))
    assert expected_output == output


@patch('coursera.api.get_page')
def test_extract_links_from_lecture_assets_typname_url_and_asset(get_page, course):
    """
    This test makes sure that _extract_links_from_lecture_assets grabs url
    links both from typename == 'asset' and == 'url'.
    """
    get_page.side_effect = [
        json.loads(slurp_fixture(
            'json/supplement-open-course-assets-typename-url-reply-1.json')),
        json.loads(slurp_fixture(
            'json/supplement-open-course-assets-typename-url-reply-2.json')),
        json.loads(slurp_fixture(
            'json/supplement-open-course-assets-typename-url-reply-3.json')),
        json.loads(slurp_fixture(
            'json/supplement-open-course-assets-typename-url-reply-4.json')),
        json.loads(slurp_fixture(
            'json/supplement-open-course-assets-typename-url-reply-5.json')),
    ]

    expected_output = json.loads(slurp_fixture(
        'json/supplement-extract-links-from-lectures-url-asset-output.json'))
    assets = ['Yry0spSKEeW8oA5fR3afVQ',
              'kMQyUZSLEeWj-hLVp2Pm8w',
              'xkAloZmJEeWjYA4jOOgP8Q']
    output = course._extract_links_from_lecture_assets(assets)
    output = json.loads(json.dumps(output))
    assert expected_output == output


@patch('coursera.api.get_page')
def test_list_courses(get_page, course):
    """
    Test course listing method.
    """
    get_page.side_effect = [
        json.loads(slurp_fixture('json/list-courses-input.json'))
    ]
    expected_output = json.loads(
        slurp_fixture('json/list-courses-output.json'))
    expected_output = expected_output['courses']
    output = course.list_courses()
    assert expected_output == output


@pytest.mark.parametrize(
    "input_filename,output_filename,subtitle_language,video_id", [
        ('video-reply-1.json', 'video-output-1.json',
            'en,zh-CN|zh-TW', "None"),
        ('video-reply-1.json', 'video-output-1-en.json',
            'zh-TW', "None"),
        ('video-reply-1.json', 'video-output-1-en.json',
            'en', "None"),
        ('video-reply-1.json', 'video-output-1-all.json',
            'all', "None"),
        ('video-reply-1.json', 'video-output-1-all.json',
            'zh-TW,all|zh-CN', "None"),
        ('video-reply-2.json', 'video-output-2.json',
            'en,zh-CN|zh-TW', "None"),
    ]
)
def test_extract_subtitles_from_video_dom(input_filename, output_filename, subtitle_language, video_id):
    video_dom = json.loads(slurp_fixture('json/%s' % input_filename))
    expected_output = json.loads(slurp_fixture('json/%s' % output_filename))
    course = api.CourseraOnDemand(
        session=Mock(cookies={}), course_id='0', course_name='test_course')
    actual_output = course._extract_subtitles_from_video_dom(
        video_dom, subtitle_language, video_id)
    actual_output = json.loads(json.dumps(actual_output))
    assert actual_output == expected_output


@pytest.mark.parametrize(
    "input_filename,output_filename", [
        ('empty-input.json', 'empty-output.txt'),
        ('answer-text-replaced-with-span-input.json',
         'answer-text-replaced-with-span-output.txt'),
        ('question-type-textExactMatch-input.json',
         'question-type-textExactMatch-output.txt'),
        ('question-type-regex-input.json', 'question-type-regex-output.txt'),
        ('question-type-mathExpression-input.json',
         'question-type-mathExpression-output.txt'),
        ('question-type-checkbox-input.json', 'question-type-checkbox-output.txt'),
        ('question-type-mcq-input.json', 'question-type-mcq-output.txt'),
        ('question-type-singleNumeric-input.json',
         'question-type-singleNumeric-output.txt'),
        ('question-type-reflect-input.json', 'question-type-reflect-output.txt'),
        ('question-type-mcqReflect-input.json',
         'question-type-mcqReflect-output.txt'),
        ('question-type-unknown-input.json', 'question-type-unknown-output.txt'),
        ('multiple-questions-input.json', 'multiple-questions-output.txt'),
    ]
)
def test_quiz_exam_to_markup_converter(input_filename, output_filename):
    quiz_json = json.loads(slurp_fixture(
        'json/quiz-to-markup/%s' % input_filename))
    expected_output = slurp_fixture(
        'json/quiz-to-markup/%s' % output_filename).strip()

    converter = api.QuizExamToMarkupConverter(session=None)
    actual_output = converter(quiz_json).strip()
    # print('>%s<' % expected_output)
    # print('>%s<' % actual_output)
    assert actual_output == expected_output


class TestMarkupToHTMLConverter:
    def _p(self, html):
        return BeautifulSoup(html).prettify()

    STYLE = None

    def setup_method(self, test_method):
        self.STYLE = self._p(
            "".join([define.INSTRUCTIONS_HTML_INJECTION_PRE,
                     define.INSTRUCTIONS_HTML_MATHJAX_URL,
                     define.INSTRUCTIONS_HTML_INJECTION_AFTER])
        )
        self.markup_to_html = api.MarkupToHTMLConverter(session=None)

        ALTERNATIVE_MATHJAX_CDN = "https://alternative/mathjax/cdn.js"
        self.STYLE_WITH_ALTER = self._p(
            "".join([define.INSTRUCTIONS_HTML_INJECTION_PRE,
                     ALTERNATIVE_MATHJAX_CDN,
                     define.INSTRUCTIONS_HTML_INJECTION_AFTER])
        )
        self.markup_to_html_with_alter_mjcdn = api.MarkupToHTMLConverter(
            session=None, mathjax_cdn_url=ALTERNATIVE_MATHJAX_CDN)

    def test_empty(self):
        output = self.markup_to_html("")
        output_with_alter_mjcdn = self.markup_to_html_with_alter_mjcdn("")
        markup = """
        <meta charset="UTF-8"/>
        """
        assert self._p(markup) + self.STYLE == output
        assert self._p(markup) + \
            self.STYLE_WITH_ALTER == output_with_alter_mjcdn

    def test_replace_text_tag(self):
        markup = """
        <co-content>
        <text>
            Test<text>Nested</text>
        </text>
        <text>
            Test2
        </text>
        </co-content>
        """
        result = """
        <meta charset="UTF-8"/>
        <co-content>
        <p>
            Test<p>Nested</p>
        </p>
        <p>
            Test2
        </p>
        </co-content>\n
        """
        output = self.markup_to_html(markup)
        output_with_alter_mjcdn = self.markup_to_html_with_alter_mjcdn(markup)
        assert self._p(result) + self.STYLE == output
        assert self._p(result) + \
            self.STYLE_WITH_ALTER == output_with_alter_mjcdn

    def test_replace_heading(self):
        output = self.markup_to_html("""
        <co-content>
            <heading level="1">Text</heading>
            <heading level="2">Text</heading>
            <heading level="3">Text</heading>
            <heading level="4">Text</heading>
            <heading level="5">Text</heading>
            <heading >Text</heading>
        </co-content>
        """)
        assert self._p("""
        <meta charset="UTF-8"/>
        <co-content>
            <h1 level="1">Text</h1>
            <h2 level="2">Text</h2>
            <h3 level="3">Text</h3>
            <h4 level="4">Text</h4>
            <h5 level="5">Text</h5>
            <h1>Text</h1>
        </co-content>\n
        """) + self.STYLE == output

    def test_replace_code(self):
        output = self.markup_to_html("""
        <co-content>
            <code>Text</code>
            <code>Text</code>
        </co-content>
        """)
        assert self._p("""
        <meta charset="UTF-8"/>
        <co-content>
            <pre>Text</pre>
            <pre>Text</pre>
        </co-content>\n
        """) + self.STYLE == output

    def test_replace_list(self):
        output = self.markup_to_html("""
        <co-content>
            <list bullettype="numbers">Text</list>
            <list bullettype="bullets">Text</list>
        </co-content>
        """)
        assert self._p("""
        <meta charset="UTF-8"/>
        <co-content>
            <ol bullettype="numbers">Text</ol>
            <ul bullettype="bullets">Text</ul>
        </co-content>\n
        """) + self.STYLE == output

    @patch('coursera.api.AssetRetriever')
    def test_replace_images(self, mock_asset_retriever):
        replies = {
            'nVhIAj61EeaGyBLfiQeo_w': Mock(data=b'a', content_type='image/png'),
            'vdqUTz61Eea_CQ5dfWSAjQ': Mock(data=b'b', content_type='image/png'),
            'nodata': Mock(data=None, content_type='image/png')
        }
        mock_asset_retriever.__call__ = Mock(return_value=None)
        mock_asset_retriever.__getitem__ = Mock(
            side_effect=replies.__getitem__)
        self.markup_to_html._asset_retriever = mock_asset_retriever

        output = self.markup_to_html("""
        <co-content>
            <text>\n\n</text>
            <img assetId=\"nVhIAj61EeaGyBLfiQeo_w\" alt=\"\"/>
            <text>\n\n</text>
            <img assetId=\"vdqUTz61Eea_CQ5dfWSAjQ\" alt=\"\"/>
            <text>\n\n</text>
        </co-content>
        """)

        assert self._p("""
        <meta charset="UTF-8"/>
        <co-content>
            <p></p>
            <img alt="" assetid="nVhIAj61EeaGyBLfiQeo_w" src="data:image/png;base64,YQ=="/>
            <p></p>
            <img alt="" assetid="vdqUTz61Eea_CQ5dfWSAjQ" src="data:image/png;base64,Yg=="/>
            <p></p>
        </co-content>\n
        """) + self.STYLE == output

    @patch('coursera.api.AssetRetriever')
    def test_replace_audios(self, mock_asset_retriever):
        replies = {
            'aWTK9sYwEeW7AxLLCrgDQQ': Mock(data=b'a', content_type='audio/mpeg'),
            'bWTK9sYwEeW7AxLLCrgDQQ': Mock(data=b'b', content_type='unknown')
        }
        mock_asset_retriever.__call__ = Mock(return_value=None)
        mock_asset_retriever.__getitem__ = Mock(
            side_effect=replies.__getitem__)
        self.markup_to_html._asset_retriever = mock_asset_retriever

        output = self.markup_to_html("""
        <co-content>
            <asset id=\"aWTK9sYwEeW7AxLLCrgDQQ\" name=\"M111\" extension=\"mp3\" assetType=\"audio\"/>
            <asset id=\"bWTK9sYwEeW7AxLLCrgDQQ\" name=\"M112\" extension=\"mp3\" assetType=\"unknown\"/>
        </co-content>
        """)

        assert self._p("""
        <meta charset="UTF-8"/>
        <co-content>
            <asset assettype="audio" extension="mp3" id="aWTK9sYwEeW7AxLLCrgDQQ" name="M111">
            </asset>
            <audio controls="">
             Your browser does not support the audio element.
             <source src="data:audio/mpeg;base64,YQ==" type="audio/mpeg">
             </source>
            </audio>
            <asset assettype="unknown" extension="mp3" id="bWTK9sYwEeW7AxLLCrgDQQ" name="M112">
            </asset>
        </co-content>\n
        """) + self.STYLE == output


def test_quiz_converter():
    pytest.skip()
    quiz_to_markup = api.QuizExamToMarkupConverter(session=None)
    markup_to_html = api.MarkupToHTMLConverter(session=None)

    quiz_data = json.load(open('quiz.json'))['contentResponseBody']['return']
    result = markup_to_html(quiz_to_markup(quiz_data))
    # from ipdb import set_trace; set_trace(context=20)
    print('RESULT', result)
    with open('quiz.html', 'w') as file:
        file.write(result)


def test_quiz_converter_all():
    pytest.skip()
    import os

    from coursera.coursera_dl import get_session
    from coursera.cookies import login
    session = None
    session = get_session()

    quiz_to_markup = api.QuizExamToMarkupConverter(session=session)
    markup_to_html = api.MarkupToHTMLConverter(session=session)

    path = 'quiz_json'
    for filename in ['quiz-audio.json']:  # os.listdir(path):
        # for filename in ['all_question_types.json']:
        # if 'YV0W4' not in filename:
        #     continue
        # if 'QVHj1' not in filename:
        #     continue

        #quiz_data = json.load(open('quiz.json'))['contentResponseBody']['return']
        current = os.path.join(path, filename)
        print(current)
        quiz_data = json.load(open(current))
        result = markup_to_html(quiz_to_markup(quiz_data))
        # from ipdb import set_trace; set_trace(context=20)
        # print('RESULT', result)
        with open('quiz_html/' + filename + '.html', 'w') as f:
            f.write(result)


def create_session():
    from coursera.coursera_dl import get_session
    from coursera.credentials import get_credentials
    from coursera.cookies import login

    session = get_session()
    username, password = get_credentials(netrc=expanduser('~/.netrc'))
    login(session, username, password)
    return session


@patch('coursera.api.get_page')
@patch('coursera.api.get_reply')
def test_asset_retriever(get_reply, get_page):
    reply = json.loads(slurp_fixture('json/asset-retriever/assets-reply.json'))
    get_page.side_effect = [reply]
    get_reply.side_effect = [Mock(status_code=200, content='<...>',
                                  headers=Mock(get=Mock(return_value='image/png')))] * 4

    asset_ids = ['bWTK9sYwEeW7AxLLCrgDQQ',
                 'VceKeChKEeaOMw70NkE3iw',
                 'VcmGXShKEea4ehL5RXz3EQ',
                 'vdqUTz61Eea_CQ5dfWSAjQ']

    expected_output = [
        api.Asset(id="bWTK9sYwEeW7AxLLCrgDQQ", name="M111.mp3", type_name="audio",
                  url="url4", content_type="image/png", data="<...>"),
        api.Asset(id="VceKeChKEeaOMw70NkE3iw", name="09_graph_decomposition_problems_1.pdf",
                  type_name="pdf", url="url7", content_type="image/png", data="<...>"),
        api.Asset(id="VcmGXShKEea4ehL5RXz3EQ", name="09_graph_decomposition_starter_files_1.zip",
                  type_name="generic", url="url2", content_type="image/png", data="<...>"),
        api.Asset(id="vdqUTz61Eea_CQ5dfWSAjQ", name="Capture.PNG",
                  type_name="image", url="url9", content_type="image/png", data="<...>"),
    ]

    retriever = api.AssetRetriever(session=None)
    actual_output = retriever(asset_ids)

    assert expected_output == actual_output


def test_debug_asset_retriever():
    pytest.skip()
    asset_ids = ['bWTK9sYwEeW7AxLLCrgDQQ',
                 'bXCx18YwEeWicwr5JH8fgw',
                 'bX9X18YwEeW7AxLLCrgDQQ',
                 'bYHvf8YwEeWFNA5XwZEiOw',
                 'tZmigMYxEeWFNA5XwZEiOw']
    asset_ids = asset_ids[0:5]

    more = ['VceKeChKEeaOMw70NkE3iw',
            'VcmGXShKEea4ehL5RXz3EQ']

    print('session')
    session = create_session()
    retriever = api.AssetRetriever(session)
    #assets = retriever.get(asset_ids)
    assets = retriever(more)

    print(assets)
